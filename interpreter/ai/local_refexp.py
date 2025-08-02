import os
import multiprocessing
import torch

# necessary to allow running on both CPU and GPU
if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)

from vllm import LLM, SamplingParams
from transformers import Qwen2VLProcessor
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
        self.sampling_params = None

    def init_model(self):
        model_name = "ivelin/storycheck-jedi-3b-1080p-quantized"
        processor = Qwen2VLProcessor.from_pretrained(model_name)
        if os.getenv("STORYCHECK_FORCE_CPU") or not torch.cuda.is_available():
            os.environ["VLLM_IMAGE_DEVICE"] = "cpu"
        model = LLM(
            model=model_name,
            quantization="bitsandbytes" if torch.cuda.is_available() else None,
            max_model_len=4096,
            enforce_eager=True,
            gpu_memory_utilization=0.8
        )
        sampling_params = SamplingParams(temperature=0.01, max_tokens=1024, top_k=1, seed=0)
        return model, processor, sampling_params

    def process_refexp(self, image, refexp, shared_engine=None, return_annotated_image=False):
        if shared_engine:
            self.model, self.sampling_params, self.processor = shared_engine
        if not self.model or not self.processor:
            self.model, self.processor, self.sampling_params = self.init_model()

        # Resize image
        resized_height, resized_width = smart_resize(image.height, image.width)
        resized_image = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)

        # Prepare input with tool prompt (unified with standalone)
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
        chat_template = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        token_ids = self.processor.tokenizer(chat_template, return_tensors="pt")['input_ids'][0].tolist()
        inputs = [{
            "prompt_token_ids": token_ids,
            "multi_modal_data": {"image": resized_image}
        }]

        # Generate
        outputs = self.model.generate(inputs, sampling_params=self.sampling_params)
        text = outputs[0].outputs[0].text.strip()

        # Parse coordinates (unified with standalone)
        try:
            matches = re.findall(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL)
            coords = None
            for match in matches:
                action = json.loads(match)
                if action["name"] == "computer_use" and action["arguments"].get("action") == "left_click":
                    coords = action["arguments"].get("coordinate")
                    if coords:
                        x, y = coords
                        break
            if coords is None:
                raise ValueError("No valid left_click coordinate found")
            # Scale back to original size (fixed division)
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