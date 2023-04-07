from loguru import logger
from .prerequisites import Prerequisites
from .user_steps import UserSteps
from .expected_results import ExpectedResults
from .browser import UserAgent


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


class StoryInterpreter:
    """
    Given a populated UserStory object, it iterates over the list of
    sections and interprets each step per section.
    """

    user_story = None

    def __init__(self, user_story=None):
        assert user_story is not None, 'user_story should be a populated object'
        self.user_story = user_story
        # init ai model

    async def run(self):
        async with Prerequisites(prompts=self.user_story.prerequisites) as reqs:
            # run prereq steps
            await reqs.run()
            async with UserAgent() as user_agent:
                page = user_agent.page
                page.on("console", log_browser_console_message)
                # run user steps section
                # user_steps = UserSteps(user_agent=self.user_agent,
                #                        prompts=self.user_story.user_steps)
                # await user_steps.run()
                pass

            # # run expected results section
            # expected_results = ExpectedResults(
            #     user_agent=self.user_agent, prompts=self.user_story.expected_results)
            # await expected_results.run()
            # page = self.user_agent.page
            # # get mock wallet address
            # address = await page.evaluate("() => window.ethereum.signer.address")
            # logger.info(
            #     'user mock wallet account address: {address}', address=address)
            # # check mock wallet balance
            # balance = await page.evaluate(
            #     "(address) => window.ethereum.provider.send('eth_getBalance',[address, 'latest'])",
            #     address)
            # logger.info(
            #     'user mock wallet account balance: {balance}', balance=balance)
            # TODO: implement proper result object with success and error properties
            result = 'Success'
        return result
