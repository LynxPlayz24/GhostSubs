from flask import Flask, jsonify, send_file
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

TRANSLATION_FILE = "translation.txt"

@app.route("/")
def index():
    return send_file("overlay.html")

@app.route("/subtitle")
def get_subtitle():
    try:
        if os.path.exists(TRANSLATION_FILE):
            with open(TRANSLATION_FILE, "r", encoding="utf-8") as f:
                text = f.read().strip()
            if text:
                return jsonify({"text": text})
    except Exception:
        pass
    return jsonify({"text": "Waiting for subtitles..."})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)