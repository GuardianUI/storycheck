import re
import json
import logging
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

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

def parse_coordinates(response):
    logger.debug(f"Parsing response: {response}")
    matches = re.findall(r"<tool_call>(.*?)</tool_call>", response, re.DOTALL)
    if not matches:
        logger.error("No <tool_call> block found in response.")
        return None
    for match in matches:
        try:
            action = json.loads(match.strip())
            action_name = action.get("name")
            action_type = action["arguments"].get("action")
            if action_name == "computer_use" and action_type in ("left_click", "mouse_move"):
                coords = action["arguments"].get("coordinate")
                if coords and len(coords) == 2:
                    logger.debug(f"Raw coordinates (resized image): {coords}")
                    return coords
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing tool call: {e}\nTool call: {match.strip()}")
            continue
    logger.error("No valid left_click or mouse_move tool call found in response.")
    return None

def annotate_image(image: Image.Image, coordinates: list, output_path: str):
    """Annotate image with red circles at given coordinates."""
    draw = ImageDraw.Draw(image)
    radius = 20  # Size of the marker
    for coord in coordinates:
        x, y = coord
        logger.debug(f"Annotating coordinate on original image: ({x}, {y})")
        # Draw a red circle at the coordinate
        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=None,
            outline="red",
            width=4
        )
    image.save(output_path)
    logger.info(f"Annotated image saved to {output_path}")