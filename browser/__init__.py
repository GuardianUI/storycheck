from playwright.async_api import async_playwright
from loguru import logger
from pathlib import Path


class UserAgent:

    def __init__(self):
        # shared session object during a story check run
        self.session = dict()

    async def start(self):
        logger.debug("Starting playwright user agent...")
        self.playwright = await async_playwright().start()
        chromium = self.playwright.chromium
        pixel5 = self.playwright.devices["Pixel 5"]
        self.browser = await chromium.launch()
        browser_context = await self.browser.new_context(**pixel5, record_video_dir="results/videos/")
        here = Path(__file__).parent
        fname = here / "mock_wallet/provider/provider.js"
        # TODO: find a way to pass prerequisites to js init script
        await browser_context.add_init_script(path=fname)
        self.page = await browser_context.new_page()
        logger.debug("Started playwright user agent.")

    async def stop(self):
        await self.browser.close()
        await self.playwright.stop()
        logger.debug("Stopped playwright.")
