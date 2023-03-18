import gradio as gr
from loguru import logger
import asyncio
from blockchain import LocalChain
from browser import UserAgent
from ai import RefExp
from PIL import Image
from dotenv import load_dotenv


async def story_check(story: str):
    logger.debug("Story Check starting for user story:\n {story}", story=story)
    try:
        # start local blockchain fork
        chain = LocalChain()
        await chain.start()
        # parse md
        # setup playwright with mock wallet
        user_agent = UserAgent()
        await user_agent.start()
        # init ai model
        refexp = RefExp()
        # run steps with VLM
        logger.debug("Running Story Steps...")
        page = user_agent.page
        await page.goto("http://whatsmyuseragent.org/")
        await page.screenshot(path="results/example_1.png")
        await page.goto("http://app.uniswap.org/")
        await page.screenshot(path="results/example_2.png")
        with Image.open("results/example_2.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select get started button")
            annotated_image.save("results/example_2_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        screen_x = int(width*center_point['x'])
        screen_y = int(height*center_point['y'])
        logger.debug("Mouse click at x:{x}, y:{y}", x=screen_x, y=screen_y)
        await page.mouse.click(screen_x, screen_y)
        await page.wait_for_url("**/#/swap")
        # await page.wait_for_timeout(2000)
        await page.mouse.dblclick(screen_x, screen_y)
        # await page.wait_for_url("**")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_3.png")
        logger.debug("Done running Story Steps...")
        # check results
        # return results
        # in case of errors, return meaningful message with suggested corrective actions
        result = 'Success'
    except Exception as e:
        logger.exception(e)
        result = 'Error'
    finally:
        await user_agent.stop()
        await chain.stop()
        logger.debug("Story Check Finished.")
    return result


async def main():
    load_dotenv()
    title = "StoryCheck Playground by GuardianUI"
    with open('examples/uniswap.md', 'r') as file:
        initial_story = file.read()
    with gr.Blocks(title=title) as demo:
        inp = gr.Textbox(lines=10, label="Input User Story in Markdown format:",
                         value=initial_story)
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
