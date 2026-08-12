from huggingface_hub import hf_hub_download

model_path = hf_hub_download(
    repo_id="QuantLLM/TinyLlama-1.1B-Chat-GGUF",
    filename="TinyLlama-1.1B-Chat-GGUF.Q4_K_M.gguf",
    local_dir="models"
)
print(f"✅ Downloaded to: {model_path}")