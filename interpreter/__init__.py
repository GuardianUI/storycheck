from ai import RefExp
from loguru import logger
from PIL import Image
from abc import abstractmethod, ABC


class StorySection(ABC):

    class StepInterpreter(ABC):
        @abstractmethod
        def interpret_prompt(self):
            """
            Interpret in computer code the intention of the natural language input prompt.
            """
            pass

    def __init__(self, prompts: list):
        self.prompts = prompts

    def run(self):
        """
        Run all steps in this story section.
        """
        for p in self.prompts:
            prompt_class = self.classify_prompt(p)
            interpreter = self.get_interpreter_by_class(prompt_class)
            interpreter.interpret_prompt(p)

    @abstractmethod
    def classify_prompt(self, prompt: str = None):
        """
        Classifies a natural language prompt as one of multiple predefined options.
        """
        pass

    @abstractmethod
    def get_interpreter_by_class(self, prompt_class=None) -> StepInterpreter:
        """
        Look for the interpreter of a specific prompt class.
        """


class StoryInterpreter:
    """
    Given a populated UserStory object, it iterates over the list of
    sections and interprets each step per section.
    """

    user_story = None
    refexp_model = None

    async def log_browser_console_message(msg):
        values = []
        for arg in msg.args:
            values.append(await arg.json_value())
        try:
            level = logger.level(msg.type.upper()).name
        except ValueError:
            level = 'DEBUG'
        logger.log(
            level, 'Browser console[{level}]: {s}', level=level, s=values)

    def __init__(self, user_story=None,
                 user_agent=None):
        assert user_story is not None, 'user_story should be a populated object'
        assert user_agent is not None, \
            'user_agent should be a an initialized browser driver object'
        self.user_story = user_story
        self.user_agent = user_agent
        # init ai model
        self.refexp_model = RefExp()

    def interpret_prerequisites(self):
        pass

    def interpret_user_steps(self):
        page = self.user_agent.page
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

        logger.debug("Done running User Story Steps...")

    def interpret_expected_results(self):
        pass

    def run(self):
        self.interpret_prerequisites()
        self.interpret_user_steps()
        self.interpret_expected_results()
        # TODO: implement proper result object with success and error properties
        result = 'Success'
        return result
