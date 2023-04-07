import asyncio
from loguru import logger
from aiohttp import ClientSession, ClientTimeout


class LocalChain:
    """
    Wrapper around a local blockchain instance managed via Foundry Anvil
    """

    def __init__(self, chain_id='1', block_n=None):
        assert isinstance(chain_id, str)
        self.chain_id = chain_id
        self.block_n = block_n

    anvil_proc = None

    RPC_URLs = {
        '1': 'https://eth-mainnet.g.alchemy.com/v2/0Uk2xg_qksy5OMviwu8MOHMHVJX4mQ1D',
        '42161': 'https://arb-mainnet.g.alchemy.com/v2/Kjt13n8OuVVCBqxIGMGYuwgbnLzfh1U6'
    }

    async def start(self):
        # Create the subprocess; redirect the standard output
        # into a pipe.
        chain_args = ["--chain-id", self.chain_id,
                      "--fork-url", self.RPC_URLs[self.chain_id]]
        if self.block_n is not None:
            assert isinstance(self.block_n, str)
            block_args = ["--fork-block-number", self.block_n]
        else:
            block_args = []
        logger.debug(
            'Starting anvil EVM Fork with args: {chain} {block}',
            chain=chain_args,
            block=block_args)
        self.anvil_proc = await asyncio.create_subprocess_exec(
            "anvil",
            *chain_args,
            *block_args,
            # "--no-mining",
            stdout=asyncio.subprocess.PIPE
        )
        logger.debug(
            'Started anvil with process ID: {process}', process=self.anvil_proc.pid)
        # read a line of output from the anvil process
        anvil_output = await self.anvil_proc.stdout.readuntil(separator=b'Listening on 127.0.0.1:8545\n')
        logger.debug('Anvil: {l}', l=anvil_output.decode())
        # wait for anvil RPC endpoint to become available
        anvil_url = "http://127.0.0.1:8545"
        async with ClientSession() as session:
            async with session.post(anvil_url) as response:
                # logger.debug('Anvil server response: {r}', r=response)
                if response.status == 200:
                    logger.debug(
                        'Anvil RPC endpoint ready.')
                else:
                    # rtext = await response.text()
                    raise ConnectionError(
                        f'Failed to start anvil. Server status response: {response.status}')

    async def stop(self):
        # try to stop the process nicely
        logger.debug(
            'Stopping anvil. Process: {process}', process=self.anvil_proc.pid)
        self.anvil_proc.terminate()
        try:
            # wait 15 seconds for the process to terminate
            await asyncio.wait_for(self.anvil_proc.communicate(), timeout=3.0)
        except asyncio.subprocess.TimeoutExpired:
            # if process did not shutdown nicely, force kill it
            await self.anvil_proc.kill()
            await asyncio.wait_for(self.anvil_proc, timeout=1.0)
        finally:
            logger.debug(
                'Stopped anvil.')
