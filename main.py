import os
from dotenv import load_dotenv
from flask import Flask
from google import genai

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize the free Google client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.route('/process', methods=['POST'])
def process_kurti():
    try:
        # Generate the script using the updated free Gemini model
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents="""Create 60-word Instagram script for:
Product: Kurti
Sizes: S, M, L, XL
Prices: ₹299-₹599
Tone: Engaging"""
        )
        
        return {"status": "success", "script": response.text}, 200
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
