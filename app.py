import gradio as gr
from loguru import logger
import asyncio
from blockchain import LocalChain
from browser import UserAgent
from ai import RefExp
from PIL import Image
from dotenv import load_dotenv
from markdown import StoryParser, UserStory


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
        user_agent = UserAgent()
        await user_agent.start()
        # init ai model
        refexp = RefExp()
        # initi md parser
        parser = StoryParser()
        user_story: UserStory = parser.parse(story)
        # return

        # run steps with VLM
        logger.debug("Running Story Steps...")
        page = user_agent.page

        page.on("console", log_browser_console_message)

        # await page.goto("http://whatsmyuseragent.org/")
        # await page.screenshot(path="results/example_1.png")
        await page.goto("https://app.sporosdao.xyz/")

        # get mock wallet address
        address = await page.evaluate("() => window.ethereum.signer.address")
        logger.info(
            'user mock wallet account address: {address}', address=address)
        # check mock wallet balance
        balance = await page.evaluate(
            "(address) => window.ethereum.provider.send('eth_getBalance',[address, 'latest'])",
            address)
        logger.info(
            'user mock wallet account balance: {balance}', balance=balance)

        await page.screenshot(path="results/example_2.png", animations='disabled')
        with Image.open("results/example_2.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="click on connect wallet in the top right corner")
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
                image=image, prompt="click on circle icon in the top right corner")
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
        await page.screenshot(path="results/example_3_1.png", animations='disabled')

        with Image.open("results/example_3_1.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="click on create a new company button")
            annotated_image.save("results/example_3_1_annotated.png")
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
                image=image, prompt="click on Go! right arrow button left of Available")
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

        # get mock wallet address
        address = await page.evaluate("() => window.ethereum.signer.address")
        logger.info(
            'user mock wallet account address: {address}', address=address)
        # check mock wallet balance
        balance = await page.evaluate(
            "(address) => window.ethereum.provider.send('eth_getBalance',[address, 'latest'])",
            address)
        logger.info(
            'user mock wallet account balance: {balance}', balance=balance)

        with Image.open("results/example_5.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select on-chain name text field")
            annotated_image.save("results/example_5_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])

        await page.keyboard.type("Test DAO")
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_7.png",
                              animations='disabled',
                              caret='initial')

        # get mock wallet address
        address = await page.evaluate("() => window.ethereum.signer.address")
        logger.info(
            'user mock wallet account address: {address}', address=address)
        # check mock wallet balance
        balance = await page.evaluate(
            "(address) => window.ethereum.provider.send('eth_getBalance',[address, 'latest'])",
            address)
        logger.info(
            'user mock wallet account balance: {balance}', balance=balance)

        with Image.open("results/example_7.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select Token Symbol text field")
            annotated_image.save("results/example_7_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])

        await page.keyboard.type("TDO")

        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_8.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_8.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select Continue button")
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
                              caret='initial',
                              full_page=True)

        # get mock wallet address
        address = await page.evaluate("() => window.ethereum.signer.address")
        logger.info(
            'user mock wallet account address: {address}', address=address)
        # check mock wallet balance
        balance = await page.evaluate(
            "(address) => window.ethereum.provider.send('eth_getBalance',[address, 'latest'])",
            address)
        logger.info(
            'user mock wallet account balance: {balance}', balance=balance)

        with Image.open("results/example_9.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select Address text field above Enter the wallet address")
            annotated_image.save("results/example_9_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])

        await page.keyboard.type("0x5389199D5168174FA177908685FbD52A7138Ed1a")

        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_11.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_11.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select text field below Initial Tokens")
            annotated_image.save("results/example_11_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])

        await page.keyboard.type("1200")

        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_12.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_12.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select text field under Email")
            annotated_image.save("results/example_12_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])

        await page.keyboard.type("test@email.com")

        await page.keyboard.press("PageDown")

        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_13.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_13.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select Continue button")
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
                image=image, prompt="select Continue button")
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

        await page.keyboard.press("PageUp")

        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_16.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_16.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="click on the checkbox left of Agree")
            annotated_image.save("results/example_16_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])

        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_17.png",
                              animations='disabled',
                              caret='initial')

        await page.keyboard.press("PageDown")

        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_18.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_18.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="select Continue button")
            annotated_image.save("results/example_18_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_19.png",
                              animations='disabled',
                              caret='initial')

        await page.keyboard.press("PageUp")
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_20.png",
                              animations='disabled',
                              caret='initial')

        with Image.open("results/example_20.png") as image:
            annotated_image, center_point = refexp.process_refexp(
                image=image, prompt="Click on Deploy Now button")
            annotated_image.save("results/example_20_annotated.png")
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])

        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="results/example_21.png",
                              animations='disabled',
                              caret='initial')

        # get mock wallet address
        address = await page.evaluate("() => window.ethereum.signer.address")
        logger.info(
            'user mock wallet account address: {address}', address=address)
        # check mock wallet balance
        balance = await page.evaluate(
            "(address) => window.ethereum.provider.send('eth_getBalance',[address, 'latest'])",
            address)
        logger.info(
            'user mock wallet account balance: {balance}', balance=balance)

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
