# File: interpreter/expected_results.py
from .section import StorySection
from .step import StepInterpreter, get_prompt_text
from .step import get_prompt_link
from slugify import slugify
from loguru import logger
from enum import Enum, auto
from pprint import pformat as pf
import re
import os
from traceback import format_tb
from pathlib import Path
import json


class CheckStep(StepInterpreter):
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up any resources allocated for checks
        """
        pass

class VerifierCheck(CheckStep):
    def __init__(self, user_agent=None, **kwargs):
        super().__init__(user_agent=user_agent, **kwargs)
        self.user_agent = user_agent

    async def interpret_prompt(self, prompt, link):
        logger.debug(f"Verifier prompt: {prompt}, link: {link}")
        verifier_path = Path(link)
        results_dir = self.user_agent.results_dir  # From UserAgent        
        if verifier_path.exists():
            with open(verifier_path, 'r') as f:
                code = f.read()
            # Placeholder for execution (e.g., integrate code_execution tool or exec)
            logger.info(f"Would execute verifier {verifier_path}: {code[:100]}...")
            try:
                local_scope = {}
                exec(code, globals(), local_scope)
                result = local_scope['verify'](results_dir)  # Generic call with results_dir
                if not result.get('passed', False):
                    return result.get('error', "Verifier failed without error message")                
                logger.info(f"Verifier {verifier_path} passed.")
                return None
            except Exception as e:
                return f"Execution error: {str(e)}"
        else:
            return f"Verifier file not found: {verifier_path}"

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
            errors = compare_snapshots(saved_json=saved_json, new_json=new_json)
        logger.debug('snapshot check completed.')
        return errors

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up any resources allocated for prerequisites
        """
        pass

class ExpectedResults(StorySection):
    class CheckLabels(Enum):
        SNAPSHOT = auto()
        VERIFIER = auto()

    def __init__(self, user_agent=None, **kwargs):
        assert user_agent is not None
        super().__init__(**kwargs)
        self.user_agent = user_agent
        self.interpreters = {
            self.CheckLabels.SNAPSHOT: SnapshotCheck(user_agent=self.user_agent),
            self.CheckLabels.VERIFIER: VerifierCheck(user_agent=self.user_agent)
        }
        self.parsed_results = []

    def classify_prompt(self, prompt: list = None):
        """
        Classifies a natural language prompt in md-AST format as one of multiple predefined options.
        """
        assert prompt is not None
        logger.debug('Classifying prompt:\n {prompt}', prompt=pf(prompt))
        text = get_prompt_text(prompt)
        _, link = get_prompt_link(prompt[0] if prompt else {})
        text = text.lower().strip()
        logger.debug('Prompt text: {text}', text=text)
        if re.search(r'match snapshot\b', text):
            return self.CheckLabels.SNAPSHOT
        if re.search(r'verifier\b', text) or link:
            return self.CheckLabels.VERIFIER

    def get_interpreter_by_class(self, prompt_class=None) -> StepInterpreter:
        """
        Look for the interpreter of a specific prompt class.
        """
        return self.interpreters[prompt_class]

    def interpret(self, expected_results: list):
        self.parsed_results = []
        for node in expected_results:
            if node:
                text, link = get_prompt_link(node[0])
                text = text.strip()
                if link is None:
                    slug = slugify(text)
                    link = f"verifiers/{slug}.py"
                self.parsed_results.append({'text': text, 'verifier_link': link})

    async def run(self, story_interpreter=None):
        assert story_interpreter is not None, 'story_interpreter should be a populated object'
        passed = True
        errors = []
        self.interpret(story_interpreter.user_story.expected_results)
        for result in self.parsed_results:
            # Simulate prompt list for classify
            sim_prompt = [{'children': [{'type': 'text', 'raw': result['text']}, 
                                        {'type': 'link', 'href': result['verifier_link']} if result['verifier_link'] else {}]}]
            prompt_class = self.classify_prompt(sim_prompt)
            interpreter = self.get_interpreter_by_class(prompt_class)
            err = await interpreter.interpret_prompt(result['text'], result['verifier_link'])
            if err:
                passed = False
                errors.append(err)
        logger.info(f"Expected Results report: Passed={passed}, Errors={errors}")                
        return passed, errors

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
            await interpreter.__aexit__(None, None, None)