import asyncio
from loguru import logger


class Anvil:
    """
    Wrapper around a Foundry Anvil process instance
    """

    # OS reference to an anvil subprocesses
    anvil_proc = None

    async def start(self):
        # Create the subprocess; redirect the standard output
        # into a pipe.
        self.anvil_proc = await asyncio.create_subprocess_exec(
            "anvil",
            " --fork-url https://eth-mainnet.g.alchemy.com/v2/0Uk2xg_qksy5OMviwu8MOHMHVJX4mQ1D",
            "--fork-block-number 16848466ls",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        # Read and log any output.
        stdout, stderr = await self.anvil_proc.communicate()
        while stdout:
            logger.info(f'[stdout]\n{stdout.decode()}')
        while stderr:
            logger.info(f'[stderr]\n{stderr.decode()}')

    async def stop(self):
        # try to stop the process nicely
        await self.anvil_proc.terminate()
        try:
            # wait 15 seconds for the process to terminate
            stdout, stderr = await self.anvil_proc.communicate(timeout=15)
            while stdout:
                logger.info(f'[stdout]\n{stdout.decode()}')
            while stderr:
                logger.info(f'[stderr]\n{stderr.decode()}')
        except asyncio.subprocess.TimeoutExpired:
            # if process did not shutdown nicely, force kill it
            await self.anvil_proc.kill()
            outs, errs = await self.anvil_proc.communicate()
