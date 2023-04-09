
import os

# stability.ai stuff
import base64
import requests

# stable diffusion stuff. 
engine_id = "stable-diffusion-v1-5"
api_host = os.getenv('API_HOST', 'https://api.stability.ai')
api_key = os.environ.get('STABILITY_KEY')

if api_key is None:
    raise Exception("Missing Stability API key.")

text_prompt_image = 'an image of a single, fantastical creature in its natural habitat that has some chimeric combination of the following traits: golden fur, sharp teeth and claws, muscular build, powerful roar, excellent vision, mane (in males), streamlined body, smooth skin, blowhole for breathing, flippers for swimming, echolocation for communication, intelligent.'

response = requests.post(
    f"{api_host}/v1/generation/{engine_id}/text-to-image",
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    },
    json={
        "text_prompts": [
            {
                "text": text_prompt_image
            }
        ],
        "cfg_scale": 7,
        "clip_guidance_preset": "FAST_BLUE",
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 30,
    },
)


print("testing3...")
if response.status_code != 200:
    raise Exception("Non-200 response: " + str(response.text))

data = response.json()

print("testing4...")

for i, image in enumerate(data["artifacts"]):
    with open(f"./out/v1_txt2img_{i}.png", "wb") as f:
        f.write(base64.b64decode(image["base64"]))







print("done!")









