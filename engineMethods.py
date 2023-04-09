import openai
import sheets
import os
import uuid
import base64
import requests
import random

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# stability.ai stuff
sd_engine_id = "stable-diffusion-v1-5"
sd_api_host = os.getenv('API_HOST', 'https://api.stability.ai')
sd_api_key = os.environ.get('STABILITY_KEY')
if sd_api_key is None:
    raise Exception("Missing Stability API key.")

def breed_generate_images(parent_id_1,parent_id_2,new_aesthetic_traits,new_behavioral_traits,num_samples=3):
    text_prompt_image = "an image of a single, fantastical creature in its natural habitat "+\
        "that has some chimeric combination of the following traits: "+\
        new_aesthetic_traits+", "+new_behavioral_traits+\
        "the entire creature can be seen from the front, and the creature is fit within the frame. "+\
        "The art style should be semi-realistic, colorful, detailed. "

    print("=-=-=--=-=-==--=-==--==-=-\n")
    print("Sending request to SD: "+text_prompt_image)
    response = requests.post(
        f"{sd_api_host}/v1/generation/{sd_engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {sd_api_key}"
        },
        json={
            "text_prompts": [{"text": text_prompt_image}],
            "cfg_scale": 7,
            "clip_guidance_preset": "FAST_BLUE",
            "height": 512,
            "width": 512,
            "samples": num_samples,
            "steps": 30,
        },
    )
    if response.status_code != 200:
        print("SD.AI had a Non-200 response: " + str(response.text))
        raise Exception("Non-200 response: " + str(response.text))
    
    print("SD.AI returned with 200 response. Success.")
    data = response.json()

    # create unique strings for image names; these are temporary because they might not be saved to sheets.
    unique_image_names = []
    for i, image in enumerate(data["artifacts"]):
        unique_image_name = parent_id_1+"~"+parent_id_2+"~"+str(i)+"~"+uuid.uuid4().hex+".png"
        with open(f"./out/"+unique_image_name, "wb") as f:
            f.write(base64.b64decode(image["base64"]))
        unique_image_names.append(unique_image_name)

    return unique_image_names

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# openai stuff
COMPLETIONS_API_PARAMS = {
    "temperature": 0.0,
    "max_tokens": 3000,
    "model": "gpt-3.5-turbo",
}

def answer_query_with_context(prompt) -> str:
    system_message = "You are a helpful assistant. \n"+\
                    "When responding, provide no context, only a print of multiple rows of text.\n"+\
                    "Each response should print on a new line. \n"
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
    
    print("openai returned with a Success.")
    return response


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# sheets data management
def get_sheets_header(tab_name):
    data = sheets.fetch_table_from_sheets(tab_name)
    return data[0]

def get_animal_row(animal_id, data):
    for row in data:
        if row[0] == animal_id:
            return row
    print(f"Animal {animal_id} not found in table")
    return None

def get_two_nonzero_animals():
    data = sheets.fetch_table_from_sheets('CreatureTraits')
    header = data[0]
    animal_1_row = None
    animal_2_row = None

    # get two random animals that have a value in column "TotalPower" that is greater than zero
    while animal_1_row is None or animal_2_row is None:
        animal_1_row = random.choice(data[1:])
        animal_2_row = random.choice(data[1:])
        if animal_1_row[header.index("starter_creature")] == "0" or animal_2_row[header.index("starter_creature")] == "0":
            animal_1_row = None
            animal_2_row = None

    animal_1_dict = {header[i]: animal_1_row[i] for i in range(0, len(header))}
    animal_2_dict = {header[i]: animal_2_row[i] for i in range(0, len(header))}

    return animal_1_dict,animal_2_dict

def get_trait_power_dicts():
    # fetch the table and return usable dicts. 
    trait_success_chance_dict = {}
    trait_description_dict = {}
    trait_shorthand_dict = {}

    trait_power_table = sheets.fetch_table_from_sheets("TraitPower")
    
    # Loop through each row in the trait_power_table
    for row in trait_power_table[1:]:
        traitscore = row[0]
        success_chance = row[1]
        description = row[2]
        shorthand = row[3]
        
        # Add key-value pairs to the dictionaries
        trait_success_chance_dict[traitscore] = success_chance
        trait_description_dict[traitscore] = description
        trait_shorthand_dict[traitscore] = shorthand
    
    return trait_success_chance_dict,trait_description_dict,trait_shorthand_dict


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# breeding

async def breed(animal_id_1,animal_id_2):
    try:
        # First, fetch the rows associated with the two animals.
        data = sheets.fetch_table_from_sheets('CreatureTraits')
        header = data[0]
        animal_1_row = get_animal_row(animal_id_1, data)
        animal_2_row = get_animal_row(animal_id_2, data)
        animal_1_dict = {header[i]: animal_1_row[i] for i in range(1, len(header))}
        animal_2_dict = {header[i]: animal_2_row[i] for i in range(1, len(header))}

        # combine the animal traits
        new_aesthetic_properties,new_behavioral_properties = breed_trait_combination(
            animal_1_dict['creature'],animal_2_dict['creature']
            ,animal_1_dict['aesthetic_properties'],animal_2_dict['aesthetic_properties']
            ,animal_1_dict['behavioral_properties'],animal_2_dict['behavioral_properties']
            )
        
        # now identify a few names. 
        new_name_list = breed_name_creation(
            animal_1_dict['creature'],animal_2_dict['creature']
            ,new_aesthetic_properties,new_behavioral_properties
        )

        # now generate a few images for the creature.
        unique_image_names = breed_generate_images(
            animal_1_row[0],animal_2_row[0]
            ,new_aesthetic_properties,new_behavioral_properties
            )
        
        # print("The new names are: " + ", ".join(new_name_list))
        # print("the new image names are: " + ", ".join(unique_image_names))

        # generate other known metadata for the bred creature.
        selected_creature_ancestors = animal_1_dict['creature']+", "+animal_2_dict['creature']

        # Generate a random selection of the new creature's traits. Logic:
        new_lamarkian_properties = breed_lamarkian_combination(animal_1_row[0],animal_2_row[0])

        return {
                "error": False,
                "new_name_list": new_name_list,
                "unique_image_names": unique_image_names,
                "ancestors": selected_creature_ancestors,
                "aesthetic_properties": new_aesthetic_properties,
                "behavioral_properties": new_behavioral_properties,
                "lamarkian_properties": new_lamarkian_properties
            }
    except:
        return {
            "error": True,
        }

def breed_trait_combination(
        parent_name_1,parent_name_2
        ,parent_a_properties_1,parent_a_properties_2
        ,parent_b_properties_1,parent_b_properties_2):
    # Trait combination. 
    prompt = "I will describe the aesthetic and behavioral traits of the fantastical parents of a fantastical creature.\n"+\
            "I would like you to describe the traits of the offspring by smartly combining the traits of its parent creatures.\n"+\
            "Some parent traits may combine without conflict. "+\
                "For example, consider a creature whose parents have the traits 'Fur Coat' and 'Long Tail'. In cases like these, include both traits in the offspring.\n"+\
            "Some parent traits may conflict, but there is a realistic midpoint between the two. "+\
                "For example, consider a creature whose parents have the traits 'Four Legs' and '8 Legs'. In cases like these, include one trait representing an average, such as 'Six Legs'.\n"+\
            "Some parent traits may conflict, and there is no sensical midpoint between the two. "+\
                "For example, consider a creature whose parents have the traits 'Talons' and 'Hooves'. In cases like these, try your best to combine them, or simply pick one trait, such as 'Sharp Hooves'.\n"+\
            "Finally, I would like you to fabricate one new aesthetic trait, and one new behavioral trait, each of which was NOT present in either of the parents."+\
                "These novel traits should not conflict with any existing traits, but they may be surprising or fantastical or outlandish.\n"+\
            "The creatures parents are called: "+parent_name_1+" and "+parent_name_2+".\n"+\
            "The creatures parents have the following aesthetic traits: "+parent_a_properties_1+", "+parent_a_properties_2+".\n"+\
            "The creatures parents have has the following behavioral traits: "+parent_b_properties_1+", "+parent_b_properties_2+".\n"+\
            "In your response, give me one line for aesthetic traits, and then a second line for behavioral traits. I would like no explanation, no parantheses, no numbers. "+\
            "Give me as many traits as you can, but no more than 15 aesthetic traits and no more than 15 behavioral traits. "+\
            "Please give me resultant aesthetic and behavioral traits now." 
    gptresponse = answer_query_with_context(prompt)
    new_aesthetic_properties = gptresponse.split('\n')[0]
    new_behavioral_properties = gptresponse.split('\n')[1]
    return new_aesthetic_properties,new_behavioral_properties
    
def breed_name_creation(
        parent_name_1,parent_name_2,aesthetic_properties,behavioral_properties
        ):
    # Name creation. 
    prompt = "I will describe a fantastic creature. I would like you to brainstorm for me some novel names for this creature.\n"+\
            "The names could be derived from the creature's appearance, behavior, or from the names of their animal ancestors.\n"+\
            "The creature is descended from the two following creatures: "+parent_name_1+" and "+parent_name_2+".\n"+\
            "The creature has the following aesthetic properties: "+aesthetic_properties+".\n"+\
            "The creature has the following behavioral properties: "+behavioral_properties+".\n"+\
            "For your understanding, I provide 3 example names (and in parantheses, the animals they came from): \n"+\
            "Bearded Squidoat (from Mountain Goat and Giant Squid)\n"+\
            "Elkuchin (from Capuchin Monkey and Elk)\n"+\
            "Rhealope (from Saiga Antelope and Rhea)\n"+\
            "In your response, give me JUST one name per row; no explanation, no parantheses, no numbers. "+\
            "Please give me exactly 3 names now." 
    gptresponse = answer_query_with_context(prompt)
    new_name_list = gptresponse.split('\n')
    return new_name_list

def breed_lamarkian_combination(parent_id_1,parent_id_2):
    # look up all of the lamarkian properties in the game. 
    lamarkian_properties = sheets.fetch_table_from_sheets("Lamarks", column_name="lamark")

    # look up the lamarkian properties for the parents.
    # First, fetch the rows associated with the two animals.
    data = sheets.fetch_table_from_sheets('CreatureTraits')
    header = data[0]
    animal_1_row = get_animal_row(parent_id_1, data)
    animal_2_row = get_animal_row(parent_id_2, data)
    animal_1_dict = {header[i]: animal_1_row[i] for i in range(1, len(header))}
    animal_2_dict = {header[i]: animal_2_row[i] for i in range(1, len(header))}

    # for each lamarkian property, randomly select one of the two parent values.
    new_lamarkian_properties = {}
    for lamarkian_property in lamarkian_properties:
        new_lamarkian_properties[lamarkian_property] = random.choice([animal_1_dict[lamarkian_property],animal_2_dict[lamarkian_property]])

    return new_lamarkian_properties

def get_animal_strengths_and_weaknesses(creature_id):
    # fetch animal stats.
    data = sheets.fetch_table_from_sheets('CreatureTraits')
    header = data[0]
    animal_row = get_animal_row(creature_id, data)
    animal_dict = {header[i]: animal_row[i] for i in range(0, len(header))}

    # look up all of the lamarkian properties in the game. 
    lamarkian_properties_table = sheets.fetch_table_from_sheets("Lamarks")
    lamarkian_properties = []
    lamark_emoji_dict = {}
    for row in lamarkian_properties_table[1:]:
        lamark = row[0]
        emoji = row[2]
        lamarkian_properties.append(lamark)
        # Add key-value pair
        lamark_emoji_dict[lamark] = emoji

    # look up trait power dicts
    trait_success_chance_dict,trait_description_dict,trait_shorthand_dict = get_trait_power_dicts()

    # Create a dictionary of lamarkian properties with their values as integers
    lamarkian_properties_dict = {k: int(animal_dict[k]) for k in lamarkian_properties}
    # Filter out the values of -1; let's generally not tell the player what the creature cannot do. 
    filtered_dict = {k: v for k, v in lamarkian_properties_dict.items() if v != -1}

    # Get the lowest 4 values
    lowest_keys = sorted(filtered_dict, key=filtered_dict.get)[:4]
    lowest_values = [filtered_dict[k] for k in lowest_keys]
    lowest_tuples = list(zip(lowest_keys, lowest_values))

    # But I do want to tell them about ONE thing the creature cannot do. 
    if -1 in lamarkian_properties_dict.values():
        keys_with_neg_one = [k for k, v in lamarkian_properties_dict.items() if v == -1]
        key = random.choice(keys_with_neg_one)
        lowest_tuples.append((key, -1))

    highest_keys = sorted(filtered_dict, key=lambda x: -filtered_dict[x])[:5]
    highest_values = [filtered_dict[k] for k in highest_keys]
    highest_tuples = list(zip(highest_keys, highest_values))

    #  Finally, prepare the string.
    working_string = ""
    working_string += "Some of the "+animal_dict['creature']+"'s strengths:\n"
    for prop, val in highest_tuples:
        working_string += f"{lamark_emoji_dict[str(prop)]} {prop}: {trait_shorthand_dict[str(val)]}\n"

    working_string += "\nSome of the "+animal_dict['creature']+"'s weaknesses:\n"
    for prop, val in lowest_tuples:
        working_string += f"{lamark_emoji_dict[str(prop)]} {prop}: {trait_shorthand_dict[str(val)]}\n"
    
    return working_string





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# questing



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# tbd



