from . import StorySection


class Prerequisites(StorySection):

    class StepInterpreter(StorySection.StepInterpreter):
        def interpret_prompt(self):
            """
            Interpret in computer code the intention of the natural language input prompt.
            """
            pass

    def classify_prompt(self, prompt: str = None):
        """
        Classifies a natural language prompt as one of multiple predefined options.
        """
        pass

    def get_interpreter_by_class(self, prompt_class=None) -> StepInterpreter:
        """
        Look for the interpreter of a specific prompt class.
        """
        pass
