import gradio as gr
from loguru import logger
import asyncio
from blockchain import LocalChain
from browser import UserAgent
from ai import RefExp
from PIL import Image
from dotenv import load_dotenv


def xyxy(point=None, page=None):
    assert point is not None
    assert page is not None
    # Convert predicted point in [0..1] range coordinates to viewport coordinates
    vpSize = page.viewport_size
    cpTranslated = {
        'x': int(point['x'] * vpSize['width']),
        'y': int(point['y'] * vpSize['height'])
    }
    return cpTranslated


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
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the url to update as a result of click()
        await page.wait_for_url(url="**", timeout=2000)
        await page.screenshot(path="results/example_3.png")

        with Image.open("results/example_3.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select connect wallet button")
            annotated_image.save("results/example_3_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the url to update as a result of click()
        await page.wait_for_url(url="**", timeout=2000)
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_4.png", animations='disabled')

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
