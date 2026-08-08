from llama_cpp import Llama

model_path = "C:/ORCA/models/phi-3-mini-4k-instruct-q4_K_M.gguf"

print("Loading model...")
llm = Llama(
    model_path=model_path,
    n_ctx=1024,
    n_threads=1,
    n_gpu_layers=0,
    verbose=False
)

# Phi-3 expects this format:
prompt = "<|user|>\nHello, world!<|end|>\n<|assistant|>\n"

print("Testing inference...")
response = llm.create_completion(
    prompt=prompt,
    max_tokens=50,
    temperature=0.7,
    stop=["<|end|>", "<|user|>"],
    echo=False
)

print("Full response:", response)
print("Text:", response['choices'][0]['text'])