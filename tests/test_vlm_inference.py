import time
import torch
import logging
from PIL import Image, ImageDraw
from vllm import LLM, SamplingParams
from transformers import Qwen2_5_VLProcessor
import vllm
import re
import json
from huggingface_hub import hf_hub_download
import math
from typing import Tuple
import numpy as np
import os

# Configure logging with console and file output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('results/test_vlm_inference.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(file_handler)

# Counter for llm.generate calls
generate_call_count = 0

def round_by_factor(number: int, factor: int) -> int:
    """Return the closest integer to number that is divisible by factor"""
    return round(number / factor) * factor

def floor_by_factor(number: int, factor: int) -> int:
    """Return the largest integer less than or equal to number that is divisible by factor"""
    return math.floor(number / factor) * factor

def smart_resize(height, width, factor=28, min_pixels=56 * 56, max_pixels=14 * 14 * 4 * 1280, max_long_side=8192, **kwargs):
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

def annotate_image(image: Image.Image, coordinates: list, output_path: str):
    """Annotate image with red circles at given coordinates."""
    draw = ImageDraw.Draw(image)
    radius = 10  # Size of the marker
    for coord in coordinates:
        x, y = coord
        logger.debug(f"Annotating coordinate on original image: ({x}, {y})")
        # Draw a red circle at the coordinate
        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=None,
            outline="red",
            width=2
        )
    image.save(output_path)
    logger.info(f"Annotated image saved to {output_path}")

# Model config
model_name = "ivelin/storycheck-jedi-3b-1080p-quantized"  # Use hosted repo ID
cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
processor = None

# Test parameters
image_path = "tests/uniswap_screenshot.png"
expressions = [
    "click the connect button",
    "click 'Select Token' dropdown",
    "click on ETH dropdown",
    "open Trade menu",
    "Click on arrow below 'Scroll to learn'",
    "Click on Get started button",
    "Click on Sell text field",
    "Click on Buy text field",
    "type weth in search field"
]

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
                    "action": {"type": "string", "enum": ["mouse_move", "left_click", "type", "key"]},
                    "coordinate": {"type": "array", "items": {"type": "number"}},
                    "text": {"type": "string"},
                    "keys": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["action"],
                "additionalProperties": False
            }
        }
    }

logger.info(f"vLLM version: {vllm.__version__}")

def init_vllm_engine(batch_size=4):
    global llm, sampling_params, processor
    if llm is None or processor is None:
        try:
            # Load processor with local cache
            model_cache_path = os.path.join(cache_dir, f"models--{model_name.replace('/', '--')}")
            source = 'cache' if os.path.exists(model_cache_path) else 'Hugging Face'
            processor = Qwen2_5_VLProcessor.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                local_files_only=os.path.exists(model_cache_path),
                force_download=False
            )
            logger.debug(f"Processor loaded from {source}")
            
            # Load vLLM model with local cache
            llm = LLM(
                model=model_name,
                quantization="bitsandbytes" if torch.cuda.is_available() else None,
                max_model_len=4096,
                enforce_eager=True,
                max_num_seqs=batch_size,
                download_dir=cache_dir
            )
            sampling_params = SamplingParams(temperature=0.01, max_tokens=1024, top_k=1, seed=0)
            logger.debug(f"vLLM engine initialized from {source}")
        except Exception as e:
            logger.error(f"vLLM or processor initialization failed: {e}")
            raise
    return llm, sampling_params

def parse_coordinates(response):
    logger.debug(f"Parsing response: {response}")
    matches = re.findall(r"<tool_call>(.*?)</tool_call>", response, re.DOTALL)
    if not matches:
        # Fallback: assume direct "x,y" output if tool call fails
        match_xy = re.search(r"(\d+\.?\d*),\s*(\d+\.?\d*)", response)
        if match_xy:
            logger.debug(f"Fallback: Found direct coordinates: {match_xy.group(0)}")
            return [float(match_xy.group(1)), float(match_xy.group(2))]
        logger.error("No <tool_call> or direct coordinates found in response.")
        raise ValueError("No <tool_call> or direct coordinates found in response.")
    
    for match in matches:
        try:
            action = json.loads(match)
            action_name = action["name"]
            action_type = action["arguments"].get("action")
            if action_name == "computer_use" and action_type == "left_click":
                coords = action["arguments"].get("coordinate")
                if coords:
                    logger.debug(f"Raw coordinates (resized image): {coords}")
                    return coords
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing tool call: {e}\nTool call: {match}")
            continue
    logger.error("No valid left_click tool call found in response.")
    return None

def benchmark_inference(image_path, expressions, batch_size=4, debug=False):
    global generate_call_count
    start_time = time.time()
    
    # Adjust for debug mode
    if debug:
        batch_size = 1
        logger.debug("Debug mode: Processing single step with verbose logging.")
    
    # Initialize persistent engine
    llm, sampling_params = init_vllm_engine(batch_size)
    
    # Load and resize image
    image = Image.open(image_path).convert("RGB")
    resized_height, resized_width = smart_resize(image.height, image.width, factor=28, min_pixels=56 * 56, max_pixels=14 * 14 * 4 * 1280, max_long_side=8192)
    resized_image = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
    scale_x = image.width / resized_width
    scale_y = image.height / resized_height
    logger.debug(f"Image loaded: original {image.width}x{image.height}, resized to {resized_width}x{resized_height} (scaling factors: x={scale_x:.3f}, y={scale_y:.3f})")
    
    if isinstance(expressions, str):
        expressions = [expressions]
    images = [resized_image] * len(expressions)
    tool_descs = "\n".join([json.dumps(computer_use_function(), ensure_ascii=False)])
    messages_list = [
        [
            {"role": "system", "content": [{"type": "text", "text": FN_CALL_TEMPLATE.format(tool_descs=tool_descs)}]},
            {"role": "user", "content": [{"type": "image"}, {"type": "text", "text": exp}]}
        ]
        for exp in expressions
    ]
    
    # Format and tokenize inputs
    inputs = []
    for messages, img in zip(messages_list, images):
        chat_template = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        token_ids = processor.tokenizer(chat_template, return_tensors="pt")['input_ids'][0].tolist()
        inputs.append({
            "prompt_token_ids": token_ids,
            "multi_modal_data": {"image": img}
        })
        logger.debug(f"Input prompt for expression '{messages[-1]['content'][-1]['text']}': {chat_template}")
    
    # Run batched inference
    try:
        generate_call_count += 1
        logger.debug(f"Starting llm.generate call #{generate_call_count}")
        outputs = llm.generate(inputs, sampling_params=sampling_params)
        logger.debug(f"Completed llm.generate call #{generate_call_count}")
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        raise
    
    results = []
    valid_coordinates = []
    for o, exp in zip(outputs, expressions):
        text = o.outputs[0].text.strip()
        logger.debug(f"Raw model output for '{exp}': {text}")
        try:
            coords = parse_coordinates(text)
            if coords:
                x, y = coords
                scaled_x = x * image.width / resized_width
                scaled_y = y * image.height / resized_height
                logger.debug(f"Scaled coordinates for '{exp}' (original image {image.width}x{image.height}): ({int(scaled_x)}, {int(scaled_y)})")
                results.append(f"{int(scaled_x)},{int(scaled_y)}")
                valid_coordinates.append((int(scaled_x), int(scaled_y)))
            else:
                results.append("invalid")
        except Exception as e:
            logger.error(f"Failed to process output for '{exp}': {e}")
            results.append("invalid")
    
    # Annotate image with valid coordinates
    if valid_coordinates:
        annotate_image(image.copy(), valid_coordinates, "results/annotated_image.png")
    
    end_time = time.time()
    logger.debug(f"Inference time for {len(expressions)} prompts: {end_time - start_time:.2f}s")
    logger.debug(f"Throughput: {len(expressions) / (end_time - start_time):.2f} inferences/sec")
    logger.debug(f"Predicted coords (first result): {results[0]}")
    if debug and results:
        logger.debug(f"Full results: {results}")
    return results, image

def test_vlm_inference():
    # Expected coordinates for each expression (scaled to original image 1126x950)
    expected_coords = [
        (1075, 119),  # click the connect button
        (704, 586),   # click 'Select Token' dropdown
        (719, 451),   # click on ETH dropdown
        (104, 125),   # open Trade menu
        (559, 884),   # Click on arrow below 'Scroll to learn'
        (559, 681),   # Click on Get started button
        (499, 451),   # Click on Sell text field
        (555, 587),   # Click on Buy text field
        (575, 125)    # type weth in search field
    ]
    tolerance = 10  # Pixel tolerance for coordinate variations
    
    # Test the inference function with a dummy image and expression
    results, image = benchmark_inference(image_path, expressions, batch_size=len(expressions), debug=True)
    for res, exp, expected in zip(results, expressions, expected_coords):
        if res == "invalid":
            logger.error(f"Invalid coordinate output for expression: {exp}")
            assert res != "invalid", f"Invalid coordinate output for '{exp}'"
        coords = res.split(",")
        assert len(coords) == 2, f"Expected x,y coordinates for '{exp}'"
        x, y = map(int, coords)
        assert 0 <= x <= image.width and 0 <= y <= image.height, f"Coordinates ({x}, {y}) for '{exp}' must be in image bounds ({image.width}, {image.height})"
        # Check if predicted coordinates are within tolerance
        expected_x, expected_y = expected
        distance = np.sqrt((x - expected_x)**2 + (y - expected_y)**2)
        logger.debug(f"Coordinate check for '{exp}': predicted ({x}, {y}), expected ({expected_x}, {expected_y}), distance {distance:.2f} pixels")
        assert distance <= tolerance, f"Coordinates ({x}, {y}) for '{exp}' deviate too far from expected ({expected_x}, {expected_y}) by {distance:.2f} pixels"

if __name__ == "__main__":
    test_vlm_inference()