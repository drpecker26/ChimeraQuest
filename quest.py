
import openai
import sheets
import random
import engineMethods

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# openai stuff

COMPLETIONS_API_PARAMS = {
    "temperature": 0.0,
    "max_tokens": 3000,
    "model": "gpt-3.5-turbo",
    # "model": "gpt-4",
}

def answer_query_with_context(prompt) -> str:
    system_message = "You are a helpful assistant. \n"
    try:
        response = openai.ChatCompletion.create(
          messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
          ,**COMPLETIONS_API_PARAMS
        )
    except openai.error.RateLimitError:
        # Handle the rate limit error
        response = "Ah, Snap. The OpenAI service is currently overloaded. Sorry. Please try again later."
    else:
        # Handle the successful response
        response = response["choices"][0]["message"]["content"].strip(" \n")
    return response


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# questing

def get_three_random_quests():
    # fetch all quests and choose a random one. 
    quests_table = sheets.fetch_table_from_sheets('Quest')

    quest_text_column = [row[1] for row in quests_table]
    quest_traits_tested_column =  [row[2] for row in quests_table]
    quest_traits_tested_with_emojis_column = [row[3] for row in quests_table]

    random_indices = random.sample(range(len(quest_text_column)), 3)

    quest_descriptions = [quest_text_column[index] for index in random_indices]
    quest_traits_testeds = [quest_traits_tested_column[index] for index in random_indices]
    quest_traits_testeds_with_emojis = [quest_traits_tested_with_emojis_column[index] for index in random_indices]
    
    print(quest_descriptions)
    print(quest_traits_testeds_with_emojis)
    
    return quest_descriptions, quest_traits_testeds, quest_traits_testeds_with_emojis

async def quest(creature_id,quest_description):
    # sends creature on a quest, runs open ai to get a description of the quest, and returns the narrative. 

    # fetch the quest matching the description.  
    quest_text_column = sheets.fetch_table_from_sheets('Quest','description')
    quest_traits_tested_column = sheets.fetch_table_from_sheets('Quest','traits_tested')
    for index, quest_text in enumerate(quest_text_column):
        if quest_text == quest_description:
            quest_skills = quest_traits_tested_column[index]
            quest_skills = quest_skills.split(', ')
            break

    print("creature_id "+creature_id+" is going on quest: "+quest_text+", testing skills: "+str(quest_skills))

    # get creature for testing.
    animal_table = sheets.fetch_table_from_sheets('CreatureTraits')
    header_row = animal_table[0]
    for row in animal_table:
        if row[0] == creature_id:
            animal = row
            break
    else:
        # Handle case where no matching row was found
        animal = None
        print("Could not find creature with id "+creature_id+".")

    # Create a dictionary that maps each header to its corresponding index
    header_indices = {header: index for index, header in enumerate(header_row)}
    indices_to_lookup = [header_indices[header] for header in quest_skills]
    relevant_skill_attribute_scores = [animal[index] for index in indices_to_lookup]
    print("random animal is "+animal[0]+ " and is named "+animal[37]) if animal[37] else print("random animal is "+animal[0]+ " and has no name.")
    print(relevant_skill_attribute_scores)

    # look up trait power dicts
    trait_success_chance_dict,trait_description_dict,trait_shorthand_dict = engineMethods.get_trait_power_dicts()

    # get only the relevant descriptions and chances
    trait_descriptions = [trait_description_dict[key] for key in relevant_skill_attribute_scores]
    trait_success_chances = [trait_success_chance_dict[key] for key in relevant_skill_attribute_scores]

    print("chances of success for each trait:")
    print(trait_success_chances)

    # determine trial success. 
    # skill check line-broken text:
    skill_check_text = ""
    num_successes = 0
    num_failures = 0
    traits_succeeded = []

    for i in range(len(trait_success_chances)):
        if random.random() < float(trait_success_chances[i]):
            print(f"Success. Trait '{quest_skills[i]}' Score was {relevant_skill_attribute_scores[i]} (which is considered {trait_descriptions[i]}) and Chance was {trait_success_chances[i]}")
            num_successes += 1
            skill_check_text += f"The creature attempted to succeed using its trait '{quest_skills[i]}' with capability {trait_descriptions[i]}. It resulted in a Success!\n"
            traits_succeeded.append(quest_skills[i])
        else:
            print(f"Failure. Trait '{quest_skills[i]}' Score was {relevant_skill_attribute_scores[i]} (which is considered {trait_descriptions[i]}) and Chance was {trait_success_chances[i]}")
            num_failures += 1
            skill_check_text += f"The creature attempted to succeed using its trait '{quest_skills[i]}' with capability {trait_descriptions[i]}. It resulted in a Failure.\n"
    
    if num_successes == 0:
        quest_result = "Failure."
    elif num_successes == len(trait_success_chances):
        quest_result = "Smashing Success!"
    else:
        quest_result = "Success."
    print("The quest result was: "+quest_result)
    print("====\n\n")

    # based on these results, prompt GPT for a narrative describing what happened. 
    name_line = "The Creature's name is: " + str(animal[37]) + "\n" if animal[37] else "The Creature has no name. \n"
    prompt = "I will describe for you a creature undertaking a task. I would like you to tell me a 1 paragraph story of no longer than 100 words of this creature succeeding at, or failing at, this task.\n"+\
    "First, I will describe the creature's goal. "+\
    "Then, I will describe some of the creatures physical and behavioral traits. "+\
    "Then, I will list some skills the creature possesses, and whether or not that skill check passed."+\
    "Finally, I will describe the outcome of the task.\n\n"+\
    "The Creature's species is: "+str(animal[1])+"\n"+\
    name_line+\
    "Creature Goal: "+quest_text+"\n"+\
    "Creature Physical Traits: "+str(animal[2])+"\n"+\
    "Creature Behavioral Traits: "+str(animal[3])+"\n"+\
    "The Creatures skill checks resolved thus:\n\n"+\
    skill_check_text+\
    "The Quest Resulted in a "+quest_result+"\n\n"+\
    "Writing notes follow: \n"+\
    "1. Note that most often, the creature will succeed at skills it is strong at, and fail at skills it is not strong at. "+\
    "Sometimes the creature will fail at a skill they are strong at, or succeed at a skill they are not strong at. "+\
    "Make references to every skill check provided, and describe how that success helped (or failure hindered) meeting the creature's goal.\n"+\
    "2. Where possible, reference the creatures physical or behavioral traits. However, this is not required.\n"+\
    "3. If you think it would be entertaining, feel free to embellish on details.\n"+\
    "4. The tone should be DRAMATIC! Use ALL CAPS when things get EXCITING!\n"
    "5. When identifying the creature, reference both the name and the species, E.g. 'Sammy the Snow Leopard'. If it has no name, reference only the species, e.g. 'the Snow Leopard'. \n\n"

    print(prompt)
    print("===========\n\n")
    quest_narrative = answer_query_with_context(prompt)
    print(quest_narrative)

    print("A "+str(animal[0])+" attempted to "+quest_text+". it was a "+quest_result)
    print("===========\n\n")

    # Depending on quest result, adjust lamarks. 
    if quest_result == "Success.":
        # increase lamarks for all trait that succeeded by 1.
        trait_changes_text =adjust_lamarks(creature_id, list_of_traits_to_improve = traits_succeeded, delta = 1)
    elif quest_result == "Smashing Success!":
        # increase lamarks for all trait that succeeded by 3.
        trait_changes_text = adjust_lamarks(creature_id, list_of_traits_to_improve = traits_succeeded, delta = 3)
    elif quest_result == "Failure.":
        # decrease lamarks for all traits by 1.
        trait_changes_text = adjust_lamarks(creature_id, list_of_traits_to_improve = quest_skills, delta = -1)
    
    return {
        "quest_narrative": quest_narrative,
        "trait_changes_text": trait_changes_text,
        # "passfail": quest_result,
    }

def adjust_lamarks(creature_id, list_of_traits_to_improve, delta=1):
    # Fetch the table
    table = sheets.fetch_table_from_sheets('CreatureTraits')
    header_row = table[0]
    data_rows = table[1:]

    # Find the row with the specified creature_id
    target_row = None
    for row in data_rows:
        if row[0] == creature_id:
            target_row = row
            break

    # If the creature_id wasn't found, raise an error
    if target_row is None:
        raise ValueError(f"No row found with creature_id '{creature_id}'")

    # Update the values for the specified traits
    for trait in list_of_traits_to_improve:
        if trait in header_row:
            # Calculate the new value for the trait
            current_value = int(target_row[header_row.index(trait)])
            new_value = current_value + delta

            # cannot go below -1 or above 100
            new_value = -1 if new_value < -1 else new_value
            new_value = 100 if new_value > 100 else new_value
                
            # Update the value in the row
            target_row[header_row.index(trait)] = str(new_value)

    # Write the updated table back to Google Sheets
    sheets.update_sam_sheets('CreatureTraits',creature_id, target_row)

    # return with the text descripting all trait changes. 
    if delta == 1:
        trait_changes_text = "👍 "
        for trait in list_of_traits_to_improve:
            trait_changes_text += f"{trait} "
        trait_changes_text += "**improved** slightly. 👍"
    if delta == 3:
        trait_changes_text = "🎉 "
        for trait in list_of_traits_to_improve:
            trait_changes_text += f"{trait} "
        trait_changes_text += "**improved** greatly. 🎉"
    if delta == -1:
        trait_changes_text = "💩 "
        for trait in list_of_traits_to_improve:
            trait_changes_text += f"{trait} "
        trait_changes_text += "**decreased** slightly. 💩"
    
    return trait_changes_text






