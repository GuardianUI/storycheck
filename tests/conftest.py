import sys
import os
import pytest
import gc
import torch
from pathlib import Path
import logging

# Add project root to sys.path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

root = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Optional: Fixture example if needed later (e.g., for shared setup)
@pytest.fixture(scope="session")
def project_root():
    return root

res_dir = Path(os.environ.get("GUARDIANUI_RESULTS_PATH", f"{root}/results/"))
res_dir.mkdir(parents=True, exist_ok=True)    
os.makedirs(res_dir, exist_ok=True)

@pytest.fixture(scope="session")
def results_dir():
    return res_dir

@pytest.fixture(scope="session")
def logger():
    # Configure logging with console and file output
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
    logger = logging.getLogger(__name__)
    file_handler = logging.FileHandler(f'{res_dir}/tests.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(file_handler)
    logger.info("Logger initialized for tests")
    return logger

@pytest.fixture(scope="session")
def shared_local_refexp():
    from interpreter.ai.local_refexp import LocalRefExp
    local_refexp = LocalRefExp()
    yield local_refexp
    # Explicit cleanup to prevent hangs
    del local_refexp
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.empty_cache()

