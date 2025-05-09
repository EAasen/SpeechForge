from flask import Flask, request, jsonify
from transformers import pipeline
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Load the Dia-1.6B TTS model
print("Loading Dia-1.6B TTS model...")
tts_pipeline = pipeline("text-to-speech", model="nari-labs/Dia-1.6B")
print("Model loaded successfully.")

@app.route('/')
def hello_world():
    return "Hello, World!"

@app.route('/speak', methods=['POST'])
def speak():
    # Get text input from the request
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({"error": "Text input is required."}), 400

    # Generate speech audio
    audio = tts_pipeline(text)

    # Create output directory structure
    now = datetime.now()
    output_dir = f"/outputs/{now.year}/{now.month:02}/{now.day:02}"
    os.makedirs(output_dir, exist_ok=True)

    # Save audio file
    output_file = os.path.join(output_dir, "output.wav")
    with open(output_file, "wb") as f:
        f.write(audio["audio"])  # Assuming the pipeline returns a dict with "audio"

    # Return file path in response
    return jsonify({"file_path": output_file})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
