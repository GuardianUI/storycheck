# File Path: interpreter/expected_results.py

from .section import StorySection
from .step import StepInterpreter, get_prompt_text
from loguru import logger
from enum import Enum, auto
from pprint import pformat as pf
import re
import os
from traceback import format_tb
from pathlib import Path
import json

class CheckStep(StepInterpreter):
    async def aexit(self):
        """
        Clean up any resources allocated for prerequisites
        """
        pass

def cleanup_tx(tx):
    """
    Edit out from transaction signature variables such as gasLimit
    that are not essential for storycheck.
    """
    for p in tx["writeTx"]['params']:
        p.pop('gasLimit', None)

def tx_matches(txsaved, txnew):
    """
    Compare two blockchain write transactions for matching signature and results.
    """
    cleanup_tx(txsaved)
    cleanup_tx(txnew)
    # compare call sigs
    jswrite = json.dumps(txsaved["writeTx"])
    jnwrite = json.dumps(txnew["writeTx"])
    if jswrite != jnwrite:
        logger.error("""Transaction call signatures do not match:
                        Saved tx sig:\n {s}
                        New tx sig:\n {n}
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
    return True

def compare_snapshots(saved_json=None, new_json=None):
    assert saved_json is not None
    assert new_json is not None
    logger.debug('Saved tx snapshot:\n {s}', s=saved_json)
    logger.debug('New tx snapshot:\n {n}', n=new_json)
    if len(saved_json) == len(new_json):
        mismatched = [(txsaved, txnew) for txsaved, txnew in zip(
            saved_json, new_json) if not tx_matches(txsaved, txnew)]
    else:
        mismatched = True
    if mismatched:
        logger.error('Mismatched transactions: {m}', m=mismatched)
        errors = {
            'saved_snapshot': saved_json,
            'new_snapshot': new_json
        }
        logger.warning('Snapshots do not match!')
    else:
        logger.debug('No mismatched transactions')
        errors = None
        logger.debug('Snapshots match.')
    return errors

class SnapshotCheck(CheckStep):
    def __init__(self, user_agent=None, **kwargs):
        super().__init__(user_agent=user_agent, **kwargs)
        self.user_agent = user_agent

    async def interpret_prompt(self, prompt):
        logger.debug('snapshot check prompt:\n {prompt}', prompt=pf(prompt))
        story_path = os.environ.get("GUARDIANUI_STORY_PATH")
        assert story_path is not None
        fpath = Path(story_path)
        saved_snapshot = fpath.with_suffix('.snapshot.json')
        errors = None

        if not saved_snapshot.exists():
            logger.debug('No previous snapshot found. Saving snapshot.')
            with open(saved_snapshot, 'w') as outfile:
                json.dump(self.user_agent.wallet_tx_snapshot, outfile)
        else:
            logger.debug('Found saved snapshot. Comparing transactions...')
            with open(saved_snapshot, 'r') as infile:
                saved_json = json.load(infile)
            new_json = self.user_agent.wallet_tx_snapshot
            errors = compare_snapshots(saved=saved_json, new=new_json)

        logger.debug('snapshot check completed.')
        return errors

    async def aexit(self):
        """
        Clean up any resources allocated for prerequisites
        """
        pass

class ExpectedResults(StorySection):
    class CheckLabels(Enum):
        SNAPSHOT = auto()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_agent = kwargs.get('user_agent')
        self.interpreters = {
            self.CheckLabels.SNAPSHOT: SnapshotCheck(user_agent=self.user_agent)
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