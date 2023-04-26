from .section import StorySection
from .step import StepInterpreter, NotImplementedInterpreter


# check if snapshot saved
# if snapshot saved, compare to snapshot from current run
# else save current snapshot alongside story for future comparison
# os.environ.get("GUARDIANUI_STORY_PATH")

class ExpectedResults(StorySection):

    class StepInterpreter(StepInterpreter):
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
        return NotImplementedInterpreter(user_agent=self.user_agent)
