from flask import Flask, request, jsonify
from g4f.client import Client

app = Flask(__name__)
client = Client()

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get("text", "")
    
    prompt = (
        f"Translate the following text to Somali. "
        f"Crucially, any numbers found in the text MUST be written out as Somali words. "
        f"Provide only the translated text:\n\n{text}"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"translated_text": response.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
