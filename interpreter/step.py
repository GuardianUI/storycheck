from abc import abstractmethod, ABC
from loguru import logger
from PIL import Image
import re  # For extract_url in BrowseStep

from interpreter.ai import local_refexp

def get_prompt_text(ast_prompt: list) -> str:
    """
    Helper method for pulling text value from a parsed MD AST structure
    """
    for c in ast_prompt[0]['children']:
        if c['type'] == 'text':
            return c['raw']

def get_prompt_link(ast_prompt: list) -> str:
    """
    Helper method for pulling URL value from a parsed MD AST structure
    """
    for c in ast_prompt[0]['children']:
        if c['type'] == 'link':
            return c['href']

class StepInterpreter(ABC):
    def __init__(self, user_agent=None):
        self.user_agent = user_agent

    @abstractmethod
    async def interpret_prompt(self, prompt: str):
        """
        Interpret in computer code the intention of a natural language input prompt.
        Parameters:
          prompt(str): natural language prompt
        """
        pass

class NotImplementedInterpreter(StepInterpreter):
    """
    Placeholder for prompts that cannot be interpreted.
    """
    async def interpret_prompt(self, prompt: str):
        logger.warning(
'Interpreter not implemented for prompt: {prompt}', prompt=prompt)

class BrowseStep(StepInterpreter):
    """
    Interpreter for browse prompts (restored from original repo).
    """
    async def interpret_prompt(self, prompt: str):
        # Assuming prompt is string; adjust if AST
        url = self.extract_url(prompt)
        if url:
            await self.user_agent.page.goto(url)
        else:
            logger.warning(f"No URL found in browse prompt: {prompt}")

    def extract_url(self, text):
        match = re.search(r'(https?://\S+)', text)
        return match.group(1) if match else None

class ClickStep(StepInterpreter):
    async def interpret_prompt(self, prompt: str):
        screenshot = await self.user_agent.page.screenshot(type='png')
        screenshot = Image.frombytes("RGB", screenshot.size, screenshot)
        annotated_image, center_point = await local_refexp.process_refexp(screenshot, prompt)
        pixel_x = int(screenshot.width * center_point["x"])
        pixel_y = int(screenshot.height * center_point["y"])
        await self.user_agent.page.mouse.click(pixel_x, pixel_y)

class KBInputStep(StepInterpreter):
    async def interpret_prompt(self, prompt: str):
        await self.user_agent.page.keyboard.type(prompt)

class ScrollStep(StepInterpreter):
    async def interpret_prompt(self, prompt: str):
        if 'up' in prompt.lower():
            await self.user_agent.page.keyboard.press('PageUp')
        else:
            await self.user_agent.page.keyboard.press('PageDown')

class KeyPressStep(StepInterpreter):
    async def interpret_prompt(self, prompt: str):
        await self.user_agent.page.keyboard.press(prompt)