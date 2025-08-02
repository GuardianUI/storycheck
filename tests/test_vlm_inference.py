from PIL import Image, ImageDraw
from pathlib import Path
import time
import logging
import os

# Configure logging with console and file output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('results/test_vlm_inference.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(file_handler)
results_dir = Path(os.environ.get("GUARDIANUI_RESULTS_PATH", "results/"))
results_dir.mkdir(parents=True, exist_ok=True)

# Counter for inference calls
inference_call_count = 0

def annotate_image(image: Image.Image, coordinates: list, output_path: str):
    """Annotate image with red circles at given coordinates."""
    draw = ImageDraw.Draw(image)
    radius = 10 # Size of the marker
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

def benchmark_inference(image_path, expressions, local_refexp, debug=False):
    global inference_call_count
    start_time = time.time()
    
    # Load image
    image = Image.open(image_path).convert("RGB")
    
    if isinstance(expressions, str):
        expressions = [expressions]
    
    results = []
    valid_coordinates = []
    for exp in expressions:
        inference_call_count += 1
        logger.debug(f"Starting inference call #{inference_call_count} for '{exp}'")
        try:
            _, center_point = local_refexp.process_refexp(image, exp, return_annotated_image=False)
            x, y = center_point.get('x', 0), center_point.get('y', 0)
            logger.debug(f"Image loaded: original {image.width}x{image.height}; Coordinates from LocalRefExp: ({x}, {y})")
            results.append(f"{x},{y}")
            valid_coordinates.append((x, y))
        except Exception as e:
            logger.error(f"Failed inference for '{exp}': {e}")
            results.append("invalid")
    
    # Annotate image with valid coordinates
    if valid_coordinates:
        annotate_image(image.copy(), valid_coordinates, "results/annotated_image.png")
    
    end_time = time.time()
    logger.debug(f"Inference time for {len(expressions)} prompts: {end_time - start_time:.2f}s")
    logger.debug(f"Throughput: {len(expressions) / (end_time - start_time):.2f} inferences/sec")
    if results:
        logger.debug(f"Predicted coords (first result): {results[0]}")
    if debug and results:
        logger.debug(f"Full results: {results}")
    return results, image

def test_vlm_inference(shared_local_refexp):
    # Expected coordinates for each expression (scaled to original image 1126x950)
    expected_coords = [
        (1075, 119), # click the connect button
        (704, 586), # click 'Select Token' dropdown
        (719, 451), # click on ETH dropdown
        (104, 125), # open Trade menu
        (559, 884), # Click on arrow below 'Scroll to learn'
        (559, 681), # Click on Get started button
        (499, 451), # Click on Sell text field
        (555, 587), # Click on Buy text field
        (575, 125) # type weth in search field
    ]
    tolerance = 10 # Pixel tolerance for coordinate variations
   
    # Test the inference function with a dummy image and expression
    results, image = benchmark_inference(image_path, expressions, shared_local_refexp, debug=True)
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
        distance = ((x - expected_x)**2 + (y - expected_y)**2)**0.5
        logger.debug(f"Coordinate check for '{exp}': predicted ({x}, {y}), expected ({expected_x}, {expected_y}), distance {distance:.2f} pixels")
        assert distance <= tolerance, f"Coordinates ({x}, {y}) for '{exp}' deviate too far from expected ({expected_x}, {expected_y}) by {distance:.2f} pixels"
    
    # Explicit cleanup to prevent hangs
    import gc
    import torch
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

if __name__ == "__main__":
    test_vlm_inference()