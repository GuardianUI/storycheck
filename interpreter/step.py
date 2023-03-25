from abc import abstractmethod, ABC
from loguru import logger


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
