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

def download_from_drive(file_id):
    try:
        # Load your cloud service account tokens securely
        creds = Credentials.from_service_account_info(
            eval(os.getenv("GOOGLE_CREDS"))
        )
        service = build('drive', 'v3', credentials=creds)
        
        # Pull streaming file binary blocks out from Google Drive
        request = service.files().get_media(fileId=file_id)
        file_data = io.BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download Progress: {int(status.progress() * 100)}%")
            
        print("--- SUCCESS! DOWNLOADED MEDIA FILE FROM GOOGLE DRIVE ---")
        return file_data.getvalue()
    except Exception as e:
        print(f"Google Drive Download Error (Ensure file ID is real and shared with service account): {str(e)}")
        return None

def generate_script():
    # Initialize the modern free Google AI client
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Retry loop to push past temporary free tier high-demand spikes
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
                print(f"Model busy (Spike in demand). Retrying in 5 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(5)
                continue
            print(f"AI Generation Error: {str(e)}")
            raise e

if __name__ == "__main__":
    # Test file ID placeholder for your automation pipeline
    SAMPLE_FILE_ID = "1abc123XYZ_placeholder_id"
    
    # 1. Download asset file
    media_bytes = download_from_drive(SAMPLE_FILE_ID)
    
    # 2. Build the marketing script
    generated_text = generate_script()
    print("Generated Script Output:\n", generated_text)
    
    # 3. Insert metadata records straight into your data tracking matrix
    try:
        response = supabase.table("kurti_jobs").insert({
            "product_name": "Kurti",
            "sizes": "S, M, L, XL",
            "prices": "₹299-₹599",
            "status": "completed",
            "video_url": generated_text
        }).execute()
        print("--- SUCCESS! CACHED TRANSACTION ENTRY TO DATABASE ---")
    except Exception as e:
        print(f"Database Save Error: {str(e)}")
