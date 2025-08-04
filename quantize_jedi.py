# File: quantize_jedi.py
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
import torch
from huggingface_hub import HfApi, login, create_repo, repo_info
import os
from dotenv import load_dotenv
import hashlib
from torch.ao.quantization import default_dynamic_qconfig

# Load environment variables from .env.local (preferred) or .env
dotenv_path = '.env.local' if os.path.exists('.env.local') else '.env'
load_dotenv(dotenv_path=dotenv_path)

# Setup
model_name = "xlangai/Jedi-3B-1080p"
gpu_quantized_model_dir = "model/quantized-gpu"  # Save under model/quantized-gpu/
cpu_quantized_model_dir = "model/quantized-cpu"  # Save under model/quantized-cpu/
gpu_repo_id = "ivelin/storycheck-jedi-3b-1080p-quantized"  # Existing GPU repo
cpu_repo_id = "ivelin/storycheck-jedi-3b-1080p-cpu-int8"  # New CPU repo

# Get Hugging Face token from environment or raise error
hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
if not hf_token:
    raise ValueError("HF_TOKEN environment variable not set. Please set it in .env.local or .env.")
login(hf_token)

# Check if repositories exist, create if they don't
for repo in [gpu_repo_id, cpu_repo_id]:
    try:
        _ = repo_info(repo_id=repo, repo_type="model")
        print(f"Repository {repo} already exists.")
    except Exception:
        create_repo(repo_id=repo, repo_type="model", exist_ok=True)
        print(f"Repository {repo} created.")

# GPU Quantization (existing 4-bit BitsAndBytes for GPU/vLLM)
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

# Helper function to compute SHA256 hash of model files in a directory
def compute_model_hash(model_dir):
    hash_algo = hashlib.sha256()
    for root, _, files in os.walk(model_dir):
        for file in sorted(files):  # Sort for consistent hashing
            if file.endswith(('.bin', '.json', '.txt')):  # Key model files
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    while chunk := f.read(4096):
                        hash_algo.update(chunk)
    return hash_algo.hexdigest()

# Helper function to check if upload is needed (compare local hash with remote)
def should_upload(api, repo_id, local_dir):
    local_hash = compute_model_hash(local_dir)
    hash_file = 'model_hash.txt'
    try:
        # Download remote hash if exists
        remote_hash_path = api.hf_hub_download(repo_id=repo_id, filename=hash_file, repo_type="model")
        with open(remote_hash_path, 'r') as f:
            remote_hash_value = f.read().strip()
        if local_hash == remote_hash_value:
            print(f"Skipping upload for {repo_id}: Local model matches remote (hash: {local_hash})")
            return False
    except Exception:
        # If hash file doesn't exist or download fails, proceed with upload
        pass
    # Save new hash locally for upload
    hash_path = os.path.join(local_dir, hash_file)
    with open(hash_path, 'w') as f:
        f.write(local_hash)
    return True

# Save quantized model locally under model/quantized-gpu/
os.makedirs(gpu_quantized_model_dir, exist_ok=True)
model.save_pretrained(gpu_quantized_model_dir)
processor.save_pretrained(gpu_quantized_model_dir)
print(f"GPU quantized model saved to {gpu_quantized_model_dir}")

# CPU Quantization (new INT8 dynamic for Transformers CPU fallback)
processor_cpu = AutoProcessor.from_pretrained(model_name)
model_cpu = AutoModelForImageTextToText.from_pretrained(
    model_name,
    low_cpu_mem_usage=True,
    use_cache=False
)

# Apply dynamic INT8 quantization (CPU-compatible)
model_cpu = torch.quantization.quantize_dynamic(
    model_cpu, {torch.nn.Linear: default_dynamic_qconfig}, dtype=torch.qint8
)

os.makedirs(cpu_quantized_model_dir, exist_ok=True)
model_cpu.save_pretrained(cpu_quantized_model_dir)
processor_cpu.save_pretrained(cpu_quantized_model_dir)
print(f"CPU quantized model saved to {cpu_quantized_model_dir}")

# Upload to Hugging Face (updates the repo each run)
api = HfApi()
if should_upload(api, gpu_repo_id, gpu_quantized_model_dir):
    api.upload_folder(
        folder_path=gpu_quantized_model_dir,
        repo_id=gpu_repo_id,
        repo_type="model",
        commit_message=f"Update GPU quantized model version {os.getenv('GITHUB_RUN_ID', 'local')}"
    )
    print("GPU quantized model uploaded to Hugging Face")
else:
    print("GPU upload skipped (no changes)")

# Upload CPU version
if should_upload(api, cpu_repo_id, cpu_quantized_model_dir):
    api.upload_folder(
        folder_path=cpu_quantized_model_dir,
        repo_id=cpu_repo_id,
        repo_type="model",
        commit_message=f"Update CPU quantized model version {os.getenv('GITHUB_RUN_ID', 'local')}"
    )
    print("CPU quantized model uploaded to Hugging Face")
else:
    print("CPU upload skipped (no changes)")