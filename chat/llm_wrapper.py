import sys
from pathlib import Path
from django.conf import settings
from llama_cpp import Llama

_llm_instance = None
_draft_instance = None

def load_llm():
    """Load the main Qwen model and the draft TinyLlama model."""
    global _llm_instance, _draft_instance

    if _llm_instance is None:
        model_path = settings.LLM_MODEL_PATH
        if not model_path.exists():
            print(f"❌ Model not found at {model_path}")
            return None

        print(f"🧠 Loading main LLM from {model_path}...")
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
        print("✅ Main LLM loaded.")

    # Load draft model (only for future use)
    if _draft_instance is None and hasattr(settings, 'DRAFT_MODEL_PATH'):
        draft_path = settings.DRAFT_MODEL_PATH
        if draft_path.exists():
            print(f"🧠 Loading draft model from {draft_path}...")
            _draft_instance = Llama(
                model_path=str(draft_path),
                n_ctx=512,
                n_batch=128,
                n_threads=1,
                n_gpu_layers=0,
                use_mmap=True,
                use_mlock=False,
                verbose=False
            )
            print("✅ Draft model loaded.")
        else:
            print(f"⚠️ Draft model not found at {draft_path}. Skipping.")
    else:
        if hasattr(settings, 'DRAFT_MODEL_PATH') and not settings.DRAFT_MODEL_PATH.exists():
            print("⚠️ DRAFT_MODEL_PATH not set or file missing.")

    return _llm_instance

def get_llm():
    return _llm_instance

def get_draft():
    return _draft_instance

def generate_stream(prompt, max_tokens=512):
    llm = get_llm()
    if llm is None:
        yield "⚠️ LLM not loaded."
        return

    # Draft is loaded but NOT passed to create_completion to avoid errors
    formatted_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

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
                    delta = delta.replace('<|im_end|>', '').replace('<|im_start|>', '')
                    if delta:
                        yield delta
    except Exception as e:
        yield f"⚠️ LLM Error: {str(e)}"