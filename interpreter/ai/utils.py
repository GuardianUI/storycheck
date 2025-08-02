import math

FN_CALL_TEMPLATE = """You are a helpful assistant.

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

def get_tool_descs():
    """Returns the JSON description for computer_use tool."""
    return {
        "type": "function",
        "function": {
            "name": "computer_use",
            "description": "UI actions",
            "parameters": {
                "properties": {
                    "action": {"type": "string", "enum": ["left_click", "type", "key_press", "mouse_move", "scroll"]},
                    "coordinate": {"type": "array", "items": {"type": "number"}},
                    "text": {"type": "string"},
                    "key": {"type": "string"}
                },
                "required": ["action"]
            }
        }
    }

def round_by_factor(number: int, factor: int) -> int:
    return round(number / factor) * factor

def floor_by_factor(number: int, factor: int) -> int:
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