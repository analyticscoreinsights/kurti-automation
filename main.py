import os
from dotenv import load_dotenv
from google import genai
from supabase import create_client

# Automatically load environment metrics
load_dotenv()

# Initialize the Supabase Client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def generate_script():
    try:
        # Initialize the free modern Google client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Request content from the active free model
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
        print(f"AI Generation Error: {str(e)}")
        raise e

def save_to_db(script_text):
    try:
        # Insert structural keys directly into your Supabase Data Table
        response = supabase.table("kurti_jobs").insert({
            "product_name": "Kurti",
            "sizes": "S, M, L, XL",
            "prices": "₹299-₹599",
            "status": "completed",
            "video_url": script_text
        }).execute()
        print("--- SUCCESS! CAPTURED TO SUPABASE DATABASE ---")
        print(response)
    except Exception as e:
        print(f"Database Insertion Error: {str(e)}")
        raise e

if __name__ == "__main__":
    generated_text = generate_script()
    print("Generated Script:", generated_text)
    save_to_db(generated_text)
