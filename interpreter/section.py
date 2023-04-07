from abc import abstractmethod, ABC
from .step import StepInterpreter


class StorySection(ABC):

    def __init__(self, prompts: list = None):
        assert prompts is not None
        self.prompts = prompts

    async def run(self):
        """
        Run all steps in this story section.
        """
        for p in self.prompts:
            prompt_class = self.classify_prompt(p)
            interpreter = self.get_interpreter_by_class(prompt_class)
            await interpreter.interpret_prompt(p)

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
        pass
