from loguru import logger
from PIL import Image
from abc import abstractmethod, ABC
from prerequisites import Prerequisites
from user_steps import UserSteps
from expected_results import ExpectedResults


async def log_browser_console_message(msg):
    values = []
    for arg in msg.args:
        values.append(await arg.json_value())
    try:
        level = logger.level(msg.type.upper()).name
    except ValueError:
        level = 'DEBUG'
    logger.log(
        level, 'Browser console[{level}]: {s}', level=level, s=values)


def xyxy(point=None, page=None):
    assert point is not None
    assert page is not None
    # Convert predicted point in [0..1] range coordinates to viewport coordinates
    vpSize = page.viewport_size
    cpTranslated = {
        'x': int(point['x'] * vpSize['width']),
        'y': int(point['y'] * vpSize['height'])
    }
    return cpTranslated


class StepInterpreter(ABC):
    @abstractmethod
    def interpret_prompt(self, prompt):
        """
        Interpret in computer code the intention of the natural language input prompt.
        """
        pass


class StorySection(ABC):

    def __init__(self, user_agent=None, prompts: list = None):
        assert user_agent is not None
        assert prompts is not None
        self.prompts = prompts
        self.user_agent = user_agent

    def run(self):
        """
        Run all steps in this story section.
        """
        for p in self.prompts:
            prompt_class = self.classify_prompt(p)
            interpreter = self.get_interpreter_by_class(prompt_class)
            interpreter.interpret_prompt(p)

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


class StoryInterpreter:
    """
    Given a populated UserStory object, it iterates over the list of
    sections and interprets each step per section.
    """

    user_story = None

    def __init__(self, user_story=None,
                 user_agent=None):
        assert user_story is not None, 'user_story should be a populated object'
        assert user_agent is not None, \
            'user_agent should be a an initialized browser driver object'
        self.user_story = user_story
        self.user_agent = user_agent
        # init ai model

    def run(self):
        page = self.user_agent.page
        page.on("console", log_browser_console_message)

        prerequisites = Prerequisites(user_agent=self.user_agent,
                                      prompts=self.user_story.prerequisites)
        prerequisites.run()
        user_steps = UserSteps(user_agent=self.user_agent,
                               prompts=self.user_story.user_steps)
        user_steps.run()
        expected_results = ExpectedResults(
            user_agent=self.user_agent, prompts=self.user_story.expected_results)
        expected_results.run()
        # TODO: implement proper result object with success and error properties
        result = 'Success'
        return result
