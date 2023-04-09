import discord
import os
import random

import datetime
import pandas as pd

# my stuff
import sheets
import engineMethods
import quest

# bot_persona = 'SamTestBot'
# bot_persona = 'CTV_Sam_Bot'
bot_persona = 'BreedquestBot'

# Launch as SamTestBot
intents = discord.Intents.all()
client = discord.Client(intents=intents)
discord_token = os.getenv("BREEDQUEST_BOT_TOKEN")

# variables
message_requestors = {} # key = message.id; value = message.author
player_starter_creatures = {} # key = message.author; value = {starter_creature_options_dict}
player_bred_creature = {} # key = message.author; value = breed_result (a dict)
quest_options_dict = {} # key = message.id; value = 

acceptable_emoji_responses = ['🇦', '🇧', '🇨', '❌'] # '🔄',
acceptable_emoji_responses_five = ['🇦', '🇧', '🇨', '🇩', '🇪', '❌'] # '🔄',

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# discord event handlingand reaction methods.
@client.event
async def on_ready():
    print(bot_persona+' is now online.')

@client.event
async def on_message(message):
    requestor_user_id = message.author
    # if the user is the bot myself, do nothing. 
    if requestor_user_id == client.user:
        return
    if client.user.mentioned_in(message):
        start_index = message.content.index("<@"+str(client.user.id)+">") + len("<@"+str(client.user.id)+">")
        text_after_mention = message.content[start_index:].strip()

        # user's gamestate. 
        has_creature,creature_name,creature_id = await get_players_creature(message.author)
        
        # handle the condition. 
        if text_after_mention == 'starter':
            print('I was asked by '+message.author.name+': starter')
            if has_creature:
                await message.channel.send(f"{message.author.mention}: "+"You already have "+creature_name+"! At the moment, you may only have one Chimera.")
                return
            else:
                await post_starter_creature_prompt(message.channel, message.author)
            return
        if text_after_mention == 'quest':
            print('I was asked by '+message.author.name+': quest')
            if not has_creature:
                await message.channel.send(f"{message.author.mention}: "+": You don't have a Chimera yet! You can get one by typing 'starter'.")
                return
            else:
                await post_quest_prompt(message,creature_name,creature_id)
            return
        if text_after_mention == 'secrettest':
            # secret only
            print('I was asked by '+message.author.name+': secrettest')
            # creature_id_test = 'tentacled_boar_412'
            # quest_test = "Dive into Kermond's pipes to remove the marbles or coins at the bottom to fix his plumbing"
            # await quest.quest(creature_id_test,quest_test)
            return
        else:
            print('I didnt recognize the command.')
            await message.channel.send(f"{message.author.mention}: I don't understand. I only know: "
                                    "'starter' \n"
                                    "'quest' \n"
                                    )



@client.event
async def on_reaction_add(reaction, user):

    # if a) user isn't bot and b) message being reacted to was sent by bot:
    if user != client.user and reaction.message.author == client.user:

        print('I saw a reaction ('+reaction.emoji+') by '+user.name+'('+str(user.id)+') to one of my posts.')
        
        # Check if the reaction was added by the original requestor
        original_requestor = message_requestors.get(reaction.message.id)
        print('   original requestor: '+original_requestor.name+'('+str(original_requestor.id)+')')

        # if a) correct emoji, b) original requestor, c) starter creature prompt:
        if reaction.emoji in acceptable_emoji_responses \
            and original_requestor == user \
            and reaction.message.content.find("Welcome to ChimeraQuest.") != -1:

            print(user.name+' reacted to Welcome Message with: '+reaction.emoji)
            await act_on_starter_creature_prompt_response(reaction,user)
            
        
        # if a) correct emoji, b) original requestor, c) creature selection prompt:
        elif reaction.emoji in acceptable_emoji_responses \
            and original_requestor == user \
            and reaction.message.content.find("Breeding complete") != -1:

            print(user.name+' reacted to Breeding Complete with:'+reaction.emoji)
            await act_on_breeding_complete_response(reaction,user)

        # if a) correct emoji, b) original requestor, c) quest prompt:
        elif reaction.emoji in acceptable_emoji_responses \
            and original_requestor == user \
            and reaction.message.content.find("Quest time.") != -1:

            print(user.name+' reacted to Quest time with:'+reaction.emoji)
            await send_creature_on_quest(reaction,user)
            


async def act_on_starter_creature_prompt_response(reaction,requestor_user):
    # If ❌ was selected, delete the message.
    if reaction.emoji == '❌':
        await reaction.message.delete()
        return

    # get the creature pair the player selected with their emoji
    starter_creature_options_dict = player_starter_creatures[requestor_user]
    selected_starter_creature_pair = starter_creature_options_dict[reaction.emoji]
    
    starter_creature_prompt_2a = "You got it! breeding: **"
    starter_creature_prompt_2b = "**. Standby... (10-15sec)"
    new_content = starter_creature_prompt_2a+\
        selected_starter_creature_pair[0]['creature']+" + "+\
        selected_starter_creature_pair[1]['creature']+starter_creature_prompt_2b
    await reaction.message.edit(content=new_content)
    await reaction.message.clear_reactions()

    print("Player has selected the following creatures to breed: "+\
        selected_starter_creature_pair[0]['creature']+" + "+\
        selected_starter_creature_pair[1]['creature'])

    # breed the creatures
    breed_result = await engineMethods.breed(selected_starter_creature_pair[0]['creature_id'], selected_starter_creature_pair[1]['creature_id'])
    if breed_result["error"]:
        print("Error in breeding. (error 1)")
        await reaction.message.edit(content="Something went wrong breeding "+
                                    selected_starter_creature_pair[0]['creature']+" + "+
                                    selected_starter_creature_pair[1]['creature']+
                                    "😢. Please try again. (error 1)")
        return
    
    # Post a new message with the new creature name and images. 
    try:
        await post_breed_selection_prompt(reaction.message.channel, requestor_user, breed_result)
    except:
        print("Error in posting breed selection prompt. (error 2)")
        await reaction.message.edit(content="Something went wrong breeding "+
                                    selected_starter_creature_pair[0]['creature']+" + "+
                                    selected_starter_creature_pair[1]['creature']+
                                    "😢. Please try again. (error 2)")
        return

async def act_on_breeding_complete_response(reaction,requestor_user):
    # If ❌ was selected, delete the message.
    if reaction.emoji == '❌':
        await reaction.message.delete()
        return

    # get the creature by emoji. 
    emoji_selection_index = acceptable_emoji_responses.index(reaction.emoji)

    # prepare the data for uploading to Sheets. 
    breed_result = player_bred_creature[requestor_user]
    new_creature_id = breed_result["new_name_list"][emoji_selection_index].lower().replace(" ", "_")+ "_" + str(random.randint(0, 999)).zfill(3)
    
    # Process our lamarkian properites. 
    new_lamarkian_properties = breed_result["lamarkian_properties"]
    lamarkian_total = sum(int(value) for value in new_lamarkian_properties.values())
    lamarkian_total_string = f"{lamarkian_total}"

    new_row = [
        new_creature_id,
        breed_result["new_name_list"][emoji_selection_index],
        breed_result["unique_image_names"][emoji_selection_index],
        breed_result["ancestors"],
        "d"+str(requestor_user.id),
        requestor_user.name,
        breed_result["aesthetic_properties"],
        breed_result["behavioral_properties"],
        #biomes (not used)
        "",
        #stats
        breed_result["lamarkian_properties"]["Climb"],
        breed_result["lamarkian_properties"]["Strength"],
        breed_result["lamarkian_properties"]["Agile"],
        breed_result["lamarkian_properties"]["Endurance"],
        breed_result["lamarkian_properties"]["Run"],
        breed_result["lamarkian_properties"]["Swim"],
        breed_result["lamarkian_properties"]["Dive"],
        breed_result["lamarkian_properties"]["Fly"],
        breed_result["lamarkian_properties"]["Dig"],
        breed_result["lamarkian_properties"]["Hide"],
        breed_result["lamarkian_properties"]["Stealth"],
        breed_result["lamarkian_properties"]["Resistance"],
        breed_result["lamarkian_properties"]["Scrounge"],
        breed_result["lamarkian_properties"]["Fight"],
        breed_result["lamarkian_properties"]["Defend"],
        breed_result["lamarkian_properties"]["Social"],
        breed_result["lamarkian_properties"]["Intelligence"],
        breed_result["lamarkian_properties"]["Heavy"],
        breed_result["lamarkian_properties"]["Sight"],
        breed_result["lamarkian_properties"]["Smell"],
        breed_result["lamarkian_properties"]["Hearing"],
        breed_result["lamarkian_properties"]["Adaptation"],
        breed_result["lamarkian_properties"]["Mimicry"],
        breed_result["lamarkian_properties"]["Venom"],
        breed_result["lamarkian_properties"]["Bioluminescence"],
        breed_result["lamarkian_properties"]["Regeneration"],
        #total power of lamarkian properties
        lamarkian_total_string,
        "0", #starter creature
        "", #nickname
        "xxx", #last column
    ]
    # append the new creature to the sheet
    sheets.write_to_sam_sheets('CreatureTraits', new_row)

    # now keep track of player's collection, too!
    player_gamestate_new_row = [
        new_creature_id,
        breed_result["new_name_list"][emoji_selection_index],
        "owned",
    ]
    # check to see if player does not yet have a gamestate, and instantiate if not.
    if not sheets.sheet_exists("d"+str(requestor_user.id)):
        sheets.instantiate_new_gamestate_sheet("d"+str(requestor_user.id))
    
    # then write to it. 
    sheets.write_to_sam_sheets("d"+str(requestor_user.id), player_gamestate_new_row)
    
    # Events, too. 
    events_new_row = [
        "d"+str(requestor_user.id),
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        new_creature_id,
        "bred creature",
    ]
    sheets.write_to_sam_sheets('Events', events_new_row)

    # delete THIS message
    await reaction.message.delete()

    # and send a new message confirming the creature was added to the player's collection.
    try:
        await post_breed_confirmation(reaction.message.channel, requestor_user, new_creature_id)
    except:
        print("Error in posting breed confirmation. (error 3)")
    # finally, send the follow-up. 
    try:
        await post_things_to_do(reaction.message.channel, requestor_user)
    except:
        print("Error in posting breed selection prompt. (error 4)")
    return


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Discord Posting Methods

# breeding related (main thread)
async def post_starter_creature_prompt(channel, requestor_user):
    starter_creature_options_dict,discord_message_text = await construct_starter_message_prompt()
    message = await channel.send(f"{requestor_user.mention}: "+discord_message_text)

    # keep track of the starter creatures I've provided.
    message_requestors[message.id] = requestor_user
    player_starter_creatures[requestor_user] = starter_creature_options_dict

    # React to the message with the specified emojis
    for emoji in acceptable_emoji_responses:
        await message.add_reaction(emoji)    
    print("I've prompted "+requestor_user.name+" to select a starter creature pair.")

async def post_breed_selection_prompt(channel, requestor_user, breed_result):
    # keep track of the options presented. 
    player_bred_creature[requestor_user] = breed_result

    print("breed_result['new_name_list']")
    print(breed_result['new_name_list'])

    discord_message_text = (
        "Breeding complete! You get only ONE pick of the litter 😁\n\n"
        f"🇦 **{breed_result['new_name_list'][0]}**\n"
        f"🇧 **{breed_result['new_name_list'][1]}**\n"
        f"🇨 **{breed_result['new_name_list'][2]}**\n"
        "\n\n"
    )

    # Create a list of image file objects from the image file paths to attach.
    image_files = [discord.File(os.path.join("./out", name)) for name in breed_result["unique_image_names"]]
    message = await channel.send(f"{requestor_user.mention}: "+discord_message_text, files=image_files)

    # Keep track of users game state so we know who to listen to for reactions. 
    message_requestors[message.id] = requestor_user

    # React to the message with the specified emojis
    for emoji in acceptable_emoji_responses:
        await message.add_reaction(emoji)
    print("I've provided creatures for "+requestor_user.name+"("+str(requestor_user.id)+") to select.")

async def post_breed_confirmation(channel, requestor_user, new_creature_id):

    # at this point the creature's data has been uploaded. So pull from there. 
    data = sheets.fetch_table_from_sheets('CreatureTraits')
    header = data[0]
    animal_row = engineMethods.get_animal_row(new_creature_id, data)
    animal_dict = {header[i]: animal_row[i] for i in range(0, len(header))}

    # Describe the creature's strengths and weaknesses. 
    strengths_and_weaknesses = engineMethods.get_animal_strengths_and_weaknesses(new_creature_id)

    # compose the text message. 
    discord_message_text = ("Congrats on your new **"+animal_dict['creature']+"**! 🎉\n\n")
    discord_message_text += strengths_and_weaknesses
    discord_message_text += "\n (There are other skills not mentioned here.)"

    image_file = discord.File(os.path.join("./out", animal_dict['image_url']))
    message = await channel.send(f"{requestor_user.mention}: "+discord_message_text, file=image_file)

    print("I've congratulated "+requestor_user.name+" on their new creature.")

async def post_things_to_do(channel, requestor_user):
    # Player has their creature. Tell them what thei can do with their creature.
    discord_message_text = (
            "Here are all the things you can do with your new Chimera.\n"
            # "(Click an emote to respond to this message, or 🚧 [coming soon] @ me telling me what you'd like to do.)\n"
            # "🇦 **Quest**. Type '@ChimeraQuest quest' \n"
            # "🇧 🚧 **Status of my Chimera** [coming soon]. 🚧 \n"
            # "🇨 🚧 **Rename my Chimera** [coming soon]. 🚧 \n"
            # "🇩 🚧 **Play with my Chimera** [coming soon]. 🚧 \n"
            # "🇪 🚧 **Release my Chimera** [coming soon]. 🚧 \n"
            "**Quest**. Type '@ChimeraQuest quest' \n"
            "🚧 **Status of my Chimera** [coming soon]. 🚧 \n"
            "🚧 **Rename my Chimera** [coming soon]. 🚧 \n"
            "🚧 **Play with my Chimera** [coming soon]. 🚧 \n"
            "🚧 **Release my Chimera** [coming soon]. 🚧 \n"
            "\n\n"
        )
    message = await channel.send(discord_message_text)

    # keep track of the requestor for this message.id. 
    message_requestors[message.id] = requestor_user

    # # React to the message with the specified emojis
    # for emoji in acceptable_emoji_responses_five:
    #     await message.add_reaction(emoji)    
    print("I've prompted player to start their adventure.")

# questing related
async def post_quest_prompt(message_to_thread_from,creature_name,creature_id):

    # offer 3 quests. 
    quest_descriptions, quest_traits_testeds, quest_traits_testeds_with_emojis = quest.get_three_random_quests()
    
    # determine the creature's chance of success at those quests. 
    # fetch the traitscores of the creature.
    data = sheets.fetch_table_from_sheets('CreatureTraits')
    header = data[0]
    animal_row = engineMethods.get_animal_row(creature_id, data)
    animal_dict = {header[i]: animal_row[i] for i in range(1, len(header))}
    
    # now get the success chances for traitscores. 
    trait_success_chance_dict,trait_description_dict,trait_shorthand_dict =  engineMethods.get_trait_power_dicts()
    
    # Finally, the Lamark emojis.
    lamarkian_properties_table = sheets.fetch_table_from_sheets("Lamarks")
    lamarkian_properties = []
    lamark_emoji_dict = {}
    for row in lamarkian_properties_table[1:]:
        lamark = row[0]
        emoji = row[2]
        lamarkian_properties.append(lamark)
        # Add key-value pair
        lamark_emoji_dict[lamark] = emoji
    
    # create the code blocks containing the skill lookups. 
    all_quest_code_blocks = []
    for quest_option in quest_traits_testeds:
        quest_option_list = quest_option.split(", ")
        quest_specific_code_block = "```\n"
        for trait in quest_option_list:
            percent_success = float(trait_success_chance_dict[animal_dict[trait]]) * 100
            quest_specific_code_block += (
                lamark_emoji_dict[trait] + " " + trait.ljust(16) + 
                trait_shorthand_dict[animal_dict[trait]].ljust(2) + 
                " " + "{:.0f}%".format(percent_success) + "\n"
            )

        quest_specific_code_block += "```"
        all_quest_code_blocks.append(quest_specific_code_block)


    # now we can compose the message text. 
    discord_message_text = (
        "Quest time. "+creature_name+" is eager to test their skills. Where shall we go? \n"+
        "```(% = chance of success at skill check. Quest succeeds if at 1+ check is passed.)```\n"+
        f"🇦 {quest_descriptions[0]}\n"+all_quest_code_blocks[0]+
        f"🇧 {quest_descriptions[1]}\n"+all_quest_code_blocks[1]+
        f"🇨 {quest_descriptions[2]}\n"+all_quest_code_blocks[2]
    )
    # discord_message_text = (
    #     "Quest time. "+creature_name+" is eager to test their skills. Where shall we go? \n\n"
    #     f"🇦 {quest_descriptions[0]} ({quest_traits_testeds_with_emojis[0]})\n"
    #     f"🇧 {quest_descriptions[1]} ({quest_traits_testeds_with_emojis[1]})\n"
    #     f"🇨 {quest_descriptions[2]} ({quest_traits_testeds_with_emojis[2]})\n"
    #     "\n\n"
    # )

    requestor_user = message_to_thread_from.author
    thread = await message_to_thread_from.create_thread(name="A Quest for "+creature_name)
    message = await thread.send(f"{requestor_user.mention}: "+discord_message_text)

    # keep track of this thread, and the options presented.  
    message_requestors[message.id] = message_to_thread_from.author
    quest_options_dict[message.id] = {
        '🇦': quest_descriptions[0],
        '🇧': quest_descriptions[1],
        '🇨': quest_descriptions[2],
    }

    # React to the message with the specified emojis
    for emoji in acceptable_emoji_responses:
        await message.add_reaction(emoji)    
    
    print("I've started a thread based on "+requestor_user.name+"'s quest initiation..")


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Various Game Methods
async def construct_starter_message_prompt():

    creature_pair_1 = engineMethods.get_two_nonzero_animals()
    creature_pair_2 = engineMethods.get_two_nonzero_animals()
    creature_pair_3 = engineMethods.get_two_nonzero_animals()

    starter_creature_options_dict = {
        '🇦': creature_pair_1,
        '🇧': creature_pair_2,
        '🇨': creature_pair_3,
    }

    starter_creature_text_options = {
        '🇦': creature_pair_1[0]['creature']+" + "+creature_pair_1[1]['creature'],
        '🇧': creature_pair_2[0]['creature']+" + "+creature_pair_2[1]['creature'],
        '🇨': creature_pair_3[0]['creature']+" + "+creature_pair_3[1]['creature'],
    }

    starter_creature_prompt = (
        "Welcome to ChimeraQuest. What combo shall we begin with?\n\n"
        f"🇦 **{starter_creature_text_options['🇦']}**\n"
        f"🇧 **{starter_creature_text_options['🇧']}**\n"
        f"🇨 **{starter_creature_text_options['🇨']}**\n"
        "\n\n"
    )
    return starter_creature_options_dict,starter_creature_prompt

async def get_players_creature(requestor_user):
    # check to see if the player already has a creature. 
    # returns bool and creature name if they do.

    # no tab at all? Player doesn't have a creature.
    if not sheets.sheet_exists("d"+str(requestor_user.id)):
        return False, None, None
    
    # fetch all rows, representing all creatures the player has.
    data = sheets.fetch_table_from_sheets("d"+str(requestor_user.id))
    header = data[0]
    all_player_creatures = data[1:]
    player_owned_creature_rows = []

    # loop through all rows in player_creatures
    for animal_row in all_player_creatures:
        # check for owned creatures.
        if animal_row[header.index('status')] == 'owned':
            player_owned_creature_rows.append(animal_row)
    
    # no owned creatures? 
    if len(player_owned_creature_rows) == 0:
        return False, None, None

    # get the first owned creature's name or species if blank. 
    if len(player_owned_creature_rows[0]) < len(header):
        name = "a "+player_owned_creature_rows[0][header.index('creature')]
    else:
        name = player_owned_creature_rows[0][header.index('creature_name_by_player')]+" (a "+player_owned_creature_rows[0][header.index('creature')]+")"
    
    #  finally, the creature's id. 
    creature_id = player_owned_creature_rows[0][header.index('creature_id')]

    return True, name, creature_id

async def send_creature_on_quest(reaction,user):
    # If ❌ was selected, delete the message.
    if reaction.emoji == '❌':
        await reaction.message.delete()
        return

    # get the quest selected by emoji. 
    selected_quest = quest_options_dict[reaction.message.id][reaction.emoji]
    print(user.name+" sent their creature on quest description: "+selected_quest)
    # clear option emojis for safety. 
    await reaction.message.clear_reactions()

    # get the player's creature id and name. 
    has_creature,creature_name,creature_id = await get_players_creature(user)

    # post a new message in this thread
    update_message = await reaction.message.channel.send(creature_name+" has been sent on a quest. They will return shortly...")
    
    # send the creature on a quest.
    quest_result = await quest.quest(creature_id,selected_quest)

    # compose a results message.
    quest_narrative = quest_result['quest_narrative']
    trait_changes_text = quest_result['trait_changes_text']
    # passfail = quest_result['passfail'] 

    quest_results_discord_message = (
        f"**{creature_name}** has returned from their quest:\n"
        f"```{quest_narrative}```\n"
        f"{trait_changes_text}\n"
    )
    await reaction.message.channel.send(quest_results_discord_message)
    # clear the update message
    await update_message.delete()

    # Update event. 
    events_new_row = [
        "d"+str(user.id),
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        creature_id,
        "quest completed",
        quest_narrative+"\n\n"+trait_changes_text,
    ]
    sheets.write_to_sam_sheets('Events', events_new_row)
    














# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Bot Powers



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# End.

client.run(discord_token)


