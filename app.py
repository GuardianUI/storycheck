import gradio as gr
from loguru import logger
import asyncio
from blockchain import LocalChain
from browser import UserAgent

from dotenv import load_dotenv
from markdown import StoryParser, UserStory
from interpreter import StoryInterpreter


async def story_check(story: str):
    logger.debug("Story Check starting for user story:\n {story}", story=story)
    try:
        # start local blockchain fork
        chain = LocalChain()
        await chain.start()
        user_agent = UserAgent()
        await user_agent.start()
        # init md parser
        parser = StoryParser()
        user_story: UserStory = parser.parse(story=story,
                                             user_agent=user_agent)
        story_interpreter = StoryInterpreter(
            user_story=user_story, user_agent=user_agent)
        logger.debug("Running Story Check...")
        result = story_interpreter.run()
    except Exception as e:
        logger.exception("Story Check Error: {e}", e=e)
        result = 'Error'
    finally:
        await user_agent.stop()
        await chain.stop()
        logger.debug("Story Check Finished.")
    return result


async def main():
    logger.add("storycheck.log", rotation="2 MB", enqueue=True)
    load_dotenv()
    title = "StoryCheck Playground by GuardianUI"
    with open('examples/sporosdao.md', 'r') as file:
        initial_story = file.read()
    with gr.Blocks(title=title) as demo:
        with gr.Tab("Edit"):
            inp = gr.Textbox(lines=10, label="Input User Story in Markdown format:",
                             value=initial_story)
        with gr.Tab("Preview"):
            md_preview = gr.Markdown(value=inp.value)
        inp.change(lambda text: text, inp, md_preview)
        btn = gr.Button(value="Run", variant="primary")
        out = gr.Markdown()
        btn.click(story_check, inputs=inp, outputs=out)
    try:
        demo.launch(server_name="0.0.0.0")
    except Exception:
        # usually caused by CTRL+C and related exceptions
        pass
    finally:
        demo.close()


if __name__ == "__main__":
    asyncio.run(main())
