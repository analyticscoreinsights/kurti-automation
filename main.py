import io
import os
import time
from dotenv import load_dotenv
from google import genai
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from supabase import create_client

# Load environment configuration variables
load_dotenv()

# Initialize the active Supabase Client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# ─── 100% AUTOMATION SETTING ────────────────────────────────────────
# PASTE YOUR COPIED GOOGLE DRIVE FOLDER ID BETWEEN THE QUOTES BELOW:
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
    
    # Using the latest live 2026 models (3.8 is primary, 3.6 is stable backup)
    models_to_try = ['gemini-3.8-flash', 'gemini-3.6-flash']
    
    for model_name in models_to_try:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempting to generate script using model: {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=f"Create an engaging 60-word Instagram script for a product promotion: {product}, Sizes: {sizes}, Prices: {prices}. Include relevant hooks, emojis, and call to actions."
                )
                return response.text
            except Exception as e:
                if "503" in str(e) and attempt < max_retries - 1:
                    print(f"Model {model_name} busy. Retrying in 5 seconds... ({attempt + 1}/{max_retries})")
                    time.sleep(5)
                    continue
                print(f"Failed with {model_name}: {str(e)}")
                break # Break inner loop to try the fallback model
                
    raise RuntimeError("All available free Google AI models are currently overloaded. Please try running again in a few minutes.")

if __name__ == "__main__":
    file_id, file_name = get_latest_file_from_drive()
    
    if file_id:
        photo = fetch_photo_from_drive(file_id)
        script = generate_script("Kurti", "S, M, L, XL", "₹299-₹599")
        print("Generated Script Output:\n", script)
        
        try:
            response = supabase.table("kurti_jobs").insert({
                "product_name": f"Kurti - {file_name}",
                "sizes": "S, M, L, XL",
                "prices": "₹299-₹599",
                "status": "completed",
                "video_url": script
            }).execute()
            print("--- SUCCESS! TRANSACTION COMMITTED TO SUPABASE DATABASE ---")
        except Exception as e:
            print(f"Database Save Error: {str(e)}")
    else:
        print("Automation halted: No source image could be pulled from the shared folder.")
