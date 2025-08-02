import sys
import os
import pytest
import gc
import torch

# Add project root to sys.path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Optional: Fixture example if needed later (e.g., for shared setup)
@pytest.fixture(scope="session")
def project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def shared_local_refexp(shared_vlm_engine):
    from interpreter.ai.local_refexp import LocalRefExp
    local_refexp = LocalRefExp()
    yield local_refexp
    # Explicit cleanup to prevent hangs
    del local_refexp
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.empty_cache()

@pytest.fixture(scope="session")
def shared_vlm_engine():
    """Shared VLM engine for all tests to avoid multiple inits and OOM in suite."""
    from vllm import LLM, SamplingParams
    from transformers import Qwen2VLProcessor
    model_name = "ivelin/storycheck-jedi-3b-1080p-quantized"
    processor = Qwen2VLProcessor.from_pretrained(model_name)
    llm = LLM(
        model=model_name,
        quantization="bitsandbytes" if torch.cuda.is_available() else None,
        max_model_len=4096,
        enforce_eager=True,
        max_num_seqs=4,
        gpu_memory_utilization=0.8  # Lower to fit suite (fits ~18.8GiB req)
    )
    sampling_params = SamplingParams(temperature=0.01, max_tokens=1024, top_k=1, seed=0)
    yield llm, sampling_params, processor
    # Teardown
    del llm
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.empty_cache()