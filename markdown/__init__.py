"""
Parse markdown formatted user story into structured executable sections:
- prerequisites
- user steps
- expected results
"""
from dataclasses import dataclass
import mistune
from loguru import logger


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

    def get_section(self, ast: list = None, title=None) -> (list, list):
        assert ast is not None
        assert title is not None
        section_found = False
        ast_tail = ast
        prerequisites = []
        for (index, item) in enumerate(ast):
            # logger.debug(item)
            if item['type'] == 'heading' and item['children'][0]['type'] == 'text' \
                    and item['children'][0]['raw'].lower() == title.lower():
                section_found = True
                ast_tail = ast_tail[index+1:]
                # logger.debug('Section found: {s}', s=title)
                break
        # logger.debug("section_found: {section_found}",
                #  section_found=section_found)
        if section_found:
            list_found = False
            # extract list items for this sections
            for (index, item) in enumerate(ast_tail):
                if item['type'] == 'list':
                    list_found = True
                    ast_tail = ast_tail[index+1:]
                    break
            # logger.debug("list_found: {list_found}",
                    #  list_found=list_found)
            if list_found:
                for index2, child in enumerate(item['children']):
                    if child['type'] == 'list_item':
                        prerequisites.append(child['children'])
        return (prerequisites, ast_tail)

    def parse(self, story: str) -> UserStory:
        # get abstract syntax tree (AST)
        ast = self.markdown_parser(story)
        # pretty_dict = pprint.pformat(ast, indent=4)
        # logger.debug("Markdown AST\n {dict}", dict=pretty_dict)
        prerequisites, ast_tail = self.get_section(
            ast=ast, title='Prerequisites')
        # pretty_dict = pprint.pformat(prerequisites, indent=4)
        # logger.debug(
        #     "Prerequisites\n {dict}, AST tail: {ast_tail}", dict=pretty_dict, ast_tail=ast_tail)
        user_steps, ast_tail = self.get_section(
            ast=ast_tail, title='User Steps')
        # pretty_dict = pprint.pformat(user_steps, indent=4)
        # logger.debug(
        #     "User Steps\n {dict}, AST tail: {ast_tail}", dict=pretty_dict, ast_tail=ast_tail)
        expected_results, ast_tail = self.get_section(
            ast=ast, title='Expected Results')
        # pretty_dict = pprint.pformat(expected_results, indent=4)
        # logger.debug(
        #     "Expected Results\n {dict}, AST tail: {ast_tail}", dict=pretty_dict, ast_tail=ast_tail)
        user_story = UserStory(prerequisites, user_steps, expected_results)
        # pretty_dict = pprint.pformat(user_story, indent=4)
        # logger.debug("UserStory\n {dict}", dict=pretty_dict)
        logger.debug('User Story Parsed')
        return user_story