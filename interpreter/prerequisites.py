from .section import StorySection
from .step import StepInterpreter, get_prompt_text
import re
from enum import Enum, auto
from loguru import logger


class ChainIdReq(StepInterpreter):

    async def interpret_prompt(self, prompt):

        def get_prompt_link(ast_prompt: list) -> str:
            for c in ast_prompt[0]['children']:
                if c['type'] == 'link':
                    return c['link']

        page = self.user_agent.page
        link = get_prompt_link(prompt)
        logger.debug('prompt: {prompt},\n link: {link}',
                     prompt=prompt, link=link)
        await page.goto(link)
        await self.save_screenshot()


class BlockNReq(StepInterpreter):

    async def interpret_prompt(self, prompt):

        def get_prompt_link(ast_prompt: list) -> str:
            for c in ast_prompt[0]['children']:
                if c['type'] == 'link':
                    return c['link']

        page = self.user_agent.page
        link = get_prompt_link(prompt)
        logger.debug('prompt: {prompt},\n link: {link}',
                     prompt=prompt, link=link)
        await page.goto(link)
        await self.save_screenshot()


class Prerequisites(StorySection):

    class ReqLabels(Enum):
        CHAINID = auto()
        BLOCK_N = auto()
        USER_ETH_BALANCE = auto()

    def __init__(self, user_agent=None, **kwargs):
        super().__init__(user_agent=user_agent, **kwargs)
        self.interpreters = {
            self.ReqLabels.CHAINID: ChainIdReq(user_agent=self.user_agent),
            self.ReqLabels.BLOCK_N: BlockNReq(user_agent=self.user_agent),
        }

    def classify_prompt(self, prompt: list = None):
        """
        Classifies a natural language prompt in md-AST format as one of multiple predefined options.
        """
        assert prompt is not None
        text = get_prompt_text(prompt)
        text = text.lower().strip()
        if re.match(r'chainid\b', text):
            return self.ReqLabels.CHAINID
        elif re.match(r'block\b', text):
            return self.ReqLabels.BLOCK_N

    def get_interpreter_by_class(self, prompt_class=None) -> StepInterpreter:
        """
        Look for the interpreter of a specific prompt class.
        """
        return self.interpreters[prompt_class]

    def __enter__(self):
        """
        runs when prerequisite used in 'with' python construct
        """
        self.run()

    def __exit__(self, type, value, traceback):
        """
        runs on exiting a 'with' python construct
        """
        # Exception handling here
        if self.user_agent.chain is not None:
            await self.user_agent.chain.stop()
