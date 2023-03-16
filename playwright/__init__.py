from playwright.async_api import async_playwright


class StoryRunner:

    def __init__(self):
        pass

    def run_story(self, user_story):
        """
        Parse and execute a user story in markdown and natural language format.
        """
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch()
        chromium = playwright.chromium
        pixel5 = playwright.devices["Pixel 5"]
        browser = await chromium.launch()
        browser_context = await browser.new_context(**pixel5)
        # in your playwright script, assuming the preload.js file is in same directory.
        await browser_context.add_init_script(path="mock_wallet/provider/provider.js")
        page = await browser_context.new_page()
        await page.goto("http://whatsmyuseragent.org/")
        await page.screenshot(path="example.png")
        await browser.close()
        await playwright.stop()
