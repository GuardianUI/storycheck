"""
Parse markdown formatted user story into structured executable sections:
- prerequisites
- user steps
- expected results
"""
from dataclasses import dataclass
import mistune
from loguru import logger
import pprint


@dataclass
class UserStory:
    """
    Typed data structure for a user story
    """
    prerequisites: list()
    user_steps: list()
    expected_results: list()


class StoryParser:
    """
    Markdown parser for user stories.
    Parses markdown text to a UserStory structure.
    """

    markdown_parser = None

    def __init__(self):
        self.markdown_parser = mistune.create_markdown(
            renderer='ast', plugins=['url'])

    def parse(self, story: str) -> UserStory:
        ast = self.markdown_parser(story)
        pretty_dict = pprint.pformat(ast, indent=4)
        logger.debug("\n {dict}", dict=pretty_dict)
        # TODO: map ast to lists
        prerequisites = []
        user_steps = []
        expected_results = []
        user_story = UserStory(prerequisites, user_steps, expected_results)
        return user_story
