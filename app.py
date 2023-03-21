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


async def log_browser_console_message(msg):
    values = []
    for arg in msg.args:
        values.append(await arg.json_value())
    try:
        level = logger.level(msg.type.upper()).name
    except ValueError:
        level = 'DEBUG'
    logger.log(level, 'Browser console[{level}]: {s}', level=level, s=values)


async def story_check(story: str):
    logger.debug("Story Check starting for user story:\n {story}", story=story)
    try:
        # start local blockchain fork
        chain = LocalChain()
        await chain.start()
        # parse md
        # setup user agent (playwright) with mock wallet
        # and user story prerequisites
        # TODO: read actual values from story markdown text
        prerequisites = {
            'wallet': {
                'ETH': 0.11
            }
        }
        user_agent = UserAgent(prerequisites=prerequisites)

        await user_agent.start()
        # init ai model
        refexp = RefExp()
        # run steps with VLM
        logger.debug("Running Story Steps...")
        page = user_agent.page

        page.on("console", log_browser_console_message)

        await page.evaluate("console.log('hello', 5, {foo: 'bar'})")

        # await page.goto("http://whatsmyuseragent.org/")
        # await page.screenshot(path="results/example_1.png")
        await page.goto("http://app.uniswap.org/")
        await page.screenshot(path="results/example_2.png", animations='disabled')
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
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_3.png", animations='disabled')

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
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_4.png", animations='disabled')

        with Image.open("results/example_4.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select MetaMask option")
            annotated_image.save("results/example_4_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_5.png", animations='disabled')

        with Image.open("results/example_5.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select text field left of ETH dropdown button")
            annotated_image.save("results/example_5_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_6.png",
                              animations='disabled',
                              caret='initial')

        await page.keyboard.type("0.1")
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_7.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_7.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="click on select token dropdown button")
            annotated_image.save("results/example_7_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_8.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_8.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select search name text field")
            annotated_image.save("results/example_8_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_9.png",
                              animations='disabled',
                              caret='initial')

        await page.keyboard.type("DAI")
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_10.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_10.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="click on Dai Stablecoin option")
            annotated_image.save("results/example_10_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_11.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_11.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select text field left of DAI dropdown button")
            annotated_image.save("results/example_11_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_12.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_12.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="Click on Swap button")
            annotated_image.save("results/example_12_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_13.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_13.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image,
                prompt="click on the pink  confirm swap button at the bottom")
            annotated_image.save("results/example_13_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_14.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_14.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image,
                prompt="click on accept button at the bottom right of price updated")
            annotated_image.save("results/example_14_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_15.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_15.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image,
                prompt="click on the pink  confirm swap button at the bottom")
            annotated_image.save("results/example_15_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_16.png",
                              animations='disabled',
                              caret='initial')

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
