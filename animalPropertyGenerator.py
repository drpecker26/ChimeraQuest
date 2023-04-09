
import openai
import sheets

COMPLETIONS_API_PARAMS = {
    "temperature": 0.0,
    "max_tokens": 3000,
    "model": "gpt-3.5-turbo",
    # "model": "gpt-4",
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
    return response



print("testing...")

output_table = []

# let's set up an intake/export to sheets to be able to bulk process.
creature_traits_table = sheets.fetch_table_from_sheets('CreatureTraits')
for i, row in enumerate(creature_traits_table):
    # debug: 
    # animal_name = 'Blue Dragon'
    if i == 0:
        # heading. 
        continue
    if i <= 253:
        # I've already got these animals. 
        continue
    animal_name = row[0]
    # if i >= 100:
    #     break
    
    print(f"Processing {animal_name}...")
    list_of_creatures = animal_name+\
        " \n\n"
    prompt = "I will give you a list of creatures.\n"+\
            "For each creature, I would like you to provide a dictionary of characteristics. "+\
            "The dictionary should include both aesthetic and behavioral properties. "+\
            "aesthetic properties are those that a viewer may observe from pictures of the animal. \n"+\
            "behavioral properties are those that describe how the animal lives and accomplishes its goals. "+\
            "Include what the animal is particularly adept at, such as 'Excellent swimmer'."+\
            "Do not include its predators or habitat.\n"+\
            "Provide your response in the exact syntax as provided in the example; note the punctuation, and lack of spaces after the commas.\n"+\
            "The animal in question is: \n\n"+\
            list_of_creatures+\
            "Here is an example response: \n"+\
            "animal: 'Mountain Goat'\n"+\
            "aesthetic_properties: 'White,Fur coat,Horned,Curved hooves,Bearded,Four Legs,Medium Size' \n"+\
            "behavioral_properties: 'Agile,Surefooted,Social,Herbivore,Climber,Territorial'"
    gptresponse = answer_query_with_context(prompt)
    # Split the string into lines
    lines = gptresponse.split('\n')

    # Iterate over the lines and extract the values
    animal = ''
    aesthetic_properties = ''
    behavioral_properties = ''
    for line in lines:
        if line.startswith('animal:'):
            animal = line.split("'")[1]
        elif line.startswith('aesthetic_properties:'):
            aesthetic_properties = line.split("'")[1]
        elif line.startswith('behavioral_properties:'):
            behavioral_properties = line.split("'")[1]
    
    # Append the values to the table
    # output_table.append([animal, aesthetic_properties, behavioral_properties])
    # Export the table to sheets, row by row. 
    print([animal, aesthetic_properties, behavioral_properties])
    sheets.write_to_sam_sheets('ScriptDumps',[animal, aesthetic_properties, behavioral_properties],'A')







# animal creation, batch entered. 
# list_of_biomes = "Subtropical Scrubland,Tropical Steppe,Temperate Steppe,Subtropical Steppe,Tropical Veld,Temperate Veld,Subtropical Veld,Tropical Wetland,Temperate Wetland,Subtropical Wetland"+\
#       " \n\n"
# prompt = "I will give you a short list of biomes. Please provide me a handful of visually distinctive animals in that biome. \n"+\
#         "For each biome, pick 4 to 8 animals that are as widely representative of the region as possible. Pick animals that are visually distinctive from one another."+\
#         "I would encourage you to include mythical animals such as Dragon, Chupacabra, Hydra, Pegasus, as well, if you feel such a creature might live in that biome."+\
#         "The list of biomes to include are: \n\n"+\
#         list_of_biomes+\
#         "The format for your response should be: \n"+\
#         "BIOME:animal,animal,animal,animal \n"+\
#         "I am expecting somewhere around 50 rows. \n\n"+\
#         "Examples of biomes and animals (please do NOT include these in your response, unless I have otherwise explicitly asked for the biome): \n"+\
#         "Temperate Swamp:Black Bear,White-tailed Deer,Great Blue Heron,Eastern Painted Turtle,Raccoon\n"+\
#         "Deep Ocean:Giant Squid,Anglerfish,Dumbo Octopus,Fangtooth Fish,Gulper Eel,Viperfish,Deep-Sea Dragonfish,Bioluminescent Jellyfish\n"+\
#         "Coral Reef:Clownfish,Parrotfish,Sea Turtle,Reef Shark,Stingray,Moray Eel,Starfish,Seahorse\n"+\
#         "Arctic Tundra:Polar Bear,Arctic Fox,Musk Ox,Snowy Owl,Arctic Hare,Caribou,Lemming,Walrus\n"+\
#         "Alpine Grassland:Mountain Goat,Alpine Ibex,Marmot,Golden Eagle,Chamois,Snowfinch,Yak,Himalayan Tahr\n"


# biome creation - something like this. 
# prompt = "I will give you a short list of biomes. Please provide me a handful of visually distinctive animals in that biome. \n"+\
#         "The biomes should be specific enough to be visually distinctive and containing distinctive flora and fauna,"+\
#         "but not so specific as to be a single location or named region. "+\
#         "for each biome, pick 4 to 8 animals that are as widely representative of the region as possible. Pick animals that are visually distinctive from one another."+\
#         "The format for your response should be: \n"+\
#         "BIOME:animal,animal,animal,animal \n"+\
#         "I am expecting somewhere around 50 rows. \n\n"+\
#         "Examples of biomes and animals (please do NOT include these in your response, unless I have otherwise explicitly asked for the biome): \n"+\
#         "Temperate Swamp:Black Bear,White-tailed Deer,Great Blue Heron,Eastern Painted Turtle,Raccoon\n"+\
#         "Deep Ocean:Giant Squid,Anglerfish,Dumbo Octopus,Fangtooth Fish,Gulper Eel,Viperfish,Deep-Sea Dragonfish,Bioluminescent Jellyfish\n"+\
#         "Coral Reef:Clownfish,Parrotfish,Sea Turtle,Reef Shark,Stingray,Moray Eel,Starfish,Seahorse\n"+\
#         "Arctic Tundra:Polar Bear,Arctic Fox,Musk Ox,Snowy Owl,Arctic Hare,Caribou,Lemming,Walrus\n"+\
#         "Alpine Grassland:Mountain Goat,Alpine Ibex,Marmot,Golden Eagle,Chamois,Snowfinch,Yak,Himalayan Tahr\n"



