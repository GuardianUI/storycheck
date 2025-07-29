# File Path: tests/test_vlm_inference.py
import time
import torch
import logging
from PIL import Image
from vllm import LLM, SamplingParams
from transformers import Qwen2_5_VLProcessor
import vllm
import re
import json
from huggingface_hub import hf_hub_download

import math
from typing import Tuple

def round_by_factor(number: int, factor: int) -> int:
    """Return the closest integer to number that is divisible by factor"""
    return round(number / factor) * factor

def floor_by_factor(number: int, factor: int) -> int:
    """Return the largest integer less than or equal to number that is divisible by factor"""
    return math.floor(number / factor) * factor

def smart_resize(height, width, factor=28, min_pixels=56 * 56, max_pixels=14 * 14 * 4 * 1280, max_long_side=8192):
    """Resize image while ensuring dimensions meet specific constraints."""
    if height < 2 or width < 2:
        raise ValueError(f"height:{height} or width:{width} must be larger than factor:{factor}")
    if max(height, width) / min(height, width) > 200:
        raise ValueError(f"absolute aspect ratio must be smaller than 100, got {height} / {width}")

    if max(height, width) > max_long_side:
        beta = max(height, width) / max_long_side
        height, width = int(height / beta), int(width / beta)
    h_bar = round_by_factor(height, factor)
    w_bar = round_by_factor(width, factor)
    if h_bar * w_bar > max_pixels:
        beta = math.sqrt((height * width) / max_pixels)
        h_bar = floor_by_factor(height / beta, factor)
        w_bar = floor_by_factor(width / beta, factor)
    return h_bar, w_bar

# Model config
#model_name = "xlangai/Jedi-3B-1080p"
model_name = "ivelin/storycheck-jedi-3b-1080p-quantized"  # Use hosted repo ID
processor = Qwen2_5_VLProcessor.from_pretrained(model_name)
max_pixels = 2700 * 28 * 28

# Test parameters
image_path = "tests/uniswap_screenshot.png"
expressions = ["click the connect button", "click 'Select Token' dropdown", "click on ETH dropdown"]

# Persistent vLLM engine (load once)
llm = None
sampling_params = None
FN_CALL_TEMPLATE = """You are a highly capable assistant designed to interact with a computer interface using tools. Always respond with structured tool calls when appropriate.
 
# Tools
You may call one or more functions to assist with the user query.
You are provided with function signatures within <tools></tools> XML tags:
<tools>
{tool_descs}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{{"name": <function-name>, "arguments": <args-json-object>}}
</tool_call>"""

def computer_use_function():
    return {
        "type": "function",
        "function": {
            "name": "computer_use",
            "description": "Use a mouse and keyboard to interact with a computer.",
            "parameters": {
                "properties": {
                    "action": {"type": "string", "enum": ["mouse_move", "left_click"]},
                    "coordinate": {"type": "array", "items": {"type": "number"}}
                },
                "required": ["action", "coordinate"]
            }
        }
    }

print(f"vLLM version: {vllm.__version__}")

def init_vllm_engine(batch_size=4):
    global llm, sampling_params
    if llm is None:
        try:
            llm = LLM(
                model=model_name,
                quantization="bitsandbytes" if torch.cuda.is_available() else None,
                max_model_len=4096,
                enforce_eager=True,
                max_num_seqs=batch_size
            )
            sampling_params = SamplingParams(temperature=0.01, max_tokens=1024, top_k=1, seed=0)
            print("vLLM engine initialized.")
        except Exception as e:
            raise Exception(f"vLLM initialization failed: {e}")
    return llm, sampling_params

def parse_coordinates(response):
    match = re.search(r"<tool_call>(.*?)</tool_call>", response, re.DOTALL)
    if not match:
        raise ValueError("No <tool_call> block found in response.")
    try:
        action = json.loads(match.group(1))
        action_name = action["name"]
        action_type = action["arguments"]["action"]
        if action_name == "computer_use" and action_type in ("mouse_move", "left_click"):
            return action["arguments"]["coordinate"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing coordinates: {e}\nResponse: {response}")
    return None

def benchmark_inference(image_path, expressions, batch_size=4, debug=False):
    start_time = time.time()
    
    # Adjust for debug mode
    if debug:
        batch_size = 1
        print("Debug mode: Processing single step with verbose logging.")
    
    # Initialize persistent engine
    llm, sampling_params = init_vllm_engine(batch_size)
    
    # Load and resize image
    image = Image.open(image_path).convert("RGB")
    resized_height, resized_width = smart_resize(image.height, image.width, factor=28, min_pixels=56 * 56, max_pixels=14 * 14 * 4 * 1280, max_long_side=8192)
    resized_image = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
    
    if isinstance(expressions, str):
        expressions = [expressions]
    images = [resized_image] * len(expressions)
    tool_descs = "\n".join([json.dumps(computer_use_function(), ensure_ascii=False)])
    messages = [
        (
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": FN_CALL_TEMPLATE.format(tool_descs=tool_descs)}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": img},
                    {"type": "text", "text": exp}
                ]
            }
        )
        for exp, img in zip(expressions, images)
    ]
    
    # Format inputs
    chat_templates = [processor.apply_chat_template(m[0], tokenize=False, add_generation_prompt=True) + processor.apply_chat_template(m[1], tokenize=False, add_generation_prompt=True) for m in messages]
    if debug:
        print(f"Input templates: {chat_templates}")
        logging.basicConfig(level=logging.DEBUG)
    
    # Prepare batched inputs for multimodal generate
    inputs = [{"prompt": template} for template in chat_templates]
    if debug:
        logging.debug(f"Generation inputs: {inputs}")
        logging.debug(f"Sampling params: {sampling_params}")
    outputs = llm.generate(inputs, sampling_params=sampling_params)
    results = []
    for o in outputs:
        text = o.outputs[0].text.strip()
        if debug:
            print(f"Raw model output: {text}")
            logging.debug(f"Full output object: {o}")
            logging.debug(f"Output text length: {len(text)}")
        coords = parse_coordinates(text)
        if coords:
            x, y = coords
            x = x * image.width / resized_width
            y = y * image.height / resized_height
            results.append(f"{int(x)},{int(y)}")
        else:
            results.append("invalid")
    
    end_time = time.time()
    print(f"Inference time for {len(expressions)} prompts: {end_time - start_time:.2f}s")
    print(f"Throughput: {len(expressions) / (end_time - start_time):.2f} inferences/sec")
    print(f"Predicted coords (first result): {results[0]}")
    if debug and results:
        print(f"Full results: {results}")
    return results

def test_vlm_inference():
    # Test the inference function with a dummy image and expression
    results = benchmark_inference(image_path, expressions, batch_size=len(expressions), debug=True)
    for res in results:
        assert res != "invalid", "Invalid coordinate output"
        coords = res.split(",")
        assert len(coords) == 2, "Expected x,y coordinates"
        x, y = map(int, coords)
        assert 0 <= x <= image.width and 0 <= y <= image.height, "Coordinates must be in image bounds"

if __name__ == "__main__":
    test_vlm_inference()