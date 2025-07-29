# File Path: tests/test_vlm_inference.py
import time
import torch
from PIL import Image
from vllm import LLM, SamplingParams
from transformers import AutoProcessor  # Only for chat template formatting

# Model config
#model_name = "xlangai/Jedi-3B-1080p"
model_name = "ivelin/storycheck-jedi-3b-1080p-quantized"  # Use hosted repo ID (files are in root)
processor = AutoProcessor.from_pretrained(model_name)

# Test parameters
image_path = "tests/uniswap_screenshot.png"
expression = "click the connect button"


# Persistent vLLM engine (load once)
llm = None
sampling_params = None

def init_vllm_engine(batch_size=4):
    global llm, sampling_params
    if llm is None:
        try:
            llm = LLM(
                model=model_name,
                quantization="bitsandbytes" if torch.cuda.is_available() else None,
                max_model_len=512,
                enforce_eager=True,
                max_num_seqs=batch_size
            )
            sampling_params = SamplingParams(temperature=0.0, max_tokens=20)
            print("vLLM engine initialized.")
        except Exception as e:
            raise Exception(f"vLLM initialization failed: {e}")
    return llm, sampling_params

def benchmark_inference(image_path, expression, batch_size=4, debug=False):
    start_time = time.time()
    
    # Adjust for debug mode
    if debug:
        batch_size = 1
        print("Debug mode: Processing single step with verbose logging.")
    
    # Initialize persistent engine
    llm, sampling_params = init_vllm_engine(batch_size)
    
    # Simulate multi-step batch
    images = [Image.open(image_path)] * batch_size
    prompts = [f"Refer to the UI element: {expression}. Output center coordinates as x,y in [0-1] range."] * batch_size
    
    # Format inputs (Jedi demo style)
    chat_templates = [
        processor.apply_chat_template([
            {"role": "user", "content": [{"type": "text", "text": p}, {"type": "image"}]}
        ])
        for p in prompts
    ]
    if debug:
        print(f"Input templates: {chat_templates[:1]}")
    
    # Run inference
    outputs = llm.generate(chat_templates, sampling_params=sampling_params)
    results = [o.outputs[0].text.strip() for o in outputs]  # e.g., ["0.42,0.67", ...]
    
    end_time = time.time()
    print(f"Inference time for {batch_size} steps: {end_time - start_time:.2f}s")
    print(f"Throughput: {batch_size / (end_time - start_time):.2f} inferences/sec")
    print(f"Predicted coords (first result): {results[0]}")
    if debug:
        print(f"Full results: {results}")
    return results

def test_vlm_inference():
    # Test the inference function with a dummy image and expression
    results = benchmark_inference(image_path, expression, batch_size=1, debug=True)
    assert len(results) == 1, "Expected one result"
    coords = results[0].split(",")
    assert len(coords) == 2, "Expected x,y coordinates"
    x, y = float(coords[0]), float(coords[1])
    assert 0 <= x <= 1 and 0 <= y <= 1, "Coordinates must be in [0-1] range"

if __name__ == "__main__":
    # Test with placeholder screenshot, debug mode for single step
    benchmark_inference(image_path, expression, batch_size=4, debug=True)