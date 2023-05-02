from playwright.async_api import async_playwright
from loguru import logger
from pathlib import Path
from eth_account import Account
import json
import os


def generate_private_key():
    # Generate a new Ethereum account
    account = Account.create()

    # Get the mnemonic phrase
    key = account.key.hex()

    return key


class UserAgent:

    def __init__(self):
        # shared session object during a story check run
        self.session = dict()
        results_dir = os.environ.get("GUARDIANUI_RESULTS_PATH", "results/")
        self.results_dir = Path(results_dir)

    async def __aenter__(self):
        """
        runs when prerequisite used in 'async with' python construct
        """
        logger.debug("Starting playwright user agent...")
        self.playwright = await async_playwright().start()
        chromium = self.playwright.chromium
        pixel5 = self.playwright.devices["Pixel 5"]
        self.browser = await chromium.launch(
            traces_dir=self.results_dir,
            slow_mo=200)  # slow down (ms) so devs can see what's going on
        # expose mock private key in browser context for wallet initialization
        mnemonic = generate_private_key()
        self.browser_context = await self.browser.new_context(
            **pixel5,
            record_video_dir=self.results_dir / "videos/",
            # Disable CORS checks in order to allow use of mock wallet
            bypass_csp=True
        )

        # def mockMnemonic():
        #     return mnemonic
        # await self.browser_context.expose_function("__mockMnemonic", mockMnemonic)
        here = Path(__file__).parent
        fname = here / "mock_wallet/provider/provider.js"
        with open(Path(fname), "r") as file:
            init_script = file.read().replace(
                "'__GUARDIANUI_MOCK__PRIVATE_KEY'", f"'{mnemonic}'")

        # Pass story prerequisites to mock wallet via js init script
        await self.browser_context.add_init_script(init_script)

        self.wallet_tx_snapshot = []

        def log_wallet_tx(tx):
            logger.debug("Logging write tx to story snapshot:\n {wtx}", wtx=tx)
            self.wallet_tx_snapshot.append(tx)

        # Capture all wallet write transactions in a story scoped snapshot
        await self.browser_context.expose_function("__guardianui__logTx", log_wallet_tx)

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
        with open(self.results_dir / "tx_log_snapshot.json", "w") as outfile:
            json.dump(self.wallet_tx_snapshot, outfile)

        await self.browser_context.tracing.stop(path=self.results_dir / "trace.zip")
        await self.browser_context.close()
        await self.browser.close()
        await self.playwright.stop()
        logger.debug("Stopped playwright.")
