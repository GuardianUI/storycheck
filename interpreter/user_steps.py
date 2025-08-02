from loguru import logger
import re
from interpreter.constants import StepLabels
from .step import StepInterpreter, ClickStep, KBInputStep, ScrollStep, KeyPressStep
from interpreter.ai.local_refexp import LocalRefExp
from .step import BrowseStep, get_prompt_text  # Restored import
from PIL import Image

class UserStepsInterpreter:

    def __init__(self, user_agent=None, **kwargs):
        super().__init__(**kwargs)
        assert user_agent is not None
        logger.debug('user_agent: {ua}', ua=user_agent)
        self.interpreters = {
            StepLabels.CLICK: ClickStep(user_agent=user_agent),
            StepLabels.KB_INPUT: KBInputStep(user_agent=user_agent),
            StepLabels.BROWSE: BrowseStep(user_agent=user_agent),  # Restored
            StepLabels.SCROLL: ScrollStep(user_agent=user_agent),
            StepLabels.KEYPRESS: KeyPressStep(user_agent=user_agent)
        }

    async def classify_prompt(self, prompt: list = None, screenshot: Image = None):
        """
        Classifies using RefExp interface; fallback on error/empty.
        """
        assert prompt is not None
        assert screenshot is not None, "Screenshot required for VLM classification"
        text = get_prompt_text(prompt).strip()
        
        try:
            # Manual fallback for direct browse (if VLM fails or prompt is simple)
            if re.match(r'browse\b', text.lower()):
                url_match = re.search(r'(https?://\S+)', text)
                if url_match:
                    return [(StepLabels.BROWSE, {'url': url_match.group(1)})]
                raise ValueError("No URL found in browse prompt")

            refexp = LocalRefExp()  # Or RemoteRefExp() if needed
            _, actions = await refexp.process_refexp(screenshot, text)
            if actions:
                return actions
            raise ValueError("No actions from RefExp")
        except Exception as e:
            logger.warning(f"VLM classification failed for prompt '{text}': {e}. Using fallback.")
            text_lower = text.lower()
            if text_lower.startswith('scroll'):
                return [(StepLabels.SCROLL, {})]
            elif text_lower.startswith('press'):
                return [(StepLabels.KEYPRESS, {})]
            elif re.match(r'type\b|input\b|enter\b', text_lower):
                return [(StepLabels.KB_INPUT, {})]
            elif re.match(r'click\b|select\b|tap\b', text_lower):
                return [(StepLabels.CLICK, {})]
            elif re.match(r'browse\b', text_lower):
                return [(StepLabels.BROWSE, {})]
            else:
                raise ValueError(f"Invalid prompt '{text}': Please use meaningful UI actions like 'click', 'type', etc.")

    def get_interpreter_by_class(self, prompt_class=None) -> StepInterpreter:
        """
        Look for the interpreter of a specific prompt class.
        """
        return self.interpreters[prompt_class]