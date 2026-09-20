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
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ─── CRUCIAL AUTOMATION SETTING ─────────────────────────────────────
# PASTE YOUR COPIED GOOGLE DRIVE FOLDER ID BETWEEN THE QUOTES BELOW:
FOLDER_ID = "1LI-M9XuMXmNRrS4pSuvCf3nlAgUO7Na6"
# ───────────────────────────────────────────────────────────────────

def get_latest_file_from_drive():
    try:
        creds = Credentials.from_service_account_info(eval(os.getenv("GOOGLE_CREDS")))
        service = build('drive', 'v3', credentials=creds)
        
        # Automatically search the folder for images, sorted by newest created date
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
        print(f"✨ Automatically found the newest image: {latest_file['name']} (ID: {latest_file['id']})")
        return latest_file['id'], latest_file['name']
    except Exception as e:
        print(f"Error scanning Google Drive folder: {str(e)}")
        return None, None

def download_from_drive(file_id):
    if not file_id:
        return None
    try:
        creds = Credentials.from_service_account_info(eval(os.getenv("GOOGLE_CREDS")))
        service = build('drive', 'v3', credentials=creds)
        
        request = service.files().get_media(fileId=file_id)
        file_data = io.BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download Progress: {int(status.progress() * 100)}%")
            
        print("--- SUCCESS! DOWNLOADED LATEST MEDIA FILE FROM DRIVE ---")
        return file_data.getvalue()
    except Exception as e:
        print(f"Google Drive Download Error: {str(e)}")
        return None

def generate_script():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents="""Create 60-word Instagram script for:
Product: Kurti
Sizes: S, M, L, XL
Prices: ₹299-₹599
Tone: Engaging"""
            )
            return response.text
        except Exception as e:
            if "503" in str(e) and attempt < max_retries - 1:
                print(f"Model busy. Retrying in 5 seconds... ({attempt + 1}/{max_retries})")
                time.sleep(5)
                continue
            print(f"AI Generation Error: {str(e)}")
            raise e

if __name__ == "__main__":
    # 1. Automatically hunt for the newest photo in your shared folder
    file_id, file_name = get_latest_file_from_drive()
    
    if file_id:
        # 2. Download the found photo dynamically
        media_bytes = download_from_drive(file_id)
        
        # 3. Build the marketing script
        generated_text = generate_script()
        print("Generated Script Output:\n", generated_text)
        
        # 4. Insert data into your Supabase grid tracking system
        try:
            response = supabase.table("kurti_jobs").insert({
                "product_name": f"Kurti - {file_name}",  # Saves the actual image filename!
                "sizes": "S, M, L, XL",
                "prices": "₹299-₹599",
                "status": "completed",
                "video_url": generated_text
            }).execute()
            print("--- SUCCESS! CACHED TRANSACTION ENTRY TO DATABASE ---")
        except Exception as e:
            print(f"Database Save Error: {str(e)}")
    else:
        print("Automation halted: No source image could be pulled.")
