# File: interpreter/__init__.py
from loguru import logger
from .prerequisites import Prerequisites
from .user_steps import UserStepsSection
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

async def log_network_request(request):
    """
    Log network requests via XHR or fetch
    """
    if request.method == 'POST':
        try:
            request_json = request.post_data_json
        except Exception:
            request_json = None
        logger.opt(colors=True).debug("""<bg #70A599>[Browser POST request]</bg #70A599>:
            url: {url}
            request json: {request_json}
            """,
                                      url=request.url,
                                      request_json=request_json
                                      )

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
        # Scope prerequisites around the entire story execution to ensure setup (e.g., chain fork)
        # persists during user steps and expected results, then cleans up afterward.
        # This aligns with prerequisites' purpose: hold true only for the scope of step execution.        
        async with Prerequisites(prompts=self.user_story.prerequisites) as reqs:
            await reqs.run()
            async with UserAgent(reqs) as user_agent:
                page = user_agent.page
                page.on("console", log_browser_console_message)
                page.on("request", log_network_request)
                # run user steps section
                logger.debug('user_agent: {ua}', ua=user_agent)
                user_steps = UserStepsSection(user_agent=user_agent,
                                            prompts=self.user_story.user_steps)
                await user_steps.run()
                async with ExpectedResults(
                    user_agent=user_agent, prompts=self.user_story.expected_results
                ) as expected_results:
                    await expected_results.run()
                errors = [entry['errors'] for entry in expected_results.errors]
                logger.debug('expected result errors: {e}', e=errors)
                if errors:
                    passed = False
        return passed, errors