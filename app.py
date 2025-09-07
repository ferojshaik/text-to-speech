
import os
import re
import io
from gtts import gTTS
from pdfminer.high_level import extract_text
from flask import Flask, request, render_template, send_file
app = Flask(__name__)
# Use environment variable for data path, fallback to local for development
DATA_DIR = os.environ.get("RENDER_DATA_DIR", ".")
UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(DATA_DIR, "outputs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def normalize_text(txt: str) -> str:
    txt = txt.replace("\r", "\n")
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()

def split_into_chunks(text: str, max_chars: int = 1500):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, buf = [], []
    for s in sentences:
        if not s: continue
        tentative = " ".join(buf + [s])
        if len(tentative) <= max_chars:
            buf.append(s)
        else:
            chunks.append(" ".join(buf))
            buf = [s]
    if buf: chunks.append(" ".join(buf))
    return chunks

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pdf_file = request.files.get("pdf")
        if not pdf_file or not pdf_file.filename:
            return "No file uploaded", 400

        # Extract text directly from the uploaded file's stream
        text = extract_text(pdf_file.stream) or ""
        text = normalize_text(text)

        if not text.strip():
            return "No readable text in PDF", 400

        # Split & convert to in-memory MP3 objects
        chunks = split_into_chunks(text)
        mp3_chunks = []

        for chunk in chunks:
            tts = gTTS(chunk, lang="en")
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            mp3_chunks.append(mp3_fp)

        # Concatenate MP3 chunks in memory
        final_mp3 = io.BytesIO()
        for mp3_fp in mp3_chunks:
            final_mp3.write(mp3_fp.read())
        final_mp3.seek(0)

        return send_file(
            final_mp3,
            as_attachment=True,
            download_name="output.mp3",
            mimetype="audio/mpeg"
        )

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
