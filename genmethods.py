from tqdm import tqdm
import os
import time
import google.generativeai as genai
from logger import get_logger
import pollinations
import random
from uuid import uuid4
from urllib.parse import quote
import requests

logger = get_logger()

# image_model: pollinations.ImageModel = pollinations.image(
# model = pollinations.image_default,
# seed = random.randint(0,1000),
# width = 1920,
# height = 1080,
# enhance = False,
# nologo = True,
# private = False,
# )


def genscript(api_key,channel_name,proj_prompt,proj_name,script_path):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(
        f"Create a detailed YouTube script for the channel {channel_name}. The video should present and explain the concept of '{proj_prompt}' in a clear, engaging, and experimental way (predict additional knowledge and features on your own). Include intuitive and innovative ideas to illustrate the concept effectively, making it relatable and intriguing for viewers. Add a captivating introduction, experimental demonstrations, technical specifications based on product (like for example power and torque for vehicles), real-life applications, and a compelling conclusion that ties everything together. It should strictly be in a format 'Title:<Engaging and Catchy video title like upcoming {proj_name} to increase user clicks>\nScript:<Engaging Script>' avoid use of suggestions, third person references, Including Steps, or having visual and audio suggestions like 'intro music or video playing etc' just use direct script suitable to fed into a TTS model"
    )
    logger.debug(response.text)
    video_title,script=response.text.split('Script:')
    try:
        video_title=video_title.split('Title: ')[1]
    except Exception as e:
        logger.error(f"Error in Generating Script: {e}")
        video_title=video_title.replace("Title: ","")

    with open(os.path.join(script_path,"script.txt"),"w") as f:
        f.write(script)
    with open(os.path.join(script_path,"title.txt"),"w") as f:
        f.write(video_title)
    logger.info("Script exported to script.txt")
    return video_title,script


def genprompts(proj_prompt,n_prompts=10):
    llm_prompt=f"""You are a prompt generator AI, that generates {n_prompts} random prompts on the given topic for getting realisting looking images from a text to image model, 
            the prompts should include prompts to generate images such as introduction of the given product by the company, and images of that product from different angles and realistic environments and each prompth should be plain text model without any headers or much special characters starting from its indexing like 1. <prompt 1 text>\n 2. <prompt 2 text> and so on."""
    
    text_model: pollinations.TextModel = pollinations.text(
    frequency_penalty = 1,
    presence_penalty = 0.5,
    temperature = 1,
    top_p = 1,
    model = pollinations.text_default,
    stream = True,
    contextual = True, # True: Holds conversation context up to 10. False: Has no conversation context
    system = llm_prompt
    )
    
    img_prompt=text_model.generate(
    prompt=proj_prompt,
    display=True
    ).text
    img_prompts= [line.strip().split(". ",1)[1] for line in img_prompt.split("\n") if line.strip()] #convert generated text list into python list
    return img_prompts


# def genimages(prompts, genpath):
#     for pr in tqdm(prompts, total=len(prompts), desc="Generating Images"):
#         retries = 3
#         for attempt in range(retries):
#             try:
#                 imgpath=os.path.join(genpath, f"gen_{random.randint(1,1000)}.png")
#                 image_model.generate(
#                     prompt=pr,
#                     save=True,
#                     file=imgpath,
#                 )
#                 time.sleep(1)
#                 break  # Break the retry loop if successful
#             except Exception as e:
#                 logger.error(f"Error: {e}. Attempt {attempt + 1} of {retries}.")
#                 if attempt < retries - 1:  # Retry only if attempts are left
#                     time.sleep(2 ** attempt)  # Exponential backoff
#                 else:
#                     logger.error("Max retries reached. Skipping this prompt.")
#                     raise e


def genimages(prompts, genpath):
    """
    Generate images using Pollinations.ai API
    Args:
        prompts (list): List of image prompts
        genpath (str): Output directory path for generated images
    """
    
    # Ensure output directory exists
    os.makedirs(genpath, exist_ok=True)
    
    # Base URL for the Pollinations API
    base_url = "https://image.pollinations.ai/prompt"
    
    # Default parameters matching the original image_model
    params = {
        'model': 'stable-diffusion',  # pollinations.image_default
        'width': 1920,
        'height': 1080,
        'enhance': 'false',
        'nologo': 'true',
        'private': 'false'
    }
    
    time.sleep(1)  # Initial delay as in original
    
    for pr in tqdm(prompts, total=len(prompts), desc="Generating Images"):
        try:
            # Generate new random seed for each image
            params['seed'] = random.randint(0, 1000)
            
            # URL encode the prompt
            encoded_prompt = quote(pr)
            
            # Construct full URL with parameters
            url = f"{base_url}/{encoded_prompt}"
            params['models']=random.choice(['stable-diffusion','flux-realism'])
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{query_string}"
            
            # Make request with same timeout as original
            response = requests.get(full_url, timeout=30)
            response.raise_for_status()
            
            # Generate unique filename
            filename = f"gen_{str(uuid4())[:8]}.png"
            filepath = os.path.join(genpath, filename)
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(response.content)
                
            time.sleep(1)  # Same delay between images as original
            
        except Exception as e:
            logger.error(e)
            print("Generation on hold for 30s...")
            logger.info("Generation on hold...")
            time.sleep(30)

