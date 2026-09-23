import io
import os
import time
import math
import requests
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from supabase import create_client
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip

# Load environment configuration variables
load_dotenv()

# Initialize active Supabase Client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# ─── DIRECT HARDCODED DRIVE FOLDER ID ───────────────────────────────
FOLDER_ID = "1LI-M9XuMXmNRrS4pSuvCf3nlAgUO7Na6"
# ───────────────────────────────────────────────────────────────────

def get_latest_file_from_drive():
    try:
        creds = Credentials.from_service_account_info(eval(os.getenv("GOOGLE_CREDS")))
        service = build('drive', 'v3', credentials=creds)
        
        query = f"'{FOLDER_ID}' in parents and mimeType contains 'image/' and trashed = false"
        results = service.files().list(
            q=query,
            orderBy="createdTime desc",
            pageSize=1,
            fields="files(id, name)"
        ).execute()
        
        files = results.get('files', [])
        if not files:
            print("No images found in Google Drive folder.")
            return None, None
            
        latest_file = files[0]
        print(f"✨ Automatically detected the newest image: {latest_file['name']} (ID: {latest_file['id']})")
        return latest_file['id'], latest_file['name']
    except Exception as e:
        print(f"Error scanning Google Drive folder: {str(e)}")
        return None, None

def fetch_photo_from_drive(file_id):
    if not file_id:
        return None
    try:
        creds = Credentials.from_service_account_info(eval(os.getenv("GOOGLE_CREDS")))
        drive = build('drive', 'v3', credentials=creds)
        
        request = drive.files().get_media(fileId=file_id)
        file_data = io.BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download Progress: {int(status.progress() * 100)}%")
            
        print("--- SUCCESS! DOWNLOADED PHOTO FROM GOOGLE DRIVE ---")
        return file_data.getvalue()
    except Exception as e:
        print(f"Google Drive Download Error: {str(e)}")
        return None

def generate_storytelling_script():
    """Generates engaging, story-led Hinglish scripts with high interactive CTA."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    models_to_try = [ 'gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-3.6-flash','gemini-2.5-flash', 'gemini-2.0-flash']
    
    prompt = """
    Write a 45-word story-based Instagram Reel voiceover in HINDI (written in Hinglish using English letters).
    
    Structure:
    1. Hook / Story Scenario: Start with a relatable daily fashion struggle (e.g., "Jab sudden plan bane aur samajh na aaye kya pehne...", or "Last minute outfit panic? We've got you!").
    2. Solution: Introduce this elegant Kurti as the perfect effortless solution for daily elegance, office, or small functions.
    3. Details: Mention premium breathable fabric, sizes S to XL, and prices starting from just ₹299 to ₹599.
    4. Strong User Interaction CTA: End with a direct question or prompt for engagement (e.g., "Aapko konsa color pasand hai? Comment 'KURTI' aur hum aapko buy link bhej denge!").
    
    Strict rules:
    - DO NOT use emojis, special characters, or hashtags in the text so speech output is seamless.
    """
    
    for model_name in models_to_try:
        max_retries = 10
        for attempt in range(max_retries):
            try:
                print(f"Generating story script using model: {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                if "503" in str(e) and attempt < max_retries - 1:
                    print(f"Model {model_name} busy. Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(20)
                    continue
                print(f"Failed with {model_name}: {str(e)}")
                break
                
    return "Jab bhi urgent outing ya office ke liye ready hona ho, yeh designer Kurti aapki pehli choice banegi. Lightweight, stylish aur super comfortable. Sizes S se XL tak, starting at ₹299. Comment 'KURTI' right now for direct buying link!"

def text_to_speech_elevenlabs(text, voice_id="1XNFRxE3WBB7iI0jnm7p", output_filename="/tmp/audio.mp3"):
    """Generates high-fidelity Indian Hinglish speech using ElevenLabs."""
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("ELEVENLABS_API_KEY missing. Using fallback gTTS...")
            return text_to_speech_free(text, output_filename)

        print("Generating high-quality Indian storytelling voice narration with ElevenLabs...")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.35,
                "similarity_boost": 0.85
            }
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            with open(output_filename, "wb") as f:
                f.write(response.content)
            print("--- SUCCESS! GENERATED ELEVENLABS INDIAN VOICE AUDIO ---")
            return output_filename
        else:
            print(f"ElevenLabs API Error: {response.status_code} - {response.text}. Falling back to gTTS...")
            return text_to_speech_free(text, output_filename)
            
    except Exception as e:
        print(f"ElevenLabs Error: {str(e)}. Falling back to gTTS...")
        return text_to_speech_free(text, output_filename)

def text_to_speech_free(text, output_filename="/tmp/audio.mp3"):
    try:
        print("Generating fallback Hindi gTTS audio narration...")
        tts = gTTS(text=text, lang='hi', tld='co.in')
        tts.save(output_filename)
        return output_filename
    except Exception as e:
        print(f"Text-to-Speech Error: {str(e)}")
        return None

def apply_cinematic_hd_zoom(clip, target_w=1080, target_h=1920, zoom_ratio=0.04):
    """Resizes to 1080x1920 Vertical HD and applies high-quality motion zoom."""
    def zoom_effect(get_frame, t):
        raw_frame = get_frame(t)
        img = Image.fromarray(raw_frame)
        
        current_w = math.ceil(target_w * (1 + (zoom_ratio * t)))
        current_h = math.ceil(target_h * (1 + (zoom_ratio * t)))
        
        current_w += current_w % 2
        current_h += current_h % 2
        
        img_resized = img.resize((current_w, current_h), Image.Resampling.LANCZOS)
        left = math.ceil((current_w - target_w) / 2)
        top = math.ceil((current_h - target_h) / 2)
        img_cropped = img_resized.crop((left, top, target_w + left, target_h + top))
        
        return np.array(img_cropped)

    return clip.transform(zoom_effect)

def create_high_quality_video(photo_bytes, audio_path, output_video_path="/tmp/output.mp4"):
    try:
        print("Processing High Definition 1080p Video with Ken Burns animation...")
        photo_path = "/tmp/photo.jpg"
        
        # Pre-process image to strict 1080x1920 (9:16 aspect ratio)
        img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
        img_resized = img.resize((1080, 1920), Image.Resampling.LANCZOS)
        img_resized.save(photo_path, quality=95)
            
        audio_clip = AudioFileClip(audio_path)
        video_duration = audio_clip.duration
        
        image_clip = ImageClip(photo_path).with_duration(video_duration)
        cinematic_clip = apply_cinematic_hd_zoom(image_clip, target_w=1080, target_h=1920)
        video_clip = cinematic_clip.with_audio(audio_clip)
        
        # Render high-bitrate full HD video
        video_clip.write_videofile(
            output_video_path, 
            fps=30, 
            codec="libx264", 
            audio_codec="aac", 
            bitrate="8000k",
            preset="medium",
            logger=None
        )
        
        audio_clip.close()
        video_clip.close()
        
        print("--- SUCCESS! HIGH QUALITY 1080P VIDEO RENDERED ---")
        return output_video_path
    except Exception as e:
        print(f"Video Generation Error: {str(e)}")
        return None

def upload_to_instagram(video_path, caption):
    try:
        token = os.getenv("INSTAGRAM_TOKEN")
        account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
        
        if not token or not account_id:
            print("Instagram credentials missing. Skipping upload.")
            return None
        
        print("Uploading video to cloud storage...")
        file_name = f"kurti_{int(time.time())}.mp4"
        
        with open(video_path, 'rb') as f:
            supabase.storage.from_('Videos').upload(
                path=file_name,
                file=f,
                file_options={"content-type": "video/mp4"}
            )
        
        video_url = supabase.storage.from_('Videos').get_public_url(file_name)
        print(f"Video hosted at: {video_url}")
        
        print(f"Creating Reel Container for Instagram Account: {account_id}")
        url = f"https://graph.facebook.com/v19.0/{account_id}/media"
        payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": token
        }
        
        response = requests.post(url, data=payload)
        result = response.json()
        
        if "id" in result:
            creation_id = result["id"]
            print(f"Container created successfully. Container ID: {creation_id}")
            
            # ─── POLLING CONTAINER STATUS ───────────────────────────────────
            print("Checking Instagram video processing status...")
            status_url = f"https://graph.facebook.com/v19.0/{creation_id}?fields=status_code&access_token={token}"
            
            max_attempts = 15
            for attempt in range(max_attempts):
                status_res = requests.get(status_url).json()
                status_code = status_res.get("status_code")
                
                print(f"Processing Status ({attempt + 1}/{max_attempts}): {status_code}")
                
                if status_code == "FINISHED":
                    print("✅ Instagram finished video processing!")
                    break
                elif status_code == "ERROR":
                    print(f"❌ Instagram video processing failed: {status_res}")
                    return None
                    
                time.sleep(30)  # Wait 10 seconds between status checks
            else:
                print("❌ Processing timed out on Instagram servers.")
                return None
            # ────────────────────────────────────────────────────────────────

            publish_url = f"https://graph.facebook.com/v19.0/{account_id}/media_publish"
            publish_payload = {
                "creation_id": creation_id,
                "access_token": token
            }
            
            publish_response = requests.post(publish_url, data=publish_payload)
            publish_result = publish_response.json()
            
            if "id" in publish_result:
                print(f"✅ SUCCESS! Posted to Instagram. Published Media ID: {publish_result['id']}")
                return publish_result['id']
            else:
                print(f"❌ Publishing Failed: {publish_result}")
                return None
        else:
            print(f"❌ Container Creation Failed: {result}")
            return None
            
    except Exception as e:
        print(f"Error during Instagram upload process: {str(e)}")
        return None
if __name__ == "__main__":
    file_id, file_name = get_latest_file_from_drive()
    
    if file_id:
        photo_bytes = fetch_photo_from_drive(file_id)
        script = generate_storytelling_script()
        print("Generated Storytelling Script Output:\n", script)
        
        if photo_bytes and script:
            audio_file = text_to_speech_elevenlabs(script)
            
            if audio_file:
                video_file = create_high_quality_video(photo_bytes, audio_file)
                
                if video_file:
                    caption = f"{script}\n\n👇 Comment 'KURTI' below to get the purchase link directly in your DM!\n\n#Kurti #Fashion #EthnicWear #DailyWear #OOTD #IndianFashion"
                    ig_post_id = upload_to_instagram(video_file, caption)
                    
                    try:
                        supabase.table("kurti_jobs").insert({
                            "product_name": "Premium Storytelling Kurti Collection",
                            "sizes": "S, M, L, XL",
                            "prices": "₹299-₹599",
                            "status": "completed",
                            "video_url": f"https://instagram.com/p/{ig_post_id}" if ig_post_id else "video_generated_hd"
                        }).execute()
                        print("--- SUCCESS! TRANSACTION COMMITTED TO SUPABASE DATABASE ---")
                    except Exception as e:
                        print(f"Database Save Error: {str(e)}")
    else:
        print("Automation halted: No source image could be pulled from the shared folder.")
