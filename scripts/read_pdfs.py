from pypdf import PdfReader
import os

def extract_text(filename):
    print(f"\n{'='*20}\nReading {filename}\n{'='*20}")
    try:
        reader = PdfReader(filename)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        print(text)
    except Exception as e:
        print(f"Error reading {filename}: {e}")

files = [
    "Entrega 1.pdf"
]

for f in files:
    if os.path.exists(f):
        extract_text(f)
    else:
        print(f"File not found: {f}")
