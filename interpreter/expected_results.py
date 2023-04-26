from .section import StorySection
from .step import StepInterpreter, get_prompt_text
from loguru import logger
from enum import Enum, auto
from pprint import pformat as pf
import re
import os
from traceback import format_tb
from pathlib import Path
import shutil
import json


class CheckStep(StepInterpreter):

    async def aexit(self):
        """
        Clean up any resources allocated for prerequisites
        """
        pass


def tx_matches(tx1, tx2):
    """
    Compare two blockchain write transactions for matching signature and results.
    """
    # compare call sigs
    j1 = json.dumps(tx1["writeTx"])
    j2 = json.dumps(tx2["writeTx"])
    return j1 == j2  # "Transaction call signature must match snapshot"
    # compare exception sigs
    txe1 = tx1['writeTxException']
    txe2 = tx2['writeTxException']
    if txe1 is not None or txe2 is not None:
        je1 = json.dumps(txe1)
        je2 = json.dumps(txe2)
        return je1 == je2  # "Transaction exception signature must match snapshot"
    # compare result sigs
    txr1 = tx1['writeTxResult']
    txr2 = tx2['writeTxResult']
    if txr1 is not None:
        return txr2 is not None  # "Transaction result must match snapshot"
    else:
        return txr2 is None  # "Transaction result must match snapshot"


def compare_snapshots(saved=None, new=None):
    assert saved is not None
    assert new is not None
    saved_json = json.load(saved)
    new_json = json.load(new)
    errors = ((txnew, txsaved) for txnew, txsaved in zip(
        new_json, saved_json) if not tx_matches(txnew, txsaved))
    assert errors is None, \
        f'Wallet transactions must match snapshot. Mismatches found:\n {errors}'


class SnapshotCheck(CheckStep):

    async def interpret_prompt(self, prompt):
        logger.debug('snapshot check prompt:\n {prompt}', prompt=pf(prompt))
        story_path = os.environ.get("GUARDIANUI_STORY_PATH")
        assert story_path is not None
        fpath = Path(story_path)
        saved_snapshot = fpath.with_suffix('.snapshot.json')
        new_snapshot = Path('results/tx_log_snapshot.json')
        if saved_snapshot.exists():
            logger.debug('Found saved snapshot. Comparing transactions...')
            compare_snapshots(saved=saved_snapshot, new=new_snapshot)
            logger.debug(
                'Wallet transactions in current run match saved snapshot.')
        else:
            logger.debug('No previous snapshot found. Saving snapshot.')
            shutil.copyfile(new_snapshot, saved_snapshot)

            # if snapshot saved, compare to snapshot from current run
            # else save current snapshot alongside story for future comparison
            # os.environ.get("GUARDIANUI_STORY_PATH")
        logger.debug('snapshot check completed.')

    async def aexit(self):
        """
        Clean up any resources allocated for prerequisites
        """
        pass


class ExpectedResults(StorySection):

    class StepInterpreter(StepInterpreter):
        def interpret_prompt(self):
            """
            Interpret in computer code the intention of the natural language input prompt.
            """
            pass

    class CheckLabels(Enum):
        SNAPSHOT = auto()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.interpreters = {
            self.CheckLabels.SNAPSHOT: SnapshotCheck(),
        }

    def classify_prompt(self, prompt: list = None):
        """
        Classifies a natural language prompt in md-AST format as one of multiple predefined options.
        """
        assert prompt is not None
        logger.debug('Classifying prompt:\n {prompt}', prompt=pf(prompt))
        text = get_prompt_text(prompt)
        text = text.lower().strip()
        logger.debug('Prompt text: {text}', text=text)
        if re.search(r'match snapshot\b', text):
            return self.CheckLabels.SNAPSHOT

    def get_interpreter_by_class(self, prompt_class=None) -> StepInterpreter:
        """
        Look for the interpreter of a specific prompt class.
        """
        return self.interpreters[prompt_class]

    async def __aenter__(self):
        """
        runs when prerequisite used in 'with' python construct
        """
        return self

    async def __aexit__(self, exception_type, exception_value, exception_traceback):
        """
        runs on exiting a 'with' python construct
        """
        # Exception handling here
        if exception_type or exception_value:
            logger.error('Exception\n type: {t},\n value: {v}, \n traceback: {tb}',
                         t=exception_type,
                         v=exception_value,
                         tb=pf(format_tb(exception_traceback)))
        for label, interpreter in self.interpreters.items():
            await interpreter.aexit()
