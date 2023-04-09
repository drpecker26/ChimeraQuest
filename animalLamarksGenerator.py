
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
    if i < 25:
        # heading. or already-completed animal. 
        continue
    animal_name = row[0]
    if i >= 50:
        break
    
    print(f"Processing {animal_name}...")
    animal_name = animal_name+\
        " \n\n"
    prompt = "I will give you the name of an animal.\n"+\
            "I will also give you a list of abilities, and what I mean by those abilities.\n"+\
            "Your job will be to give me an array of numbers representing that animal's respective capability in that ability. "+\
            "The range of numbers you give shall be -1, or between 1 and 50.\n "+\
            "-1 represents a complete lack of that ability. For example, a Moose cannot fly in any sense, and so would score -1 for Fly.\n "+\
            "Low numbers represent a low capability in that ability. For example, a Flying Squirrel can glide, but not fly, and so would score 5 for Fly.\n "+\
            "High numbers represent a high capability in that ability. For example, an Eagle can fly and dive, and so would score 49 for Fly.\n "+\
            "Make your best guess. If you do not know, or are unsure, put -1.\n "+\
            "What follows is the comprehensive list of abilities, in order. \n"+\
            " - Climb: Ability to physically traverse vertically their habitat, as in to climb trees or rocks or cliffs. \n"+\
            " - Strength: Ability to exert physical force, often used for hunting or defense. \n"+\
            " - Agile: Ability to move quickly and accurately, as in to dodge predators or catch prey. \n"+\
            " - Endurance: Ability to sustain activity for extended periods of time without getting exhausted. \n"+\
            " - Run: Ability to traverse horizontal habitats far or quickly. \n"+\
            " - Swim: Ability to swim along the surface of, or submersed in, water. \n"+\
            " - Dive: Ability to descend depths of water, without needing to surface for air for lengths of time. \n"+\
            " - Fly: Ability to float, glide, soar, or otherwise traverse the atmosphere. \n"+\
            " - Dig: Ability to burrow, penetrate, or dig earth or other material.  \n"+\
            " - Hide: Ability to defensively obscure oneself from predators. Camouflage.  \n"+\
            " - Stealth: Ability to approach prey without being detected. Sneakiness. \n"+\
            " - Resistance: Ability to survive extreme environmental conditions elements. Drought tolerant, cold tolerant.  \n"+\
            " - Scrounge: Ability to acquire nutrients. Flexible diet.  \n"+\
            " - Fight: Ability to kill prey, or defend against predators.  \n"+\
            " - Defend: Ability to defend against predators, perhaps by physical resources such as Hard shell, Quills, stingers, thorns.  \n"+\
            " - Social: Ability to cooperate, communicate, or otherwise convey information or signals to other members of the species through various means such as vocalizations or body language. \n"+\
            " - Intelligence: Ability to solve problems, learn from experience, and make decisions. To have good memory. \n"+\
            " - Heavy: Ability to use one's weight to one's advantage. \n"+\
            " - Sight: Ability to visually discern opportunities or threats. Far sight, or Peripheal perspective.  \n"+\
            " - Smell: Ability to discern opportunities or threats by means of Small. \n"+\
            " - Hearing: Ability to discern opportunities or threats by means of Sound, such as by Echolocation. \n"+\
            " - Adaptation: Ability to flexibly adapt to changing environments or situations quickly. \n"+\
            " - Mimicry: Ability to imitate sounds, appearances, or behaviors of other species or objects in the environment. \n"+\
            " - Venom: Ability to produce or inject venom as a means of defense or offense. \n"+\
            " - Bioluminescence: Ability to produce light, often for communication or hunting in the dark. \n"+\
            " - Regeneration: Ability to regrow limbs or body parts that have been lost or damaged. \n"+\
            "Provide your response in the exact syntax as provided in the example. Include the animal name before the colon. note the punctuation. Make sure the order matches the order of abilities I have provided. \n"+\
            "Here is an example response: \n"+\
            "Mountain Goat: 40,30,35,40,30,5,-1,-1,5,20,10,30,10,20,25,5,10,30,35,25,30,10,-1,-1,-1,-1\n\n "+\
            "The animal in question is: \n\n"+\
            animal_name

    gptresponse = answer_query_with_context(prompt)
    print(gptresponse)
    animal = gptresponse.split(":")[0].strip()
    matrix = gptresponse.split(":")[1].strip()

    # Append the values to the table
    print(animal+": "+matrix)
    sheets.write_to_sam_sheets('ScriptDumps',[animal, matrix], 'D')








