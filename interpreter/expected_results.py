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


def tx_matches(txsaved, txnew):
    """
    Compare two blockchain write transactions for matching signature and results.
    """
    # compare call sigs
    jswrite = json.dumps(txsaved["writeTx"])
    jnwrite = json.dumps(txnew["writeTx"])
    if jswrite != jnwrite:
        logger.warning("""Transaction call signatures do not match:
                        Saved tx sig: {s}
                        New tx sig: {n}
                        """,
                       s=jswrite,
                       n=jnwrite
                       )
        return False
    # compare exception sigs
    se = txsaved['writeTxException']
    ne = txnew['writeTxException']
    if se is not None or ne is not None:
        jse = json.dumps(se)
        jne = json.dumps(ne)
        if jse != jne:
            logger.warning("""Transaction exception signature must match snapshot:
                            Saved tx exception: {s}
                            New tx exception: {n}
                            """,
                           s=jse,
                           n=jne
                           )
            return False
    # compare result sigs
    sr = txsaved['writeTxResult']
    nr = txnew['writeTxResult']
    if sr is not None:
        if nr is None:
            logger.warning("""Transaction result must match snapshot:
                            Saved tx result: {s}
                            New tx result: {n}
                            """,
                           s=sr,
                           n=nr
                           )
            return False
    else:
        if nr is not None:
            logger.warning("""Transaction result must match snapshot:
                            Saved tx result: {s}
                            New tx result: {n}
                            """,
                           s=sr,
                           n=nr
                           )
            return False


def compare_snapshots(saved=None, new=None):
    assert saved is not None
    assert new is not None
    with open(saved) as f:
        saved_json = json.load(f)
    with open(new) as f:
        new_json = json.load(f)
    logger.debug('Saved tx snapshot:\n {s}', s=saved_json)
    logger.debug('New tx snapshot:\n {n}', n=new_json)
    if len(saved_json) == len(new_json):
        mismatched = [(txsaved, txnew) for txsaved, txnew in zip(
            saved_json, new_json) if not tx_matches(txsaved, txnew)]
    else:
        mismatched = True
    if mismatched:
        errors = {
            'saved_snapshot': saved_json,
            'new_snapshot': new_json
        }
        logger.warning('Snapshots do not match!')
    else:
        errors = None
        logger.debug('Snapshots match.')
    return errors


class SnapshotCheck(CheckStep):

    async def interpret_prompt(self, prompt):
        logger.debug('snapshot check prompt:\n {prompt}', prompt=pf(prompt))
        story_path = os.environ.get("GUARDIANUI_STORY_PATH")
        assert story_path is not None
        fpath = Path(story_path)
        saved_snapshot = fpath.with_suffix('.snapshot.json')
        new_snapshot = Path('results/tx_log_snapshot.json')
        errors = None
        if saved_snapshot.exists():
            logger.debug('Found saved snapshot. Comparing transactions...')
            errors = compare_snapshots(saved=saved_snapshot, new=new_snapshot)
        else:
            logger.debug('No previous snapshot found. Saving snapshot.')
            shutil.copyfile(new_snapshot, saved_snapshot)
        logger.debug('snapshot check completed.')
        return errors

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
