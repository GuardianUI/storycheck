from .section import StorySection
from .step import StepInterpreter, get_prompt_text
from .ai import RefExp
from enum import Enum, auto
import re
import time
from loguru import logger
from PIL import Image


class UserStepInterpreter(StepInterpreter):

    @property
    def saved_screenshot_path(self):
        return self.user_agent.session['saved_screenshot_path']
        # logger.debug(
        #     'self.user_agent.session: {session}', session=self.user_agent.session)

    async def save_screenshot(self):
        path = f'results/{time.monotonic_ns()}_{self.__class__.__name__}.png'
        await self.user_agent.page.screenshot(path=path,
                                              animations='disabled',
                                              caret='initial')
        self.user_agent.session['saved_screenshot_path'] = path
        # logger.debug(
        #     'self.user_agent.session: {session}', session=self.user_agent.session)


class BrowseStep(UserStepInterpreter):

    async def interpret_prompt(self, prompt):

        def get_prompt_link(ast_prompt: list) -> str:
            for c in ast_prompt[0]['children']:
                if c['type'] == 'link':
                    return c['link']
        logger.debug('self.user_agent: {ua}', ua=self.user_agent)
        page = self.user_agent.page
        link = get_prompt_link(prompt)
        logger.debug('prompt: {prompt},\n link: {link}',
                     prompt=prompt, link=link)
        await page.goto(link)
        await self.save_screenshot()


class ClickStep(UserStepInterpreter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.refexp = RefExp()

    def xyxy(self, point=None, page=None):
        assert point is not None
        assert page is not None
        # Convert predicted point in [0..1] range coordinates to viewport coordinates
        vpSize = page.viewport_size
        cpTranslated = {
            'x': int(point['x'] * vpSize['width']),
            'y': int(point['y'] * vpSize['height'])
        }
        return cpTranslated

    async def interpret_prompt(self, prompt=None):
        assert prompt is not None
        """
        Interpret in computer code the intention of the natural language input prompt.

        Parameters:
          prompt(str): natural language prompt
        """
        page = self.user_agent.page
        path = self.saved_screenshot_path
        logger.debug('self.saved_screenshot_path: {path}', path=path)
        text = get_prompt_text(prompt)
        with Image.open(path) as image:
            annotated_image, center_point = self.refexp.process_refexp(
                image=image, prompt=text)
            annotated_image.save(
                f'{path}_click_annotated.png')
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


class KBInputStep(UserStepInterpreter):
    async def interpret_prompt(self, prompt):
        page = self.user_agent.page
        text = get_prompt_text(prompt)
        _, value = text.split(' ', 1)
        await page.keyboard.type(value)
        # wait up to 2 seconds for the page to update as a result of click()
        await page.wait_for_timeout(2000)
        await self.save_screenshot()


class ScrollStep(UserStepInterpreter):
    async def interpret_prompt(self, prompt):
        page = self.user_agent.page
        text = get_prompt_text(prompt)
        _, direction = text.split(' ', 1)
        direction = direction.lower()
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

    class StepLabels(Enum):
        CLICK = auto()
        BROWSE = auto()
        SCROLL = auto()
        KB_INPUT = auto()
        KEYPRESS = auto()
        REVIEW = auto()

    def __init__(self, user_agent=None, **kwargs):
        super().__init__(**kwargs)
        assert user_agent is not None
        logger.debug('user_agent: {ua}', ua=user_agent)
        self.interpreters = {
            self.StepLabels.CLICK: ClickStep(user_agent=user_agent),
            self.StepLabels.BROWSE: BrowseStep(user_agent=user_agent),
            self.StepLabels.KB_INPUT: KBInputStep(user_agent=user_agent),
            self.StepLabels.SCROLL: ScrollStep(
                user_agent=user_agent)
        }

    def classify_prompt(self, prompt: list = None):
        """
        Classifies a natural language prompt in md-AST format as one of multiple predefined options.
        """
        assert prompt is not None
        text = get_prompt_text(prompt)
        text = text.lower().strip()
        if text.startswith('scroll'):
            return self.StepLabels.SCROLL
        elif text.startswith('press'):
            return self.StepLabels.KEYPRESS
        elif text.startswith('review'):
            return self.StepLabels.REVIEW
        elif re.match(r'type\b|input\b|enter\b', text):
            return self.StepLabels.KB_INPUT
        elif re.match(r'click\b|select\b|tap\b', text):
            return self.StepLabels.CLICK
        elif re.match(r'browse\b', text):
            return self.StepLabels.BROWSE

    def get_interpreter_by_class(self, prompt_class=None) -> StepInterpreter:
        """
        Look for the interpreter of a specific prompt class.
        """
        return self.interpreters[prompt_class]
