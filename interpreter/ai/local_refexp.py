# File: interpreter/ai/local_refexp.py
from loguru import logger
from PIL import Image, ImageDraw
from vllm import LLM, SamplingParams
from transformers import AutoProcessor
import torch
import html
from . import RefExp

class LocalRefExp(RefExp):
    """
    Wrapper around VLM Transformer fine tuned for RefExp task
    """

    model = None
    previous_revision = None
    processor = None
    device = None
    loaded_revision = None

    async def __init__(self,
                       model_revision: str = 'main'):
        if not model_revision:
            model_revision = 'main'
        logger.debug(
            "model checkpoint revision: {model_revision}",
            model_revision=model_revision)
        self.load_model(model_revision)

    def load_model(self, pretrained_revision: str = 'main'):
        pretrained_repo_name = 'xlangai/Jedi-3B-1080p'
        # revision can be git commit hash, branch or tag
        # use 'main' for latest revision
        logger.debug(
            "Loading model from: {pretrained_repo_name}, rev: {pretrained_revision}",
            pretrained_repo_name=pretrained_repo_name,
            pretrained_revision=pretrained_revision
        )
        if self.processor is None or self.loaded_revision is None \
                or self.loaded_revision != pretrained_revision:
            self.loaded_revision = pretrained_revision
            self.processor = AutoProcessor.from_pretrained(
                pretrained_repo_name, revision=pretrained_revision)
            self.model = LLM(
                model=pretrained_repo_name,
                quantization="awq" if torch.cuda.is_available() else None,
                max_model_len=512,
                enforce_eager=True,
                max_num_seqs=4  # Default batch size; adjust for debug
            )
            self.sampling_params = SamplingParams(temperature=0.0, max_tokens=20)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.debug('vLLM engine loaded')

    def process_refexp(self, image: Image,
                       prompt: str,
                       return_annotated_image: bool = True, debug=False):
        logger.debug(
            "(image, prompt): {image}, {prompt}", image=image, prompt=prompt)

        # Adjust batch size for debug mode
        batch_size = 1 if debug else 4

        # Initialize persistent vLLM engine
        llm, sampling_params = init_vllm_engine(batch_size)

        # Trim prompt
        prompt = prompt[:80].lower()

        # Prepare prompt (Jedi demo style)
        chat_template = self.processor.apply_chat_template([
            {"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image"}]}
        ])

        if debug:
            logger.debug(f"Input template: {chat_template}")

        # Run inference
        outputs = llm.generate([chat_template], sampling_params=sampling_params)
        result = outputs[0].outputs[0].text.strip()  # e.g., "0.42,0.67"

        # Parse coords
        try:
            x, y = map(float, result.split(","))
            if not (0 <= x <= 1 and 0 <= y <= 1):
                raise ValueError("Coordinates out of [0-1] range")
            center_point = {"x": x, "y": y}
        except Exception as e:
            logger.debug(f"Failed to parse coordinates '{result}': {e}")
            center_point = {"x": 0, "y": 0}

        logger.debug(f"Predicted center_point: {center_point}")

        width, height = image.size
        pixel_x = int(width * center_point["x"])
        pixel_y = int(height * center_point["y"])

        if return_annotated_image:
            # Annotate image (draw circle at center)
            draw = ImageDraw.Draw(image)
            r = 30
            shape = [(pixel_x - r, pixel_y - r), (pixel_x + r, pixel_y + r)]
            draw.ellipse(shape, outline="green", width=20)
            draw.ellipse(shape, outline="white", width=10)
        else:
            image = None

        return image, center_point