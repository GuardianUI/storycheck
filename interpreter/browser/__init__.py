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

    def get_chain(self):
        """
        Return chain information from the context of story prerequisites
        """
        prereqs = self.prerequisites
        chain_step = prereqs.interpreters[prereqs.ReqLabels.CHAIN]
        chain = chain_step.chain
        return chain

    def get_local_fork_rpc_url(self):
        chain = self.get_chain()
        return chain.ANVIL_RPC

    def get_remote_rpc_url(self):
        chain = self.get_chain()
        return chain.rpc_url

    async def hook_rpc_router(self, source):
        # rewrite RPC requests to local evm / anvil fork
        local_fork_rpc_url = self.get_local_fork_rpc_url()
        remote_rpc_url = self.get_remote_rpc_url()

        async def reroute_rpc(route):
            orig_url = route.request.url
            new_url = local_fork_rpc_url
            try:
                request_json = route.request.post_data_json
            except Exception:
                request_json = None
            logger.debug("""Rerouting RPC request:
                original url: {original_url}
                new url.    : {new_url}
                method: {method}
                request json: {request_json}
                """,
                         original_url=orig_url,
                         new_url=new_url,
                         method=route.request.method,
                         request_json=request_json)
            try:
                # continue_ mandates same protocol: https != http
                # await route.continue_(url=new_url)
                response = await route.fetch(url=new_url)
                try:
                    response_json = await response.json()
                except Exception:
                    response_json = None
                logger.opt(colors=True).debug("""<bg #70A599>[RPC Response]</bg #70A599>:
                    url: {url}
                    method: {method}
                    request json: {request_json}

                    OK: {ok}

                    response status: {response_status},
                    response json: {response_json}
                    """,
                                              url=new_url,
                                              request_json=request_json,
                                              method=route.request.method,
                                              ok=response.ok,
                                              response_status=response.status,
                                              response_json=response_json
                                              )
                await route.fulfill(response=response)
            except Exception as e:
                logger.exception(
                    "Exception during routing RPC. Error: {e}", e=e)
                await route.abort()
            finally:
                logger.debug("""Finished rerouting RPC request:
                    original url: {original_url}
                    new url.    : {new_url}
                    method: {method}
                    request json: {request_json}
                    """,
                             original_url=orig_url,
                             new_url=new_url,
                             method=route.request.method,
                             request_json=request_json)

        # Runs last.
        # logger.debug(
        #     'source browser context == self browser context: {bc}', bc=source['browserContext'] == self.browser_context)
        await self.browser_context.route(remote_rpc_url, reroute_rpc)
        logger.info(
            f"Activated RPC reroute rule in new page context: from {remote_rpc_url} to {local_fork_rpc_url}")

    async def __aenter__(self):
        """
        runs when prerequisite used in 'async with' python construct
        """
        logger.debug("Starting playwright user agent...")
        self.playwright = await async_playwright().start()
        chromium = self.playwright.chromium
        # set up browser to emulate a mobile device
        pixel_mobile = self.playwright.devices["Pixel 7"]
        self.browser = await chromium.launch(
            traces_dir=self.results_dir,
            slow_mo=200)  # slow down (ms) so devs can see what's going on
        # expose mock private key in browser context for wallet initialization
        mnemonic = generate_private_key()
        self.browser_context = await self.browser.new_context(
            **pixel_mobile,
            record_video_dir=self.results_dir / "videos/",
            # Disable CORS checks in order to allow use of mock wallet
            bypass_csp=True
        )

        here = Path(__file__).parent
        fname = here / "mock_wallet/provider/provider.js"
        with open(Path(fname), "r") as file:
            init_script = file.read()

        init_script = init_script.replace(
            "'__GUARDIANUI_MOCK__PRIVATE_KEY'", f"'{mnemonic}'")
        # remote_rpc_url = self.get_remote_rpc_url()
        local_fork_rpc_url = self.get_local_fork_rpc_url()
        # init_script = init_script.replace(
        #     "'__GUARDIANUI_MOCK__RPC'", f"'{remote_rpc_url}'")
        # Use local fork RPC URL for mock wallet
        init_script = init_script.replace(
            "'__GUARDIANUI_MOCK__RPC'", f"'{local_fork_rpc_url}'")
        # chain = self.get_chain()
        # init_script = init_script.replace(
        #     "'__GUARDIANUI_MOCK__CHAIN_ID'", f"{chain.chain_id}")

        await self.browser_context.expose_binding("__guardianui_hook_rpc_router",
                                                  self.hook_rpc_router)

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
        snapshot_filepath = self.results_dir / "tx_log_snapshot.json"
        with open(snapshot_filepath, "w") as outfile:
            logger.debug("Writing wallet tx snapshot to {f}",
                         f=self.results_dir / "tx_log_snapshot.json")
            logger.debug("Wallet tx snapshot value:\n {wts}",
                         wts=self.wallet_tx_snapshot)
            json.dump(self.wallet_tx_snapshot, outfile)
        if exception_type != asyncio.exceptions.CancelledError:
            await self.browser_context.tracing.stop(path=self.results_dir / "trace.zip")
            await self.browser_context.close()
            await self.browser.close()
            await self.playwright.stop()
        # wait for all pending async tasks to complete
        # await self._cancel_pending_tasks()
        logger.debug("Stopped playwright.")
