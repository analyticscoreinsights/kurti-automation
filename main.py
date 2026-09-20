import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

def process_kurti():
    try:
        # Initialize the free Google client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Generate the script using the free Gemini model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="""Create 60-word Instagram script for:
Product: Kurti
Sizes: S, M, L, XL
Prices: ₹299-₹599
Tone: Engaging"""
        )
        
        print("--- SUCCESS! GENERATED INSTAGRAM SCRIPT ---")
        print(response.text)
        print("------------------------------------------")
        
    except Exception as e:
        print(f"ERROR OCCURRED: {str(e)}")
        exit(1)

if __name__ == "__main__":
    process_kurti()
