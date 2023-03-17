import asyncio
from loguru import logger


class LocalChain:
    """
    Wrapper around a local blockchain instance managed via Foundry Anvil
    """

    # OS reference to an anvil subprocesses
    anvil_proc = None

    async def start(self):
        # Create the subprocess; redirect the standard output
        # into a pipe.
        block_n = "16848466"
        logger.debug(
            'Starting anvil ETH Mainnet Fork at Block: {block_n}', block_n=block_n)
        self.anvil_proc = await asyncio.create_subprocess_exec(
            "anvil",
            "--fork-url", "https://eth-mainnet.g.alchemy.com/v2/0Uk2xg_qksy5OMviwu8MOHMHVJX4mQ1D",
            "--fork-block-number", block_n
        )
        logger.debug(
            'Started anvil. Process: {process}', process=self.anvil_proc)

    async def stop(self):
        # try to stop the process nicely
        logger.debug(
            'Stopping anvil. Process: {process}', process=self.anvil_proc)
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
                'Stopped anvil. Process: {process}', process=self.anvil_proc)
