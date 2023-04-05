from abc import abstractmethod, ABC
from loguru import logger


def get_prompt_text(ast_prompt: list) -> str:
    """
    Helper method for pulling text value from a parsed MD AST structure
    """
    for c in ast_prompt[0]['children']:
        if c['type'] == 'text':
            return c['text']


class StepInterpreter(ABC):

    def __init__(self, user_agent=None):
        assert user_agent is not None
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
