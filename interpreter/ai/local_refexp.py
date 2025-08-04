import torch
from transformers import AutoModelForImageTextToText, Qwen2VLProcessor, BitsAndBytesConfig, AutoConfig
import os
from interpreter.ai.utils import smart_resize
from PIL import Image, ImageDraw
import re
import json
import logging

logger = logging.getLogger(__name__)

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

class LocalRefExp:
    def __init__(self):
        self.model = None
        self.processor = None

    def init_model(self):
        force_cpu = os.getenv("VLM_FORCE_CPU", "0") == "1"
        device = "cuda" if torch.cuda.is_available() and not force_cpu else "cpu"
        model_name = "ivelin/storycheck-jedi-3b-1080p-quantized" if device == "cuda" else "xlangai/Jedi-3B-1080p"

        # Quantization only for GPU, but check if model already has config to avoid warning
        quantization_config = None
        if device == "cuda":
            # Load config to check if quantization_config exists
            config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
            if not hasattr(config, "quantization_config") or config.quantization_config is None:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True
                )

        # Load processor and model (use Qwen2VLProcessor for Jedi compatibility)
        processor = Qwen2VLProcessor.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForImageTextToText.from_pretrained(
            model_name,
            quantization_config=quantization_config,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
            device_map="auto" if device == "cuda" else None
        )
        if device != "cuda":
            model = model.to(device)

        logger.info(f"Model loaded on {device} with {'quantization' if quantization_config else 'full precision'}.")

        return model, processor

    def process_refexp(self, image, refexp, shared_engine=None, return_annotated_image=False):
        if shared_engine:
            self.model, self.processor = shared_engine
        if not self.model or not self.processor:
            self.model, self.processor = self.init_model()

        # Resize image
        resized_height, resized_width = smart_resize(image.height, image.width)
        resized_image = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)

        # Prepare input with tool prompt
        tool_descs = json.dumps({
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
        })
        system_prompt = FN_CALL_TEMPLATE.format(tool_descs=tool_descs)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [{"type": "image"}, {"type": "text", "text": refexp}]}
        ]

        # Unified Transformers path
        chat_template = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=chat_template, images=resized_image, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=1024,
            temperature=0.01,
            top_k=1,
            do_sample=False  # Greedy decoding for consistent tool-call format
        )
        text = self.processor.decode(outputs[0], skip_special_tokens=True)
        logger.debug(f"Generated text: {text}")  # Log for debugging parsing issues

        # Extract only the assistant's response (after last 'assistant')
        if 'assistant' in text:
            text = text.split('assistant')[-1].strip()

        # Parse coordinates with improved regex to handle whitespace and newlines
        try:
            matches = re.findall(r"<tool_call>\s*(.+?)\s*</tool_call>", text, re.DOTALL)
            coords = None
            for match in matches:
                # Clean match: remove newlines and extra spaces
                clean_match = re.sub(r'\s+', ' ', match).strip()
                action = json.loads(clean_match)
                if action["name"] == "computer_use" and action["arguments"].get("action") == "left_click":
                    coords = action["arguments"].get("coordinate")
                    if coords:
                        x, y = coords
                        break
            if coords is None:
                raise ValueError("No valid left_click coordinate found")
            # Scale back to original size
            original_x = int(x * (image.width / resized_width))
            original_y = int(y * (image.height / resized_height))
            center_point = {'x': original_x, 'y': original_y}
        except Exception as e:
            logger.error(f"Parsing failed: {e}")
            center_point = {'x': 0, 'y': 0}  # Fallback

        if return_annotated_image:
            annotated_image = image.copy()
            draw = ImageDraw.Draw(annotated_image)
            radius = 10
            draw.ellipse([(original_x - radius, original_y - radius), (original_x + radius, original_y + radius)], fill="red")
            return annotated_image, center_point
        return None, center_point