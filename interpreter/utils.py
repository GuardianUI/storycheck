# File: interpreter/utils.py
import time
from pathlib import Path
from PIL import Image, ImageDraw
from loguru import logger
import os
from environs import Env

def load_env():
    """Load environment variables from .env.local or .env in CWD or project root."""
    env = Env()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Define search paths: project root first, then CWD (for priority: CWD overrides root)
    search_paths = [
        project_root,
        os.getcwd()
    ]

    env_files = ['.env', '.env.local']  # Load .env first, then .env.local (overrides)

    for dir_path in search_paths:
        for env_file in env_files:
            full_path = os.path.join(dir_path, env_file)
            if os.path.exists(full_path):
                env.read_env(full_path, recurse=False, override=True)

    return env

def get_timestamped_path(dir_path: Path, file_name: str = "screenshot") -> Path:
    timestamp = time.time()
    return dir_path / f"{timestamp}_{file_name}.png"

def save_screenshot(data, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if isinstance(data, bytes):
            with open(path, "wb") as f:
                f.write(data)
        elif isinstance(data, Image.Image):
            data.save(path)
        else:
            raise ValueError("Unsupported data type for screenshot")
        logger.debug(f"Screenshot saved to {path}")
    except Exception as e:
        logger.error(f"Failed to save screenshot to {path}: {e}")


def annotate_image_with_clicks(image: Image=None, coordinates: list=None, radius=20, color="red") -> Image:
    """
    Annotate image at the given path with red circles at given coordinates (list of (x, y) tuples).
    Overwrites the image file with the annotated version.
    """
    assert image is not None, "Image must be provided"
    assert coordinates, "Coordinates must be provided"
    annotated_image = image.copy()
    draw = ImageDraw.Draw(annotated_image)
    logger.debug(f"Annotating image with coordinates: {coordinates}")
    for coord in coordinates:
        x, y = coord
        # Draw a red circle at the coordinate
        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=None,
            outline=color,
            width=4
        )
    return annotated_image