from . import StorySection, StepInterpreter
from ai import RefExp
from enum import Enum, auto
import re
import time
from loguru import logger


class UserStepInterpreter(StepInterpreter):
    saved_screenshot_path = None

    async def save_screenshot(self):
        self.saved_screenshot_path = str(
            time.monotonic_ns()) + self.__class__() + '.png'
        await self.user_agent.page.screenshot(path="results/example_2.png",
                                              animations='disabled',
                                              caret='initial',
                                              full_page=True)


class ClickInterpreter(StepInterpreter):
    def interpret_prompt(self, prompt):
        """
        Interpret in computer code the intention of the natural language input prompt.
        """
        pass


class BrowseInterpreter(StepInterpreter):
    async def interpret_prompt(self, prompt):
        """
        Interpret in computer code the intention of the natural language input prompt.
        """
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

        await self.save_screenshot()


class UserSteps(StorySection):

    class ClassLabels(Enum):
        CLICK = auto()
        BROWSE = auto()
        SCROLL = auto()
        KB_TYPE = auto()
        KEYPRESS = auto()
        REVIEW = auto()

    interpreters = {
        ClassLabels.CLICK: ClickInterpreter,
        ClassLabels.BROWSE: BrowseInterpreter,
        ClassLabels.SCROLL: ScrollInterpreter,
        ClassLabels.TYPE: KBTypeInterpreter,
        ClassLabels.PRESS: KeyPressIntrepreter
    }

    def classify_prompt(self, prompt: str = None):
        """
        Classifies a natural language prompt as one of multiple predefined options.
        """
        assert prompt is not None
        prompt = prompt.lower().trim()
        if prompt.lower().startswith('scroll'):
            return self.ClassLabels.SCROLL
        elif prompt.lower().startswith('type'):
            return self.ClassLabels.KB_TYPE
        elif prompt.lower().startswith('press'):
            return self.ClassLabels.KEYPRESS
        elif prompt.lower().startswith('review'):
            return self.ClassLabels.REVIEW
        elif re.match(r'click\b|select\b|tap\b', prompt.lower()):
            return self.ClassLabels.CLICK
        elif re.match(r'browse\b', prompt.lower()):
            return self.ClassLabels.CLICK

    def get_interpreter_by_class(self, prompt_class=None) -> StepInterpreter:
        """
        Look for the interpreter of a specific prompt class.
        """
        return self.interpreters(prompt_class)

    def temp_TODO_REMOVE():
        page = self.user_agent.page
        page.on("console", log_browser_console_message)

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

        logger.debug("Done running User Story Steps...")

        prerequisites = Prerequisites(user_agent=self.user_agent,
                                      prompts=self.user_story.prerequisites)
        prerequisites.run()
        user_steps = UserSteps(user_agent=self.user_agent,
                               prompts=self.user_story.user_steps)
        user_steps.run()
        expected_results = ExpectedResults(
            user_agent=self.user_agent, prompts=self.user_story.expected_results)
        expected_results.run()
        # TODO: implement proper result object with success and error properties
        result = 'Success'
        return result
