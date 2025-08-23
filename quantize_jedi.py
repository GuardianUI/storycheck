# File: quantize_jedi.py
import torch
from transformers import AutoModelForImageTextToText, Qwen2VLProcessor, BitsAndBytesConfig
from huggingface_hub import HfApi, upload_folder, hf_hub_download
from optimum.quanto import quantize, qint8, freeze  # Use qint8 for revert
import os
import logging
import hashlib
from safetensors.torch import save_file
import json
from optimum.quanto import quantization_map
# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_model_hash(model):
    """Compute a hash of the model's state dict for comparison."""
    state_dict = model.state_dict()
    hash_obj = hashlib.sha256()
    for key in sorted(state_dict.keys()):
        hash_obj.update(key.encode())
        param = state_dict[key]
        if hasattr(param, 'dequantize'):
            param = param.dequantize()
        if isinstance(param, torch.Tensor):
            param = param.detach()
            hash_obj.update(param.cpu().numpy().tobytes())
        elif isinstance(param, tuple):
            for item in param:
                if hasattr(item, 'dequantize'):
                    item = item.dequantize()
                if isinstance(item, torch.Tensor):
                    item = item.detach()
                    hash_obj.update(item.cpu().numpy().tobytes())
                else:
                    hash_obj.update(str(item).encode())
    return hash_obj.hexdigest()

def quantize_and_save():
    model_name = "xlangai/Jedi-3B-1080p"
    gpu_output_dir = "model/quantized"
    cpu_output_dir = "model/quantized_cpu"
    gpu_repo_id = "ivelin/storycheck-jedi-3b-1080p-quantized"
    cpu_repo_id = "ivelin/storycheck-jedi-3b-1080p-cpu-quantized"
    # Ensure output directories exist
    os.makedirs(gpu_output_dir, exist_ok=True)
    os.makedirs(cpu_output_dir, exist_ok=True)
    # Load processor
    logger.info(f"Loading processor from {model_name}")
    processor = Qwen2VLProcessor.from_pretrained(model_name, trust_remote_code=True)
    
    def process_quantization(output_dir, repo_id, is_gpu=True):
        torch.manual_seed(0)  # For determinism
        if is_gpu:
            logger.info("Starting GPU quantization")
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True
            )
            model = AutoModelForImageTextToText.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                device_map="auto"
            )
            # Save as before for GPU
            model.save_pretrained(output_dir)
        else:
            logger.info("Starting CPU quantization")
            model = AutoModelForImageTextToText.from_pretrained(
                model_name,
                low_cpu_mem_usage=True,
                trust_remote_code=True
            ).to("cpu")
            quantize(model, weights=qint8, activations=qint8)  # Revert to ~3GB setup
            freeze(model)  # Pack weights to reduce size
            # Low-level save for compatibility on load without wrappers
            state_dict = model.state_dict()
            save_file(state_dict, os.path.join(output_dir, 'model.safetensors'))
            qmap = quantization_map(model)
            with open(os.path.join(output_dir, 'quantization_map.json'), 'w') as f:
                json.dump(qmap, f)
        
        processor.save_pretrained(output_dir) # Save processor to ensure video_preprocessor.json
        model_hash = compute_model_hash(model)
        hash_file = os.path.join(output_dir, 'state_dict_hash.txt')
        
        local_matches = False
        if os.path.exists(hash_file):
            with open(hash_file, 'r') as f:
                local_hash = f.read().strip()
            if local_hash == model_hash:
                local_matches = True
                logger.info(f"Local quantized model in {output_dir} matches hash, skipping save")
        
        if not local_matches:
            logger.info(f"Saving quantized model to {output_dir}")
            with open(hash_file, 'w') as f:
                f.write(model_hash)
        
        # Log size always, from existing files
        total_size_mb = sum(os.path.getsize(os.path.join(output_dir, f)) for f in os.listdir(output_dir) if f.endswith('.safetensors')) / (1024 * 1024)
        logger.info(f"Size of quantized model in {output_dir}: {total_size_mb:.2f} MB")
        
        # Ensure repo exists
        api = HfApi()
        try:
            api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
            logger.info(f"Ensured repo {repo_id} exists")
        except Exception as e:
            logger.warning(f"Failed to create repo {repo_id}: {str(e)}. Proceeding with upload attempt.")
        
        # Check Hub
        upload_needed = True
        try:
            hub_hash_path = hf_hub_download(repo_id=repo_id, filename='state_dict_hash.txt', repo_type="model")
            with open(hub_hash_path, 'r') as f:
                hub_hash = f.read().strip()
            if hub_hash == model_hash:
                logger.info(f"Quantized model matches Hub hash for {repo_id}, skipping upload")
                upload_needed = False
            else:
                logger.info(f"Hash mismatch with Hub for {repo_id}, will upload")
        except Exception as e:
            logger.info(f"Hub hash check failed for {repo_id} (likely no hash file or other error: {str(e)}), will upload")
        
        if upload_needed:
            logger.info(f"Uploading quantized model to {repo_id}")
            upload_folder(
                repo_id=repo_id,
                folder_path=output_dir,
                commit_message="Update quantized model",
                repo_type="model"
            )
        logger.info(f"Model hash for {output_dir}: {model_hash}")
    
    # Process GPU
    process_quantization(gpu_output_dir, gpu_repo_id, is_gpu=True)
    # Process CPU
    process_quantization(cpu_output_dir, cpu_repo_id, is_gpu=False)

if __name__ == "__main__":
    quantize_and_save()