from flask import Flask
import anthropic
import os

app = Flask(__name__)
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@app.route('/process', methods=['POST'])
def process_kurti():
    try:
        response = claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": """Create 60-word Instagram script for:
Product: Kurti
Sizes: S, M, L, XL
Prices: ₹299-₹599
Tone: Engaging"""
            }]
        )
        script = response.content[0].text
        return {"status": "success", "script": script}, 200
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)