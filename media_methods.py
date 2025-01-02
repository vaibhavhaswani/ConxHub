import os
import random
from gtts import gTTS
from pydub import AudioSegment
from typing import Optional, Tuple, List
import tempfile
import time
import subprocess
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, VideoClip,VideoFileClip, concatenate_videoclips
from pathlib import Path
import numpy as np

def check_ffmpeg_installed():
    """Check if ffmpeg is installed and accessible."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return True
    except FileNotFoundError:
        return False

def get_random_background_music(bg_music_path: str) -> str:
    """
    Get a random background music file from the directory.
    
    Args:
        bg_music_path (str): Path to background music directory
    
    Returns:
        str: Path to selected background music file
    """
    audio_files = [f for f in os.listdir(bg_music_path) 
                   if f.lower().endswith(('.mp3', '.wav', '.m4a'))]
    
    if not audio_files:
        raise Exception(f"No audio files found in {bg_music_path}")
    
    return random.choice(audio_files)

def create_audio_with_background(
    text: str,
    bg_music_path: str,
    output_path: str = "output.mp3",
    language: str = 'en',
    tld: str = 'com',
    slow: bool = False,
    bg_volume_reduction: int = 15,
    fade_duration: int = 3000,
    crossfade_duration: int = 1000  # Duration for crossfade between loops
) -> Tuple[bool, str]:
    """
    Creates an audio file combining text-to-speech with looped background music.
    
    Args:
        text (str): The text to convert to speech
        bg_music_path (str): Path to the directory containing background music files
        output_path (str): Path where the final audio should be saved
        language (str): Language code for TTS (default: 'en')
        tld (str): Top-level domain for accent (default: 'com' for US English)
        slow (bool): Whether to use slower speech (default: False)
        bg_volume_reduction (int): How many dB to reduce background music by (default: 15)
        fade_duration (int): Duration for fade effects in milliseconds (default: 3000)
        crossfade_duration (int): Duration for crossfade between loops (default: 1000)
    """
    if not check_ffmpeg_installed():
        return False, ("ffmpeg is not installed or not in PATH. Please install ffmpeg")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate TTS audio
            max_retries = 3
            for attempt in range(max_retries):
                temp_tts_path = os.path.join(temp_dir, f"temp_tts_{attempt}.mp3")
                try:
                    tts = gTTS(text=text, lang=language, tld=tld, slow=slow)
                    tts.save(temp_tts_path)
                    time.sleep(0.5)
                    tts_audio = AudioSegment.from_mp3(temp_tts_path)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to generate TTS after {max_retries} attempts: {str(e)}")
                    time.sleep(1)
            
            # Get TTS duration
            tts_duration = len(tts_audio)
            
            # Get random background music
            try:
                chosen_bg = get_random_background_music(bg_music_path)
                bg_path = os.path.join(bg_music_path, chosen_bg)
                background_music = AudioSegment.from_file(bg_path)
            except Exception as e:
                return False, f"Error loading background music: {str(e)}"
            
            # Adjust background music volume
            background_music = background_music - bg_volume_reduction
            
            # Create looped background music to match TTS length
            looped_background = AudioSegment.empty()
            remaining_duration = tts_duration + fade_duration
            bg_length = len(background_music)
            
            while len(looped_background) < remaining_duration:
                if len(looped_background) == 0:
                    looped_background = background_music
                else:
                    # Crossfade when adding new loop to avoid clicks/pops
                    looped_background = looped_background.append(
                        background_music,
                        crossfade=crossfade_duration
                    )
            
            # Trim to exact length needed
            looped_background = looped_background[:tts_duration + fade_duration]
            
            # Add fade effects
            looped_background = looped_background.fade_in(fade_duration).fade_out(fade_duration)
            
            # Combine audio
            combined_audio = looped_background.overlay(tts_audio)
            
            # Export final audio
            output_dir = os.path.dirname(os.path.abspath(output_path))
            os.makedirs(output_dir, exist_ok=True)
            
            max_export_retries = 3
            for attempt in range(max_export_retries):
                try:
                    combined_audio.export(output_path, format="mp3")
                    break
                except Exception as e:
                    if attempt == max_export_retries - 1:
                        raise Exception(f"Failed to export audio after {max_export_retries} attempts: {str(e)}")
                    time.sleep(1)
            
            return True, (f"Successfully created audio file: {output_path}\n"
                         f"TTS Duration: {tts_duration/1000:.1f} seconds\n"
                         f"Background Track: {chosen_bg} (looped to match TTS duration)")
            
    except Exception as e:
        return False, f"Error creating audio: {str(e)}"
    

# def create_video_with_transitions(
#     base_folder: str,
#     output_path: str = "output_video.mp4",
#     image_duration: float = 3.0,
#     transition_duration: float = 1.0,
#     min_zoom: float = 1.0,
#     max_zoom: float = 1.2
# ) -> tuple[bool, str]:
#     """
#     Creates a video from images with transitions and audio narration.
    
#     Args:
#         base_folder (str): Path containing 'images' and 'script' subfolders
#         output_path (str): Path where the output video will be saved
#         image_duration (float): Duration each image should be shown (seconds)
#         transition_duration (float): Duration of transition effects (seconds)
#         min_zoom (float): Minimum zoom factor for the Ken Burns effect
#         max_zoom (float): Maximum zoom factor for the Ken Burns effect
    
#     Returns:
#         tuple[bool, str]: (Success status, Message)
#     """
#     try:
#         # Validate folder structure
#         image_folder = os.path.join(base_folder, "images")
#         script_folder = os.path.join(base_folder, "script")
        
#         if not os.path.exists(image_folder) or not os.path.exists(script_folder):
#             return False, "Missing required folders: 'images' and 'script'"
            
#         # Get audio file
#         audio_file = os.path.join(script_folder, "script.mp3")
#         if not os.path.exists(audio_file):
#             return False, "script.mp3 not found in script folder"
            
#         # Load audio and get duration
#         audio = AudioFileClip(audio_file)
#         total_duration = audio.duration
        
#         # Get list of images
#         image_files = [f for f in os.listdir(image_folder) 
#                       if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        
#         if not image_files:
#             return False, "No image files found in images folder"
            
#         # Calculate number of images needed
#         clips = []
#         current_time = 0
        
#         def create_transition_clip(img_path: str, start_time: float, duration: float) -> VideoClip:
#             """Creates a clip with Ken Burns effect and random transitions."""
#             img = ImageClip(img_path)
            
#             # Randomly choose zoom direction (in or out)
#             zoom_in = random.choice([True, False])
#             start_zoom = min_zoom if zoom_in else max_zoom
#             end_zoom = max_zoom if zoom_in else min_zoom
            
#             # Random starting position
#             w, h = img.size
#             start_x = random.uniform(0, w * (start_zoom - 1))
#             start_y = random.uniform(0, h * (start_zoom - 1))
#             end_x = random.uniform(0, w * (end_zoom - 1))
#             end_y = random.uniform(0, h * (end_zoom - 1))
            
#             def create_frame(t):
#                 progress = t / duration
#                 current_zoom = start_zoom + (end_zoom - start_zoom) * progress
#                 current_x = start_x + (end_x - start_x) * progress
#                 current_y = start_y + (end_y - start_y) * progress
                
#                 zoomed = img.resize(current_zoom)
#                 frame = zoomed.crop(
#                     x1=current_x,
#                     y1=current_y,
#                     x2=current_x + w,
#                     y2=current_y + h
#                 ).resize(img.size).get_frame(t)
                
#                 return np.array(frame)
            
#             return VideoClip(create_frame, duration=duration)
        
#         while current_time < total_duration:
#             # Randomly select an image
#             img_file = random.choice(image_files)
#             img_path = os.path.join(image_folder, img_file)
            
#             # Create clip with transition effect
#             clip_duration = min(image_duration, total_duration - current_time)
#             if clip_duration <= 0:
#                 break
                
#             clip = create_transition_clip(
#                 img_path,
#                 current_time,
#                 clip_duration + transition_duration
#             ).set_start(current_time)
            
#             clips.append(clip)
#             current_time += clip_duration
        
#         # Combine all clips
#         final_video = CompositeVideoClip(clips)
        
#         # Add audio
#         final_video = final_video.set_audio(audio)
        
#         # Write output file
#         final_video.write_videofile(
#             output_path,
#             fps=30,
#             codec='libx264',
#             audio_codec='aac'
#         )
        
#         # Clean up
#         final_video.close()
#         audio.close()
#         for clip in clips:
#             clip.close()
        
#         return True, f"Successfully created video: {output_path}"
        
#     except Exception as e:
#         return False, f"Error creating video: {str(e)}"
    
def create_video_with_transitions(
    base_folder: str,
    output_path: str = "output_video.mp4",
    image_duration: float = 3.0,
    transition_duration: float = 1.0,
    min_zoom: float = 1.0,
    max_zoom: float = 1.2
) -> tuple[bool, str]:
    """
    Creates a video from images with transitions and audio narration.
    Ensures each image is used at least once while maintaining randomness.
    
    Args:
        base_folder (str): Path containing 'images' and 'script' subfolders
        output_path (str): Path where the output video will be saved
        image_duration (float): Duration each image should be shown (seconds)
        transition_duration (float): Duration of transition effects (seconds)
        min_zoom (float): Minimum zoom factor for the Ken Burns effect
        max_zoom (float): Maximum zoom factor for the Ken Burns effect
    
    Returns:
        tuple[bool, str]: (Success status, Message)
    """
    try:
        # Validate folder structure
        image_folder = os.path.join(base_folder, "images")
        script_folder = os.path.join(base_folder, "script")
        
        if not os.path.exists(image_folder) or not os.path.exists(script_folder):
            return False, "Missing required folders: 'images' and 'script'"
            
        # Get audio file
        audio_file = os.path.join(script_folder, "script.mp3")
        if not os.path.exists(audio_file):
            return False, "script.mp3 not found in script folder"
            
        # Load audio and get duration
        audio = AudioFileClip(audio_file)
        total_duration = audio.duration
        
        # Get list of images
        image_files = [f for f in os.listdir(image_folder) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        
        if not image_files:
            return False, "No image files found in images folder"
            
        # Create a pool of unused images and a list for used images
        unused_images = image_files.copy()
        used_images = []
        
        def create_transition_clip(img_path: str, start_time: float, duration: float) -> VideoClip:
            """Creates a clip with Ken Burns effect and random transitions."""
            img = ImageClip(img_path)
            
            # Randomly choose zoom direction (in or out)
            zoom_in = random.choice([True, False])
            start_zoom = min_zoom if zoom_in else max_zoom
            end_zoom = max_zoom if zoom_in else min_zoom
            
            # Random starting position
            w, h = img.size
            start_x = random.uniform(0, w * (start_zoom - 1))
            start_y = random.uniform(0, h * (start_zoom - 1))
            end_x = random.uniform(0, w * (end_zoom - 1))
            end_y = random.uniform(0, h * (end_zoom - 1))
            
            def create_frame(t):
                progress = t / duration
                current_zoom = start_zoom + (end_zoom - start_zoom) * progress
                current_x = start_x + (end_x - start_x) * progress
                current_y = start_y + (end_y - start_y) * progress
                
                zoomed = img.resize(current_zoom)
                frame = zoomed.crop(
                    x1=current_x,
                    y1=current_y,
                    x2=current_x + w,
                    y2=current_y + h
                ).resize(img.size).get_frame(t)
                
                return np.array(frame)
            
            return VideoClip(create_frame, duration=duration)
        
        clips = []
        current_time = 0
        
        while current_time < total_duration:
            # If unused_images is empty but we still need more images,
            # refill it with all images except the last used one
            if not unused_images:
                unused_images = [img for img in image_files if img != used_images[-1]]
                random.shuffle(unused_images)
            
            # Select an image from unused_images
            img_file = unused_images.pop()
            used_images.append(img_file)
            
            img_path = os.path.join(image_folder, img_file)
            
            # Create clip with transition effect
            clip_duration = min(image_duration, total_duration - current_time)
            if clip_duration <= 0:
                break
                
            clip = create_transition_clip(
                img_path,
                current_time,
                clip_duration + transition_duration
            ).set_start(current_time)
            
            clips.append(clip)
            current_time += clip_duration
        
        # Combine all clips
        final_video = CompositeVideoClip(clips)
        
        # Add audio
        final_video = final_video.set_audio(audio)
        
        # Write output file
        final_video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac'
        )
        
        # Clean up
        final_video.close()
        audio.close()
        for clip in clips:
            clip.close()
        
        return True, f"Successfully created video: {output_path}"
        
    except Exception as e:
        return False, f"Error creating video: {str(e)}"

def add_intro_and_closure(
    final_video_path: str,
    output_path: str,
    intro_path: str,
    closure_path: str
) -> tuple[bool, str]:
    """
    Adds intro and closure videos to the final video with optimized output.

    Args:
        final_video_path (str): Path to the final video file.
        output_path (str): Path where the output video with intro and closure will be saved.
        intro_path (str): Path to the intro video file.
        closure_path (str): Path to the closure video file.

    Returns:
        tuple[bool, str]: (Success status, Message)
    """
    try:
        # Load intro, final, and closure videos
        intro_clip = VideoFileClip(intro_path)
        final_clip = VideoFileClip(final_video_path)
        closure_clip = VideoFileClip(closure_path)

        # Match resolution of all clips to the final clip's resolution
        target_resolution = final_clip.size  # Width, Height
        intro_clip = intro_clip.resize(newsize=target_resolution)
        closure_clip = closure_clip.resize(newsize=target_resolution)

        # Concatenate the videos
        final_video = concatenate_videoclips([intro_clip, final_clip, closure_clip])

        # Write output file with optimized settings
        final_video.write_videofile(
            output_path,
            fps=30,
            codec="libx264",          # Efficient codec for MP4
            audio_codec="aac",        # Audio codec
            preset="slow",            # Preset for better compression
            bitrate="2M",             # Limit bitrate to prevent excessive file size
            threads=4                 # Utilize multiple threads
        )

        # Clean up
        intro_clip.close()
        final_clip.close()
        closure_clip.close()
        final_video.close()

        return True, f"Successfully created video with intro and closure: {output_path}"

    except Exception as e:
        return False, f"Error adding intro and closure: {str(e)}"
