from loguru import logger
from .prerequisites import Prerequisites
from .user_steps import UserSteps
from .expected_results import ExpectedResults
from .browser import UserAgent


async def log_browser_console_message(msg):
    values = []
    try:
        level = 'DEBUG'
        for arg in msg.args:
            values.append(await arg.json_value())
            browser_level = msg.type.upper()
            if browser_level == 'LOG':
                browser_level = 'DEBUG'
            level = logger.level(browser_level).name
        logger.opt(colors=True).log(
            level, '<bg #70A599>[Browser(Chrome) ({level})]</bg #70A599>: {s}',
            level=level,
            s=values)
    except Exception as e:
        logger.warning(
            'Error while parsing browser console messages: message {m}', m=e)


async def log_wallet_balance(page):
    # check status of mock wallet
    mwallet = await page.evaluate("() => window.ethereum")
    logger.debug("window.ethereum: {mw}", mw=(mwallet is not None))
    # check wallet balance at the beginning of step
    wbalance = await page.evaluate(
        """
            async () => {
                    const wallet = window.ethereum
                    const signer = window.ethereum?.signer
                    let balance = -1
                    if (wallet && signer) {
                        balance = await wallet.send(
                            'eth_getBalance',
                            [signer.address, 'latest']
                        )
                    }
                    return balance
                }
            """)
    logger.debug("user wallet balance: {b}", b=wbalance)


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
        passed = True
        errors = None
        async with Prerequisites(prompts=self.user_story.prerequisites) as reqs:
            await reqs.run()
            async with UserAgent() as user_agent:
                page = user_agent.page
                page.on("console", log_browser_console_message)
                # run user steps section
                logger.debug('user_agent: {ua}', ua=user_agent)
                user_steps = UserSteps(user_agent=user_agent,
                                       prompts=self.user_story.user_steps)
                await user_steps.run()
                await log_wallet_balance(page)
                # run expected results section
        async with ExpectedResults(
                prompts=self.user_story.expected_results) as expected_results:
            await expected_results.run()
            errors = expected_results.errors
            logger.debug('expected result errors: {e}', e=errors)
            if errors:
                passed = False
        return passed, errors
