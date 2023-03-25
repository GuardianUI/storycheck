from . import StorySection, StepInterpreter
from ai import RefExp
from enum import Enum, auto
import re
import time
from loguru import logger
from PIL import Image


class UserStepInterpreter(StepInterpreter):
    saved_screenshot_path = None

    async def save_screenshot(self):
        self.saved_screenshot_path = f'{time.monotonic_ns()}_{self.__class__()}.png'
        await self.user_agent.page.screenshot(path=self.saved_screenshot_path,
                                              animations='disabled',
                                              caret='initial',
                                              full_page=True)


class BrowseInterpreter(StepInterpreter):
    async def interpret_prompt(self, prompt):
        page = self.user_agent.page
        # TODO: extract link from prompt
        await page.goto("https://app.sporosdao.xyz/")
        await self.save_screenshot()


class ClickInterpreter(StepInterpreter):
    def __init__(self, *args, **kwargs):
        super.__init__(*args, **kwargs)
        self.refexp = RefExp()

    def interpret_prompt(self, prompt=None, screenshot_path: str = None):
        assert prompt is not None
        assert screenshot_path is not None
        """
        Interpret in computer code the intention of the natural language input prompt.

        Parameters:
          prompt(str): natural language prompt
          screenshot_path(str): most recent page screenshot
        """
        page = self.user_agent.page
        with Image.open(screenshot_path) as image:
            annotated_image, center_point = self.refexp.process_refexp(
                image=image, prompt=prompt)
            annotated_image.save(f'{screenshot_path}_click_annotated.png')
            logger.debug("center point: {cp}", cp=center_point
                         )
            width, height = image.size
        click_point = self.xyxy(point=center_point, page=page)
        logger.debug("Mouse click at x:{x}, y:{y}",
                     x=click_point['x'], y=click_point['y'])
        await page.mouse.click(click_point['x'], click_point['y'])
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await self.save_screenshot()


class KBInputInterpreter(StepInterpreter):
    async def interpret_prompt(self, prompt):
        page = self.user_agent.page
        _, value = prompt.split(' ', 1)
        await page.keyboard.type(value)
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await self.save_screenshot()


class ScrollInterpreter(StepInterpreter):
    async def interpret_prompt(self, prompt):
        page = self.user_agent.page
        _, direction = prompt.split(' ', 1)
        direction = direction.trim().lower()
        if direction == 'up':
            await page.keyboard.press("PageUp")
        elif direction == 'down':
            await page.keyboard.press("PageDown")
        else:
            logger.warning('scroll {dir} not implemented', dir=direction)
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
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
        ClassLabels.KB_INPUT: KBInputInterpreter,
        ClassLabels.SCROLL: ScrollInterpreter
    }

    def classify_prompt(self, prompt: str = None):
        """
        Classifies a natural language prompt as one of multiple predefined options.
        """
        assert prompt is not None
        prompt = prompt.lower().trim()
        if prompt.lower().startswith('scroll'):
            return self.ClassLabels.SCROLL
        elif prompt.lower().startswith('press'):
            return self.ClassLabels.KEYPRESS
        elif prompt.lower().startswith('review'):
            return self.ClassLabels.REVIEW
        elif re.match(r'type\b|input\b|enter\b', prompt.lower()):
            return self.ClassLabels.KB_INPUT
        elif re.match(r'click\b|select\b|tap\b', prompt.lower()):
            return self.ClassLabels.CLICK
        elif re.match(r'browse\b', prompt.lower()):
            return self.ClassLabels.CLICK

    def get_interpreter_by_class(self, prompt_class=None) -> StepInterpreter:
        """
        Look for the interpreter of a specific prompt class.
        """
        return self.interpreters(prompt_class)
