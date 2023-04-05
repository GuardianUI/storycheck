from .section import StorySection
from .step import StepInterpreter, get_prompt_text
import re
from enum import Enum, auto
from loguru import logger
from .blockchain import LocalChain


class ChainReq(StepInterpreter):

    async def interpret_prompt(self, prompt):

        def get_prompt_link(ast_prompt: list) -> str:
            for c in ast_prompt[0]['children']:
                if c['type'] == 'link':
                    return c['link']

        logger.debug('chain prompt: {prompt}')
        # chain_id = get_prompt_text(ast_prompt_id)
        # block_n = get_prompt_text(ast_prompt_block)
        # chain = LocalChain(chain_id=chain_id, block_n=block_n)
        # # set chain in session context
        # self.user_agent.chain = chain
        # logger.debug('prompt chain id: {chain_id},\n block: {block_n}',
        #              chain_id=chain_id, block_n=block_n)
        # await chain.start()
        logger.debug('chain prerequisite started')


class Prerequisites(StorySection):

    class ReqLabels(Enum):
        CHAIN = auto()
        USER_ETH_BALANCE = auto()

    def __init__(self, user_agent=None, **kwargs):
        super().__init__(user_agent=user_agent, **kwargs)
        self.interpreters = {
            self.ReqLabels.CHAIN: ChainReq(user_agent=user_agent),
        }

    def classify_prompt(self, prompt: list = None):
        """
        Classifies a natural language prompt in md-AST format as one of multiple predefined options.
        """
        assert prompt is not None
        text = get_prompt_text(prompt)
        text = text.lower().strip()
        if re.match(r'chain\b', text):
            return self.ReqLabels.CHAIN

    def get_interpreter_by_class(self, prompt_class=None) -> StepInterpreter:
        """
        Look for the interpreter of a specific prompt class.
        """
        return self.interpreters[prompt_class]

    async def __aenter__(self):
        """
        runs when prerequisite used in 'with' python construct
        """
        self.user_agent.chain = None
        await self.run()
        logger.debug('__aenter__ done')

    async def __aexit__(self, type, value, traceback):
        """
        runs on exiting a 'with' python construct
        """
        # Exception handling here
        chain = self.user_agent.chain
        if chain is not None:
            await chain.stop()
