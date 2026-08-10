import sys
from pathlib import Path
from django.conf import settings
from llama_cpp import Llama

_llm_instance = None

def load_llm():
    """Load the GGUF model into memory (called once at startup)."""
    global _llm_instance
    if _llm_instance is None:
        model_path = settings.LLM_MODEL_PATH
        if not model_path.exists():
            print(f"❌ Model not found at {model_path}")
            print("   Please download the GGUF model to this location.")
            return None
        
        print(f"🧠 Loading LLM from {model_path}...")
        _llm_instance = Llama(
            model_path=str(model_path),
            n_ctx=settings.LLM_CONFIG['n_ctx'],
            n_batch=settings.LLM_CONFIG['n_batch'],
            n_threads=settings.LLM_CONFIG['n_threads'],
            n_gpu_layers=settings.LLM_CONFIG['n_gpu_layers'],
            use_mmap=True,
            use_mlock=False,
            verbose=False
        )
        print("✅ LLM loaded successfully.")
    return _llm_instance

def get_llm():
    """Return the loaded LLM instance (or None if not loaded)."""
    return _llm_instance

def generate_stream(prompt, max_tokens=512):
    llm = get_llm()
    if llm is None:
        yield "⚠️ LLM not loaded."
        return

    # ============================================================
    # QWEN 2.5 CHATML FORMAT (with space after assistant tag)
    # ============================================================
    formatted_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n "

    try:
        response = llm.create_completion(
            prompt=formatted_prompt,
            max_tokens=max_tokens,
            temperature=0.3,
            top_p=0.9,
            echo=False,
            stream=True,
            stop=["<|im_end|>", "<|im_start|>", "User:", "Human:"]
        )

        for chunk in response:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0].get('text', '')
                if delta:
                    # Remove special tokens but KEEP spaces
                    delta = delta.replace('<|im_end|>', '').replace('<|im_start|>', '')
                    # DO NOT strip spaces – preserve them
                    yield delta
    except Exception as e:
        yield f"⚠️ LLM Error: {str(e)}"
