#### Downloading few background samples
import requests
import random
import os
from tqdm import tqdm

def get_soft_background_music(api_key, savepath, nsamples=10):
    """Downloads free soft background music samples from Freesound API."""

    API_URL = "https://freesound.org/apiv2/search/text/"

    headers = {"Authorization": f"Token {api_key}"}
    downloaded_count = 0
    page = 1
    
    while downloaded_count < nsamples:
        params = {
            "query": "soft background",
            "fields": "id,name,previews,license,description,duration",
            "filter": "tag:music type:wav",
            "page_size": 100,  # Increased page size to have more options
            "page": page,
        }
        
        # Search for soft background music
        response = requests.get(API_URL, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return
            
        data = response.json()
        if not data["results"]:
            print("No more results found. Could not download requested number of samples.")
            return
            
        # Create a list of valid tracks (duration >= 60 seconds)
        valid_tracks = [track for track in data["results"] if track["duration"] >= 60]
        
        # Shuffle the valid tracks to ensure random selection
        random.shuffle(valid_tracks)
        
        for track in tqdm(valid_tracks, desc=f"Downloading Background Samples ({downloaded_count}/{nsamples})"):
            if downloaded_count >= nsamples:
                break
                
            track_name = track["name"]
            track_duration = track["duration"]
            preview_url = track["previews"]["preview-hq-mp3"]
            
            # Download the music track
            music_response = requests.get(preview_url)
            if music_response.status_code == 200:
                # Save the file
                file_name = f"{savepath}/bg_{int(track_duration)}.mp3".replace(" ", "_")
                with open(file_name, "wb") as file:
                    file.write(music_response.content)
                downloaded_count += 1
            else:
                print(f"Error downloading track: {track_name}")
                
        # If we haven't found enough tracks, move to the next page
        if downloaded_count < nsamples:
            page += 1
            
    print(f"\nSuccessfully downloaded {downloaded_count} background music samples.")



## Example usage
pth="../backgrounds"
os.makedirs(pth,exist_ok=True)
API_KEY=os.environ["FREESOUND_API_KEY"]
get_soft_background_music(API_KEY,pth,nsamples=10)