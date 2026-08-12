import subprocess
import json
import tempfile
import os
from pathlib import Path

def analyze_image(image_path, prompt="Describe this image in detail."):
    """
    Run Moondream in a subprocess to analyze an image.
    Returns the description text.
    """
    # We'll write a temporary Python script that loads Moondream and processes the image.
    script = f"""
import sys
sys.path.insert(0, r'C:/ORCA/sandbox')
from PIL import Image
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "vikhyatk/moondream2"
revision = "2025-01-09"
model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, revision=revision)
tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)

image = Image.open(r"{image_path}")
enc_image = model.encode_image(image)
answer = model.answer_question(enc_image, "{prompt}", tokenizer)
print(answer)
"""
    # Run the script in a subprocess with a timeout
    try:
        result = subprocess.run(
            ['python', '-c', script],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout.strip()
        if not output:
            output = result.stderr.strip() or "❌ Vision analysis failed."
        return output
    except subprocess.TimeoutExpired:
        return "⚠️ Vision analysis timed out."
    except Exception as e:
        return f"⚠️ Vision error: {str(e)}"