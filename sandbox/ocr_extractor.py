import os
import tempfile
from PIL import Image
import pytesseract
import pdfplumber

# Set Tesseract path (adjust if installed elsewhere)
# Uncomment and set the correct path if needed:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(file_path):
    """Extract text from an image file using Tesseract OCR."""
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        return f"❌ OCR Error: {str(e)}"

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file using pdfplumber."""
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        return f"❌ PDF Error: {str(e)}"

def extract_text_from_file(file_path):
    """Extract text from any supported file type."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
        return extract_text_from_image(file_path)
    elif ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        return f"❌ Unsupported file type: {ext}"