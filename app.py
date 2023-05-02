import gradio as gr
from loguru import logger
import asyncio
import os
from dotenv import load_dotenv
from markdown import StoryParser, UserStory
from interpreter import StoryInterpreter
from pathlib import Path
import json
import argparse
import sys

RESULTS_DIR = Path('./results')


async def story_check(story: str):
    logger.debug("Story Check starting for user story:\n {story}", story=story)
    # init md parser
    parser = StoryParser()
    user_story: UserStory = parser.parse(story)
    story_interpreter = StoryInterpreter(
        user_story=user_story)
    logger.debug("Running Story Check...")
    passed, errors = await story_interpreter.run()
    logger.debug(
        "Story Check Results: passed: {p}, errors: {e}", p=passed, e=errors)
    json_errors = json.dumps(errors)
    logger.debug("Story Check Finished.")
    return passed, json_errors


def load_args():
    """Parse and return command line args."""
    parser = argparse.ArgumentParser(
        prog='StoryCheck by GuardianUI',
        description='Parses and executes user stories written in markdown format.',
        epilog='Copyright(c) guardianui.com 2023')
    # parser.add_argument('filename')           # positional argument
    parser.add_argument('-i', '--input-file',
                        required=True,
                        help='path to the user story input markdown file (e.g. story.md)')
    parser.add_argument('-o', '--output-dir',
                        help='directory where all results from the storycheck will be stored.',
                        default=RESULTS_DIR)
    parser.add_argument('--serve',
                        action='store_true',
                        default=False,
                        help='whether to start as a web service or run storycheck and exit.')
    args = parser.parse_args()
    return args


def start_web_service(args):
    with open(args.input_file, 'r') as file:
        initial_story = file.read()
    title = "StoryCheck Playground by GuardianUI"
    with gr.Blocks(title=title) as demo:
        with gr.Tab("Edit"):
            inp = gr.Textbox(lines=10, label="Input User Story in Markdown format:",
                             value=initial_story)
        with gr.Tab("Preview"):
            md_preview = gr.Markdown(value=inp.value)
        inp.change(lambda text: text, inp, md_preview)
        btn = gr.Button(value="Run", variant="primary")
        out = [gr.Checkbox(
            label="Passed", info="User story checks out?"), gr.Markdown()]
        btn.click(story_check, inputs=inp, outputs=out)
    try:
        demo.launch(server_name="0.0.0.0")
    except Exception:
        # usually caused by CTRL+C and related exceptions
        pass
    finally:
        demo.close()


async def run_check(args):
    with open(args.input_file, 'r') as file:
        initial_story = file.read()
    return await story_check(initial_story)


async def main():
    load_dotenv()
    args = load_args()
    story_path = Path(args.input_file)
    logger.debug('Opening input file: {infile}', infile=story_path)
    assert story_path.exists(), 'Input file not found.'
    os.environ["GUARDIANUI_STORY_PATH"] = str(story_path)
    output_dir = args.output_dir
    logger.debug('Setting output dir to: {o}', o=output_dir)
    results_path = Path(output_dir)
    results_path.mkdir(parents=True, exist_ok=True)
    os.environ["GUARDIANUI_RESULTS_PATH"] = str(results_path)
    logger.add(results_path / 'storycheck.log', rotation="2 MB")
    if args.serve:
        start_web_service(args)
    else:
        passed, json_errors = await run_check(args)
        assert passed, 'StoryCheck FAILED'


def amain() -> int:
    try:
        asyncio.run(main())
    except AssertionError as ae:
        logger.warning(ae)
        return 1
    except KeyboardInterrupt:
        logger.info('StoryCheck aborted manually.')
        return 2
    except Exception as err:
        logger.exception('Error: {e}', e=err)
        return 3
    logger.info('StoryCheck PASSED!')
    return 0  # success


# __main__ support is still here to make this file executable without
# installing the package first.
if __name__ == '__main__':
    sys.exit(amain())
