# File: quantize_jedi.py
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
import torch
from huggingface_hub import HfApi, login, create_repo, repo_info
import os
from dotenv import load_dotenv

# Load environment variables from .env.local (preferred) or .env
dotenv_path = '.env.local' if os.path.exists('.env.local') else '.env'
load_dotenv(dotenv_path=dotenv_path)

# Setup
model_name = "xlangai/Jedi-3B-1080p"
quantized_model_dir = "model/quantized"  # Save under model/quantized/
repo_id = "ivelin/storycheck-jedi-3b-1080p-quantized"  # Replace with your username/repo

# Get Hugging Face token from environment or raise error
hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
if not hf_token:
    raise ValueError("HF_TOKEN environment variable not set. Please set it in .env.local or .env.")
login(hf_token)

# Check if repository exists, create if it doesn't
try:
    _ = repo_info(repo_id=repo_id, repo_type="model")
    print(f"Repository {repo_id} already exists.")
except Exception:
    create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
    print(f"Repository {repo_id} created.")

# Quantization config (4-bit with bitsandbytes, compatible with VLMs and vLLM)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True
)

# Load and quantize the model
processor = AutoProcessor.from_pretrained(model_name)
model = AutoModelForImageTextToText.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    low_cpu_mem_usage=True,
    use_cache=False
)

# Save quantized model locally under model/quantized/
os.makedirs(quantized_model_dir, exist_ok=True)
model.save_pretrained(quantized_model_dir)
processor.save_pretrained(quantized_model_dir)
print(f"Quantized model saved to {quantized_model_dir}")

# Upload to Hugging Face (updates the repo each run)
api = HfApi()
api.upload_folder(
    folder_path=quantized_model_dir,
    repo_id=repo_id,
    repo_type="model",
    commit_message=f"Update quantized model version {os.getenv('GITHUB_RUN_ID', 'local')}"
)
print("Quantized model uploaded to Hugging Face")