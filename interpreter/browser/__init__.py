from playwright.async_api import async_playwright
from loguru import logger
from pathlib import Path


class UserAgent:

    def __init__(self):
        # shared session object during a story check run
        self.session = dict()

    async def __aenter__(self):
        """
        runs when prerequisite used in 'async with' python construct
        """
        logger.debug("Starting playwright user agent...")
        self.playwright = await async_playwright().start()
        chromium = self.playwright.chromium
        pixel5 = self.playwright.devices["Pixel 5"]
        self.browser = await chromium.launch(
            traces_dir="results/",
            slow_mo=200)  # slow down (ms) so devs can see what's going on
        self.browser_context = await self.browser.new_context(
            **pixel5,
            record_video_dir="results/videos/",
            # Disable CORS checks in order to allow use of mock wallet
            bypass_csp=True,
        )
        here = Path(__file__).parent
        fname = here / "mock_wallet/provider/provider.js"
        # TODO: find a way to pass prerequisites to js init script
        await self.browser_context.add_init_script(path=fname)
        await self.browser_context.tracing.start(
            name='storycheck-trace',
            screenshots=True,
            snapshots=True,
            sources=True,
            title='StoryCheck-Trace')
        self.page = await self.browser_context.new_page()
        logger.debug("Started playwright user agent.")
        return self

    async def __aexit__(self, exception_type, exception_value, exception_traceback):
        """
        runs on exiting a 'with' python construct
        """
        # Exception handling here
        if exception_type or exception_value:
            logger.error('Exception\n type: {t},\n value: {v}, \n traceback: {tb}',
                         t=exception_type,
                         v=exception_value,
                         tb=exception_traceback)
        await self.browser_context.tracing.stop(path="results/trace.zip")
        await self.browser_context.close()
        await self.browser.close()
        await self.playwright.stop()
        logger.debug("Stopped playwright.")
