from playwright.async_api import async_playwright
from loguru import logger
from pathlib import Path
from eth_account import Account
import json
import os
import asyncio


def generate_private_key():
    # Generate a new Ethereum account
    account = Account.create()

    # Get the mnemonic phrase
    key = account.key.hex()

    return key


class UserAgent:

    def __init__(self, prerequisites):
        assert prerequisites is not None
        self.prerequisites = prerequisites
        # shared session object during a story check run
        self.session = dict()
        results_dir = os.environ.get("GUARDIANUI_RESULTS_PATH", "results/")
        self.results_dir = Path(results_dir)

    async def hook_rpc_router(self):
        # rewrite RPC requests to local evm / anvil fork
        prereqs = self.prerequisites
        chain_step = prereqs.interpreters[prereqs.ReqLabels.CHAIN]
        chain = chain_step.chain
        remote_rpc_url = chain.rpc_url
        local_fork_rpc_url = chain.ANVIL_RPC

        async def reroute_rpc(route):
            orig_url = route.request.url
            logger.debug("""Rerouting RPC request:
                original url: {original_url}
                new url.    : {new_url}
                """,
                         original_url=orig_url,
                         new_url=local_fork_rpc_url)
            try:
                logger.debug("""Fetching new url: {new_url}
                    """,
                             new_url=local_fork_rpc_url)
                response = await route.fetch(url=local_fork_rpc_url)
                logger.debug("""Fetched new url: {new_url}
                    OK: {ok}
                    """,
                             new_url=local_fork_rpc_url,
                             ok=response.ok)
                # json = await response.json()
                await route.fulfill(response=response)
            except Exception as e:
                logger.exception(
                    "Exception while rerouting RPC request.")
                # logger.exception(
                #     "Exception setting up RPC reroute rule. Error: {e}", e=e)
                await route.abort()

        # Runs last.
        await self.page.route(remote_rpc_url, reroute_rpc)
        logger.info(
            f"Set RPC reroute rule from {remote_rpc_url} to {local_fork_rpc_url}")

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

        here = Path(__file__).parent
        fname = here / "mock_wallet/provider/provider.js"
        with open(Path(fname), "r") as file:
            init_script = file.read().replace(
                "'__GUARDIANUI_MOCK__PRIVATE_KEY'", f"'{mnemonic}'")

        await self.browser_context.expose_binding("__guardianui_hook_rpc_router", self.hook_rpc_router)

        # Pass story prerequisites to mock wallet via js init script
        await self.browser_context.add_init_script(init_script)
        logger.info("Added browser context init script.")

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

        # remember pending tasks before this scope
        self.previous_tasks = asyncio.all_tasks()

        logger.debug("Started playwright user agent.")
        return self

    async def _cancel_pending_tasks(self):
        """
        Cancel in-scope pending tasks.
        For example pending network requests initiated from within the web app.
        """
        all_tasks = asyncio.all_tasks()
        inscope_tasks = all_tasks - self.previous_tasks
        logger.debug('Cleaning up unfinished browser tasks: {tasks_n}',
                     tasks_n=len(inscope_tasks))
        for task in inscope_tasks:
            task.cancel()
        logger.debug('Browser tasks cleaned up.')

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
        # wait for all pending async tasks to complete
        await self._cancel_pending_tasks()
        await self.browser_context.tracing.stop(path=self.results_dir / "trace.zip")
        await self.browser_context.close()
        await self.browser.close()
        await self.playwright.stop()
        logger.debug("Stopped playwright.")
