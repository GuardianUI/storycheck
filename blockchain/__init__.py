import asyncio
from loguru import logger


class LocalChain:
    """
    Wrapper around a local blockchain instance managed via Foundry Anvil
    """

    # OS reference to an anvil subprocesses
    anvil_proc = None

    RPC_URLs = {
        '1': 'https://eth-mainnet.g.alchemy.com/v2/0Uk2xg_qksy5OMviwu8MOHMHVJX4mQ1D',
        '42161': 'https://arb-mainnet.g.alchemy.com/v2/Kjt13n8OuVVCBqxIGMGYuwgbnLzfh1U6'
    }

    async def start(self, chain_id='1', block_n=None):
        # Create the subprocess; redirect the standard output
        # into a pipe.
        assert isinstance(chain_id, str)
        chain_args = ["--chain-id", chain_id, "--fork-url", self.RPC_URLs[chain_id]]
        if block_n is not None:
            assert isinstance(block_n, str)
            block_args = ["--fork-block-number", block_n]
        logger.debug(
            'Starting anvil EVM Fork for ChainID: {chain_id} at Block: {block_n}', block_n=block_n)
        self.anvil_proc = await asyncio.create_subprocess_exec(
            "anvil",
            *chain_args,
            *block_args,
            # "--no-mining"
        )
        logger.debug(
            'Started anvil. Process: {process}', process=self.anvil_proc.pid)

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
