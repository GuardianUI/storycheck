import asyncio
from loguru import logger
from aiohttp import ClientSession


class LocalChain:
    """
    Wrapper around a local blockchain instance managed via Foundry Anvil
    """

    def __init__(self, chain_id='1', block_n=None, rpc_url=None):
        assert isinstance(chain_id, str)
        self.chain_id = chain_id
        self.block_n = block_n
        self.rpc_url = rpc_url

    anvil_proc = None

    # listen on all IP addresses assigned to this host
    ANVIL_HOST = '0.0.0.0'
    ANVIL_PORT = '8545'

    RPC_URLs = {
        # ETH mainnet
        '1': 'https://eth-mainnet.g.alchemy.com/v2/0Uk2xg_qksy5OMviwu8MOHMHVJX4mQ1D',
        # Goerli testnet
        '5': 'https://eth-goerli.g.alchemy.com/v2/3HpUm27w8PfGlJzZa4jxnxSYs9vQN7FZ',
        # Arbitrum
        '42161': 'https://arb-mainnet.g.alchemy.com/v2/Kjt13n8OuVVCBqxIGMGYuwgbnLzfh1U6',
        # zkSync Era Mainnet
        '324': 'https://mainnet.era.zksync.io',
        # zkSync Era Testnet
        '280': 'https://testnet.era.zksync.dev'
    }

    async def start(self):
        # Create the subprocess; redirect the standard output
        # into a pipe.
        chain_args = ["--chain-id", self.chain_id,
                      "--host", self.ANVIL_HOST,
                      "--port", self.ANVIL_PORT,
                      "--config-out", "results/anvil-out.json",
                      "--gas-price", "0",
                      "--base-fee", "0"
                      #   "--no-cors"
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
                Please provide one via explicit RPC parameter.
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
            # "--no-mining",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        logger.debug(
            'Started anvil with process ID: {process}', process=self.anvil_proc.pid)
        # read a line of output from the anvil process
        anvil_output = await self.anvil_proc.stdout.readuntil(separator=b'Listening')
        logger.debug('[Anvil stdout]: {l}', l=anvil_output.decode())
        # wait for anvil RPC endpoint to become available
        anvil_url = f"http://{self.ANVIL_HOST}:{self.ANVIL_PORT}"
        async with ClientSession() as session:
            async with session.post(anvil_url) as response:
                # logger.debug('Anvil server response: {r}', r=response)
                if response.status == 200:
                    logger.debug(
                        'Anvil RPC endpoint is now available at: {url}', url=anvil_url)
                else:
                    # rtext = await response.text()
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
        logger.debug(
            'Stopping anvil. Process: {process}', process=self.anvil_proc.pid)
        self.anvil_proc.terminate()
        try:
            self.background_tasks.cancel()
            # wait 15 seconds for the process to terminate
            await asyncio.wait_for(self.anvil_proc.communicate(), timeout=3.0)
        except asyncio.subprocess.TimeoutExpired:
            # if process did not shutdown nicely, force kill it
            await self.anvil_proc.kill()
            await asyncio.wait_for(self.anvil_proc, timeout=1.0)
        finally:
            logger.debug(
                'Stopped anvil.')
