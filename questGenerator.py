
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

prompt = "I will give you a list of abilities, and what I mean by those abilities.\n"+\
        "These are abilities of intelligent pet animals who understand english and can accomplish everyday tasks. \n"+\
        "Your job will be to brainstorm quests for these animals to go on that will test between 2 to 5 of these abilities. "+\
        "A given quest should test some or all of the abilities. "+\
        "The quests should range in tone from high stakes / exciting to mundane, every day tasks that humans do. "+\
        "The quests should be detailed and specific. "+\
        "In addition, you are to identify the specific abilities being tested. I will give some examples below. \n\n"+\
        "What follows is the comprehensive list of abilities. \n"+\
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
        "Provide your response in the exact syntax as provided in the example. Include the quest before the colon, and the abilities being tested after. \n"+\
        "Here are four example quests: \n"+\
        "Swim to the bottom of the Mississippi river and retrieve the safe from the steamboat shipwreck:Dive, Smell, Strength\n"+\
        "Impersonate an online Twitch Streamer to convince their audience to donate to the local zoo:Mimicry, Social\n"+\
        "Find and retrieve some coconuts from atop the coconut tree for someone's birthday party:Sight, Climbing\n"+\
        "Participate in a crowded Black Friday event and beat the rush to buy a new widescreen TV:Run, Agile, Heavy, Sight\n"+\
        "Now tell me 3 quest ideas that specifically include Dig. \n"
print(prompt)
gptresponse = answer_query_with_context(prompt)
print(gptresponse)









