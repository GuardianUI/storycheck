from PIL import Image
from abc import abstractmethod, ABC


class RefExp(ABC):
    """
    Abstract wrapper around VLM Transformer fine tuned for RefExp task
    """

    @abstractmethod
    async def process_refexp(self, image: Image,
                             prompt: str,
                             return_annotated_image: bool = True):
        """
        Predict coordinates of a UI element referred by text prompt.

        Args:
            image: UI screenshot in PIL format
            prompt: referring expression prompt
            return_annotated_image: whether or not to return an image
                with annotation of UI element coordiantes

        Returns:
            Tuple of (annotated_image, coordinates)

        """
        pass
