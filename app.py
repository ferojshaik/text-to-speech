import os
import re
from pathlib import Path
from flask import Flask, request, render_template, send_file
from pdfminer.high_level import extract_text
from gtts import gTTS

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
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
        pdf_file = request.files["pdf"]
        if not pdf_file:
            return "No file uploaded", 400

        pdf_path = Path(UPLOAD_FOLDER) / pdf_file.filename
        pdf_file.save(pdf_path)

        # Extract text
        text = extract_text(str(pdf_path)) or ""
        text = normalize_text(text)

        if not text.strip():
            return "No readable text in PDF", 400

        # Split & convert
        chunks = split_into_chunks(text)
        mp3_files = []

        for i, chunk in enumerate(chunks, start=1):
            tts = gTTS(chunk, lang="en")
            out_file = Path(OUTPUT_FOLDER) / f"out_part_{i}.mp3"
            tts.save(str(out_file))
            mp3_files.append(out_file)

        # Concatenate MP3s into one file
        final_file = Path(OUTPUT_FOLDER) / "final.mp3"
        with open(final_file, "wb") as f_out:
            for part in mp3_files:
                f_out.write(open(part, "rb").read())

        return send_file(final_file, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
