from abc import abstractmethod, ABC


class StepInterpreter(ABC):

    def __init__(self, user_agent=None):
        assert user_agent is not None
        self.user_agent = user_agent

    @abstractmethod
    async def interpret_prompt(self, prompt=None, **kwargs):
        """
        Interpret in computer code the intention of a natural language input prompt.

        Parameters:
          prompt(str): natural language prompt
        """
        pass
