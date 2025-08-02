import sys
import os
import pytest
import gc
import torch

# Add project root to sys.path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Optional: Fixture example if needed later (e.g., for shared setup)
@pytest.fixture(scope="session")
def project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

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