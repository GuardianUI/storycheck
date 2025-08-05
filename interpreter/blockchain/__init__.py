import asyncio
from loguru import logger
from aiohttp import ClientSession, ClientConnectionError
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

class LocalChain:
    alchemy_key = os.environ.get('ALCHEMY_API_KEY', 'YOUR_ALCHEMY_API_KEY')
    ANVIL_START_TIMEOUT = 10  # seconds to wait for anvil to start
    """
    Wrapper around a local blockchain instance managed via Foundry Anvil
    """

    def __init__(self, chain_id='1', block_n=None, rpc_url=None):
        assert isinstance(chain_id, str)
        self.chain_id = chain_id
        self.block_n = block_n
        self.rpc_url = rpc_url
        results_dir = os.environ.get("GUARDIANUI_RESULTS_PATH", "results/")
        self.results_dir = Path(results_dir)

    anvil_proc = None

    ANVIL_POLL_HOST = '127.0.0.1'
    # listen on all IP addresses assigned to this host
    ANVIL_HOST = '0.0.0.0'
    ANVIL_PORT = '8545'
    ANVIL_RPC = 'http://127.0.0.1:8545'

    RPC_URLs = {
        # ETH mainnet
        '1': f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}",  # Uses ALCHEMY_API_KEY from .env.local.
        # Goerli testnet
        '5': f"https://eth-goerli.g.alchemy.com/v2/{alchemy_key}",  # Deprecated; use Sepolia (Id 11155111). Uses ALCHEMY_API_KEY from .env.local.
        # Sepolia testnet
        '11155111': f"https://eth-sepolia.g.alchemy.com/v2/{alchemy_key}",  # Uses ALCHEMY_API_KEY from .env.local.
        # Arbitrum
        '42161': f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}",  # Uses ALCHEMY_API_KEY from .env.local.
        # Optimism
        '10': f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_key}",  # Uses ALCHEMY_API_KEY from .env.local.
        # zkSync Era Mainnet
        '324': f"https://zksync-mainnet.g.alchemy.com/v2/{alchemy_key}",  # Uses ALCHEMY_API_KEY from .env.local.
        # zkSync Era Sepolia Testnet
        '300': f"https://zksync-sepolia.g.alchemy.com/v2/{alchemy_key}",  # Uses ALCHEMY_API_KEY from .env.local.
        # zkSync Era Testnet
        '280': f"https://zksync-testnet.g.alchemy.com/v2/{alchemy_key}",  # Uses ALCHEMY_API_KEY from .env.local.
    }

    async def start(self):
        # Create the subprocess; redirect the standard output
        # into a pipe.
        chain_args = ["--chain-id", self.chain_id,
                      "--host", self.ANVIL_HOST,
                      "--port", self.ANVIL_PORT,
                      "--config-out", self.results_dir / "anvil-out.json",
                      "--gas-price", "0",
                      "--base-fee", "0"
                      ]
        if self.block_n is not None:
            assert isinstance(self.block_n, str)
            block_args = ["--fork-block-number", self.block_n]
        else:
            block_args = []
        if self.rpc_url is None:
            self.rpc_url = self.RPC_URLs.get(self.chain_id)
            assert self.rpc_url is not None, \
                f"""
                No known RPC URL for Chain ID: {self.chain_id}.
                Please provide one via explicit RPC parameter in the story file.
                """
        rpc_args = ["--fork-url", self.rpc_url]

        logger.debug(
            'Starting anvil EVM Fork with args: {chain} {block} {rpc}',
            chain=chain_args,
            block=block_args,
            rpc=rpc_args)
        self.anvil_proc = await asyncio.create_subprocess_exec(
            "anvil",
            *chain_args,
            *block_args,
            *rpc_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        logger.debug(
            'Started anvil with process ID: {process}', process=self.anvil_proc.pid)
        # wait for anvil RPC endpoint to become available
        anvil_url = f"http://{self.ANVIL_POLL_HOST}:{self.ANVIL_PORT}"
        async with ClientSession() as session:
            # Poll until anvil responds or timeout
            start_time = asyncio.get_event_loop().time()
            while True:
                try:
                    async with session.post(anvil_url) as response:
                        if response.status == 200:
                            break
                    logger.debug("Anvil polling attempt successful at {url}", url=anvil_url)
                except (ConnectionError, ClientConnectionError):
                    if asyncio.get_event_loop().time() - start_time > self.ANVIL_START_TIMEOUT:
                        raise ConnectionError(f"Anvil failed to start within {self.ANVIL_START_TIMEOUT} seconds")
                    await asyncio.sleep(0.5)
            async with session.post(anvil_url) as response:
                if response.status == 200:
                    logger.debug(
                        'Anvil RPC endpoint is now available at: {url}', url=anvil_url)
                else:
                    raise ConnectionError(
                        f'Failed to start anvil. Server status response: {response.status}')
        # capture anvil output in the unified logger

        async def anvil_log(prefix='', stream=None):
            assert stream is not None
            if prefix == 'stderr':
                level = 'WARNING'
            else:
                level = 'DEBUG'
            while not stream.at_eof():
                line = await stream.readline()
                logger.opt(colors=True).log(level,
                                            '<bg #8E866B>[EVM(Anvil) ({pref})]</bg #8E866B>: {l}',
                                            pref=prefix, l=line.decode())

        async def background_tasks():
            await asyncio.gather(
                anvil_log(prefix='stdout', stream=self.anvil_proc.stdout),
                anvil_log(prefix='stderr', stream=self.anvil_proc.stderr)
            )

        self.background_tasks = asyncio.create_task(background_tasks())

    async def stop(self):
        # try to stop the process nicely
        if self.anvil_proc is not None:
            logger.debug(
                'Stopping anvil. Process: {process}', process=self.anvil_proc.pid)
            self.anvil_proc.terminate()
            try:
                if hasattr(self, 'background_tasks'):
                    self.background_tasks.cancel()
                # wait 15 seconds for the process to terminate
                await asyncio.wait_for(self.anvil_proc.communicate(),
                                       timeout=3.0)
            except asyncio.TimeoutError:
                # if process did not shutdown nicely, force kill it
                await self.anvil_proc.kill()
                await asyncio.wait_for(self.anvil_proc, timeout=1.0)
            finally:
                logger.debug(
                    'Stopped anvil.')