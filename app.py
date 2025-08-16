# File: app.py
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


async def story_check(story_path: str):
    with open(story_path, 'r') as story_file:
        story = story_file.read()
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
    parser.add_argument('storypath',
                        help='Path to the user story directory (e.g. examples/mystory).')
    parser.add_argument('-o', '--output-dir',
                        help=f'Directory where all results from the storycheck run will be stored. Defaults to "{RESULTS_DIR}"',
                        default=RESULTS_DIR)
    run_as_service = False
    parser.add_argument('--serve',
                        action='store_true',
                        default=run_as_service,
                        help=f'Run as a web service. Defaults to "{run_as_service}".')
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
    return await story_check(args.story_md_path)


async def main():
    load_dotenv()
    args = load_args()
    story_dir = Path(args.storypath)
    assert story_dir.is_dir(), 'Story directory not found.'
    story_md_path = story_dir / 'story.md'
    assert story_md_path.exists(), 'story.md not found in directory.'
    args.story_md_path = str(story_md_path)
    logger.debug('Opening story file: {infile}', infile=story_md_path)
    os.environ["GUARDIANUI_STORY_PATH"] = str(story_md_path)
    os.environ["GUARDIANUI_STORY_DIR"] = str(story_dir)
    output_dir = args.output_dir
    logger.debug('Setting output dir to: {o}', o=output_dir)
    story_slug = story_dir.name
    results_path = Path(output_dir) / story_slug
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
        logger.error(ae)
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