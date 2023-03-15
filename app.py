import re
import gradio as gr
from PIL import Image, ImageDraw
import math
import torch
import html
from transformers import DonutProcessor, VisionEncoderDecoderModel
from loguru import logger

global model, loaded_revision, processor, device
model = None
previous_revision = None
processor = None
device = None
loaded_revision = None


def load_model(pretrained_revision: str = 'main'):
    global model, loaded_revision, processor, device
    pretrained_repo_name = 'ivelin/donut-refexp-click'
    # revision can be git commit hash, branch or tag
    # use 'main' for latest revision
    print(
        f"Loading model checkpoint from repo: {pretrained_repo_name}, revision: {pretrained_revision}")
    if processor is None or loaded_revision is None or loaded_revision != pretrained_revision:
        loaded_revision = pretrained_revision
        processor = DonutProcessor.from_pretrained(
            pretrained_repo_name, revision=pretrained_revision)  # , use_auth_token="...")
        processor.image_processor.do_align_long_axis = False
        # do not manipulate image size and position
        processor.image_processor.do_resize = False
        processor.image_processor.do_thumbnail = False
        processor.image_processor.do_pad = False
        # processor.image_processor.do_rescale = False
        processor.image_processor.do_normalize = True
        print(f'processor image size: {processor.image_processor.size}')
        model = VisionEncoderDecoderModel.from_pretrained(
            pretrained_repo_name, revision=pretrained_revision)  # use_auth_token="...",
        print(f'model checkpoint loaded')
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)


def prepare_image_for_encoder(image=None, output_image_size=None):
    """
    First, resizes the input image to fill as much as possible of the output image size
    while preserving aspect ratio. Positions the resized image at (0,0) and fills
    the rest of the gap space in the output image with black(0).
    Args:
        image: PIL image
        output_image_size: (width, height) tuple
    """
    assert image is not None
    assert output_image_size is not None
    img2 = image.copy()
    img2.thumbnail(output_image_size)
    oimg = Image.new(mode=img2.mode, size=output_image_size, color=0)
    oimg.paste(img2, box=(0, 0))
    return oimg


def translate_point_coords_from_out_to_in(point=None, input_image_size=None, output_image_size=None):
    """
    Convert relative prediction coordinates from resized encoder tensor image
    to original input image size.
    Args:
        original_point: x, y coordinates of the point coordinates in [0..1] range in the original image
        input_image_size: (width, height) tuple
        output_image_size: (width, height) tuple
    """
    assert point is not None
    assert input_image_size is not None
    assert output_image_size is not None
    print(
        f"point={point}, input_image_size={input_image_size}, output_image_size={output_image_size}")
    input_width, input_height = input_image_size
    output_width, output_height = output_image_size

    ratio = min(output_width/input_width, output_height/input_height)

    resized_height = int(input_height*ratio)
    resized_width = int(input_width*ratio)
    print(f'>>> resized_width={resized_width}')
    print(f'>>> resized_height={resized_height}')

    if resized_height == input_height and resized_width == input_width:
        return

    # translation of the relative positioning is only needed for dimentions that have padding
    if resized_width < output_width:
        # adjust for padding pixels
        point['x'] *= (output_width / resized_width)
    if resized_height < output_height:
        # adjust for padding pixels
        point['y'] *= (output_height / resized_height)
    print(
        f"translated point={point}, resized_image_size: {resized_width, resized_height}")


def process_refexp(image: Image, prompt: str, model_revision: str = 'main', return_annotated_image: bool = True):

    print(f"(image, prompt): {image}, {prompt}")

    if not model_revision:
        model_revision = 'main'

    print(f"model checkpoint revision: {model_revision}")

    load_model(model_revision)

    # trim prompt to 80 characters and normalize to lowercase
    prompt = prompt[:80].lower()

    # prepare encoder inputs
    out_size = (
        processor.image_processor.size['width'], processor.image_processor.size['height'])
    in_size = image.size
    prepped_image = prepare_image_for_encoder(
        image, output_image_size=out_size)
    pixel_values = processor(prepped_image, return_tensors="pt").pixel_values

    # prepare decoder inputs
    task_prompt = "<s_refexp><s_prompt>{user_input}</s_prompt><s_target_center>"
    prompt = task_prompt.replace("{user_input}", prompt)
    decoder_input_ids = processor.tokenizer(
        prompt, add_special_tokens=False, return_tensors="pt").input_ids

    # generate answer
    outputs = model.generate(
        pixel_values.to(device),
        decoder_input_ids=decoder_input_ids.to(device),
        max_length=model.decoder.config.max_position_embeddings,
        early_stopping=True,
        pad_token_id=processor.tokenizer.pad_token_id,
        eos_token_id=processor.tokenizer.eos_token_id,
        use_cache=True,
        num_beams=1,
        bad_words_ids=[[processor.tokenizer.unk_token_id]],
        return_dict_in_generate=True,
    )

    # postprocess
    sequence = processor.batch_decode(outputs.sequences)[0]
    print(fr"predicted decoder sequence: {html.escape(sequence)}")
    sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(
        processor.tokenizer.pad_token, "")
    # remove first task start token
    sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()
    print(
        fr"predicted decoder sequence before token2json: {html.escape(sequence)}")
    seqjson = processor.token2json(sequence)

    # safeguard in case predicted sequence does not include a target_center token
    center_point = seqjson.get('target_center')
    if center_point is None:
        print(
            f"predicted sequence has no target_center, seq:{sequence}")
        center_point = {"x": 0, "y": 0}
        return center_point

    print(f"predicted center_point with text coordinates: {center_point}")
    # safeguard in case text prediction is missing some center point coordinates
    # or coordinates are not valid numeric values
    try:
        x = float(center_point.get("x", 0))
    except ValueError:
        x = 0
    try:
        y = float(center_point.get("y", 0))
    except ValueError:
        y = 0
    # replace str with float coords
    center_point = {"x": x, "y": y,
                    "decoder output sequence (before x,y adjustment)": sequence}
    print(f"predicted center_point with float coordinates: {center_point}")

    print(f"input image size: {in_size}")
    print(f"processed prompt: {prompt}")

    # convert coordinates from tensor image size to input image size
    out_size = (
        processor.image_processor.size['width'], processor.image_processor.size['height'])
    translate_point_coords_from_out_to_in(
        point=center_point, input_image_size=in_size, output_image_size=out_size)

    width, height = in_size
    x = math.floor(width*center_point["x"])
    y = math.floor(height*center_point["y"])

    print(
        f"to image pixel values: x, y: {x, y}")

    if return_annotated_image:
        # draw center point circle
        img1 = ImageDraw.Draw(image)
        r = 30
        shape = [(x-r, y-r), (x+r, y+r)]
        img1.ellipse(shape, outline="green", width=20)
        img1.ellipse(shape, outline="white", width=10)
    else:
        # do not return image if its an API call to save bandwidth
        image = None

    return image, center_point


def story_check(story: str):

    logger.debug('user story', story)
    result = {'result': 'Success'}

    # Use gradio advanced controls to render markdown and allow edit
    # then parse
    # setup playwright with mock wallet
    # run steps with VLM
    # check results
    # return results
    # in case of errors, return meaningful message with suggested corrective actions

    return result


title = "StoryCheck Playground by GuardianUI"
description = """
  StoryCheck playground for Web3 apps.
  It takes as input markdown formatted user stories
  with steps written in natural language.
  Then it parses the text and executes the steps in a virtual web browser
  closely emulating
  the actions of a real user.
  """
examples = [["""# Test basic playwright interaction
                ## Context
                  - Wallet has:
                    - 0.1 ETH
                    - 0 DAI

                ## Steps
                1. Go to http://uniswap.org/
                2. Connect wallet
                3. Swap ETH for DAI
                4. Submit

                ## Result
                  - Wallet has:
                    - < 0.1 ETH
                    - > 100 DAI
              """]
            ]

# demo = gr.Interface(fn=story_check,
#                     inputs=["text"],
#                     outputs=["json"],
#                     title=title,
#                     description=description,
#                     examples=examples,
#                     cache_examples=False
#                     )

initial_story = """
# Swapping ETH for DAI on Uniswap

## Prerequisites
- User crypto wallet has 0.11 ETH

## Steps
1. Go to https://app.uniswap.org
2. Click on Connect Wallet
3. Swap ETH for DAI

## Expected results
- User crypto wallet has 0.1 ETH less
- User crypto wallet has 100 DAI more
"""

with gr.Blocks(title=title) as demo:
    inp = gr.Textbox(lines=10, label="Input User Story in Markdown format:",
                     value=initial_story)
    md_preview = gr.Markdown(value=inp.value)
    inp.change(lambda text: text, inp, md_preview)
    btn = gr.Button(value="Run", variant="primary")
    out = gr.Markdown()
    btn.click(fn=lambda md: "Success!", inputs=inp, outputs=out)

if __name__ == "__main__":
    demo.launch()

# share=True when running in a Jupyter Notebook
try:
    demo.launch(server_name="0.0.0.0")
except Exception:
    # usually caused by CTRL+C and related exceptions
    pass
finally:
    demo.close()
