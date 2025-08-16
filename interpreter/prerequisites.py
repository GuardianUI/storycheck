from .section import StorySection
from .step import NotImplementedInterpreter, StepInterpreter, get_prompt_text, get_prompt_link
import re
from enum import Enum, auto
from loguru import logger
from .blockchain import LocalChain
from pprint import pformat as pf
from traceback import format_tb


class ReqStep(StepInterpreter):

    async def aexit(self):
        """
        Clean up any resources allocated for prerequisites
        """
        pass


class ChainReq(ReqStep):

    async def interpret_prompt(self, prompt):

        def get_kv(ast_prompt: list) -> str:
            """
            breaks up a prompt line in key, value pair
            for example if a is one of the prompts in the list
            >>> a='id : 12345'
            >>> f = re.search(r'(\w+\b)\s*[:= ]+\s*(\d+)', a, re.IGNORECASE)
            >>> f.group(0), f.group(1), f.group(2)
            ('id : 12345', 'id', '12345')
            """
            key = None
            value = None
            if ast_prompt['type'] == 'list_item':
                text = get_prompt_text(ast_prompt['children'])
                logger.debug(
                    "Splitting '{txt}' into key, value pair", txt=text)
                m = re.search(
                    r'(\w+\b)\s*[:= ]+\s*(.*)', text, re.IGNORECASE)
                k = m.group(1)
                # normalize key name
                key = k.strip().lower()
                value = m.group(2)
            return key, value

        logger.debug('chain prompt:\n {prompt}', prompt=pf(prompt))
        chain_params = prompt[1]['children']
        logger.debug(
            'chain params prompt:\n {prompt}', prompt=pf(chain_params))
        chain_id = '1'
        block_n = None
        rpc_url = None
        for chain_param in chain_params:
            key, value = get_kv(chain_param)
            if key == 'rpc':
                rpc_url = get_prompt_link(chain_param['children'])
                logger.debug(f"Custom RPC parsed for interception: {rpc_url}")                
            elif key == 'id':
                chain_id = value
            elif key == 'block':
                block_n = value
            else:
                raise ValueError(
                    f"Invalid Prerequisite Chain parameter: {key}")
        chain = LocalChain(chain_id=chain_id,
                           block_n=block_n, rpc_url=rpc_url)
        # set chain in session context
        self.chain = chain
        logger.debug(f"LocalChain initialized with chain_id={chain_id}, block_n={block_n}, rpc_url={rpc_url}")        
        await chain.start()
        logger.debug('chain prerequisite prepared.')

    async def aexit(self):
        """
        Clean up any resources allocated for prerequisites
        """
        if self.chain is not None:
            await self.chain.stop()
            logger.debug('Local chain stopped.')


class Prerequisites(StorySection):

    class ReqLabels(Enum):
        CHAIN = auto()
        USER_ETH_BALANCE = auto()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.interpreters = {
            self.ReqLabels.CHAIN: ChainReq(),
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
        return self.interpreters.get(prompt_class, NotImplementedInterpreter())

    async def __aenter__(self):
        """
        runs when prerequisite used in 'with' python construct
        """
        return self

    async def __aexit__(self, exception_type, exception_value, exception_traceback):
        """
        runs on exiting a 'with' python construct
        """
        # Exception handling here
        if exception_type or exception_value:
            logger.error('Exception\n type: {t},\n value: {v}, \n traceback: {tb}',
                         t=exception_type,
                         v=exception_value,
                         tb=pf(format_tb(exception_traceback)))
        for label, interpreter in self.interpreters.items():
            await interpreter.aexit()
