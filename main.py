import os
from dotenv import load_dotenv
from config import channel_name,default_dir,proj_prompt, proj_name,images_per_video
from genmethods import genscript,genimages,genprompts
from logger import get_logger
from media_methods import create_audio_with_background,create_video_with_transitions,add_intro_and_closure

load_dotenv()

logger=get_logger()

# images_per_video=15 #override

meta_path="meta/"

def main():
    
    os.makedirs(default_dir,exist_ok=True)

    proj_path=os.path.join(default_dir,proj_name)
    img_path=os.path.join(proj_path,"images")
    script_path=os.path.join(proj_path,"script")
    
    os.makedirs(proj_path,exist_ok=True)
    os.makedirs(img_path,exist_ok=True)
    os.makedirs(script_path,exist_ok=True)

    google_api_key=os.getenv("GOOGLE_API_KEY")
    print("Generating Script...")
    video_title,script=genscript(google_api_key,channel_name,proj_prompt,proj_name,script_path)
    logger.info(f"Generated Script for {proj_name}")
    logger.info(f"Title: {video_title}")

    print("Generating Prompts...")
    prompts=genprompts(proj_prompt,n_prompts=images_per_video)
    logger.info(f"Generated {len(prompts)} prompts for {proj_name}")

    print("Generating Images...")
    genimages(prompts,img_path)
    logger.info(f"Generated {len(prompts)} images for {proj_name}")

    print("Performing media compilations...")
    logger.info(f"Compiling media for {proj_name}")

    success, message = create_audio_with_background(
        text=script,
        bg_music_path="backgrounds",
        output_path=f"{script_path}/script.mp3",
        bg_volume_reduction=20,
        fade_duration=2000,
        crossfade_duration=1000
    )
    if not success:
        logger.error(f"Failed to create audio for {proj_name}")
        logger.error(message)
        return
    print(message)
    logger.info(f"Created audio for {proj_name}")
    logger.info(message)

    success, message=create_video_with_transitions(
    base_folder=proj_path,
    output_path=f"{proj_path}/compiled_video.mp4",
    image_duration=8.0,
    transition_duration=3.0,
    min_zoom=1.0,
    max_zoom=1.2
    )
    if not success:
        logger.error(f"Failed to create video for {proj_name}")
        logger.error(message)
        return
    print(message)
    logger.info(f"Created video for {proj_name}")
    logger.info(message)

    success, message = add_intro_and_closure(
        final_video_path=f"{proj_path}/compiled_video.mp4",
        output_path=f"{proj_path}/final_video.mp4",
        intro_path=f"{meta_path}/intro.mp4",
        closure_path=f"{meta_path}/closure.mp4"
    )
    if not success:
        logger.error(f"Failed to add intro and closure for {proj_name}")
        logger.error(message)
        return
    print(message)
    logger.info(f"Added intro and closure for {proj_name}")

    logger.info(f"Completed media compilation for {proj_name} !")


if __name__=="__main__":
    main()



    







