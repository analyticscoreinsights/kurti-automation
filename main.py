import io
import os
import time
import requests
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

# Initialize the active Supabase Client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# ─── 100% AUTOMATION SETTING ────────────────────────────────────────
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
            print("No images found in the Google Drive folder.")
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

def generate_script(product, sizes, prices):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Active Gemini models
    models_to_try = ['gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-3.6-flash']
    
    for model_name in models_to_try:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempting to generate script using model: {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=f"Create an engaging 60-word Instagram script for a product promotion: {product}, Sizes: {sizes}, Prices: {prices}. Include relevant hooks and call to actions. Keep it clean without emojis for better voice reading."
                )
                return response.text
            except Exception as e:
                if "503" in str(e) and attempt < max_retries - 1:
                    print(f"Model {model_name} busy. Retrying in 5 seconds... ({attempt + 1}/{max_retries})")
                    time.sleep(5)
                    continue
                print(f"Failed with {model_name}: {str(e)}")
                break
                
    raise RuntimeError("All available free Google AI models are currently overloaded.")

def text_to_speech_free(text, output_filename="/tmp/audio.mp3"):
    try:
        print("Generating free text-to-speech audio narration...")
        tts = gTTS(text=text, lang='en', tld='co.in')
        tts.save(output_filename)
        print("--- SUCCESS! GENERATED FREE AUDIO CAPTION FILE ---")
        return output_filename
    except Exception as e:
        print(f"Text-to-Speech Error: {str(e)}")
        return None

def create_video_free(photo_bytes, audio_path, output_video_path="/tmp/output.mp4"):
    try:
        print("Assembling video from image frame and voice file...")
        photo_path = "/tmp/photo.jpg"
        with open(photo_path, "wb") as f:
            f.write(photo_bytes)
            
        audio_clip = AudioFileClip(audio_path)
        video_duration = audio_clip.duration
        
        # MoviePy v2 syntax
        image_clip = ImageClip(photo_path).with_duration(video_duration)
        video_clip = image_clip.with_audio(audio_clip)
        
        # Removed unsupported 'verbose' parameter
        video_clip.write_videofile(
            output_video_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac", 
            logger=None
        )
        
        audio_clip.close()
        video_clip.close()
        
        print("--- SUCCESS! VIDEO RENDERED COMPLETELY ---")
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
            
        print(f"Uploading video container to Instagram Account ID: {account_id}")
        
        # Step 1: Create media container
        url = f"https://graph.facebook.com/v19.0/{account_id}/media"
        payload = {
            "media_type": "REELS",
            "caption": caption,
            "access_token": token
        }
        
        with open(video_path, 'rb') as video_file:
            files = {'file': video_file}
            response = requests.post(url, data=payload, files=files)
            result = response.json()
            
        if "id" in result:
            creation_id = result["id"]
            print(f"Container created. Container ID: {creation_id}")
            
            # Step 2: Publish media container
            publish_url = f"https://graph.facebook.com/v19.0/{account_id}/media_publish"
            publish_payload = {
                "creation_id": creation_id,
                "access_token": token
            }
            
            publish_response = requests.post(publish_url, data=publish_payload)
            publish_result = publish_response.json()
            
            if "id" in publish_result:
                print(f"✅ SUCCESS! Posted to Instagram. Media ID: {publish_result['id']}")
                return publish_result['id']
            else:
                print(f"❌ Publishing failed: {publish_result}")
                return None
        else:
            print(f"❌ Container creation failed: {result}")
            return None
            
    except Exception as e:
        print(f"Instagram Upload Error: {str(e)}")
        return None

if __name__ == "__main__":
    file_id, file_name = get_latest_file_from_drive()
    
    if file_id:
        photo_bytes = fetch_photo_from_drive(file_id)
        script = generate_script("Kurti", "S, M, L, XL", "₹299-₹599")
        print("Generated Script Output:\n", script)
        
        if photo_bytes and script:
            # 1. Generate Voice Audio File
            audio_file = text_to_speech_free(script)
            
            if audio_file:
                # 2. Render Video
                video_file = create_video_free(photo_bytes, audio_file)
                
                # 3. Post to Instagram & Save Track Record to Supabase
                if video_file:
                    caption = f"{script}\n\n#Kurti #Fashion #WomenClothing #Shopping #IndianFashion"
                    ig_post_id = upload_to_instagram(video_file, caption)
                    
                    try:
                        response = supabase.table("kurti_jobs").insert({
                            "product_name": f"Kurti - {file_name}",
                            "sizes": "S, M, L, XL",
                            "prices": "₹299-₹599",
                            "status": "completed",
                            "video_url": f"https://instagram.com/p/{ig_post_id}" if ig_post_id else "video_generated_free_tier"
                        }).execute()
                        print("--- SUCCESS! TRANSACTION COMMITTED TO SUPABASE DATABASE ---")
                    except Exception as e:
                        print(f"Database Save Error: {str(e)}")
    else:
        print("Automation halted: No source image could be pulled from the shared folder.")
