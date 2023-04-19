from loguru import logger
from PIL import Image
from . import RefExp
from aiohttp import ClientSession
import base64
from io import BytesIO

RefExpGPT_URL = "http://ec2-54-144-176-243.compute-1.amazonaws.com:7860/run/predict"


class RemoteRefExp(RefExp):
    """
    Wrapper around Remote Refexp GPT API
    """

    async def process_refexp(self, image: Image,
                             prompt: str):
        """
        Predict coordinates of a UI element referred by text prompt.

        Args:
            image: UI screenshot in PIL format
            prompt: referring expression prompt

        Returns:
            dict: {'x','y'} coordinates of UI element

        """

        logger.debug(
            "(image, prompt): {image}, {prompt}", image=image, prompt=prompt)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
        img_str = img_str.decode("utf-8")
        base64_prefix = 'data:image/png;base64,'
        logger.debug('Base64 image string: {imgs}', imgs=img_str[:100])
        post_json = {
            "data": [
                base64_prefix + img_str,
                prompt,
                "main",
                True,
            ]
        }
        async with ClientSession() as session:
            async with session.post(RefExpGPT_URL, json=post_json) as response:
                # logger.debug('RefExpGPT server response: {r}', r=response)
                if response.status == 200:
                    response_json = await response.json()
                    # logger.debug(
                    # 'RefExpGPT RPC json response: {jsn}', jsn=response_json)
                    center_point = response_json['data'][1]
                    logger.debug(
                        'RefExpGPT RPC responded with coordinates: {cp}', cp=center_point)
                    base64_annotated_image = response_json['data'][0]
                    base64_annotated_image = base64_annotated_image[len(
                        base64_prefix):]
                    ann_img = Image.open(
                        BytesIO(base64.b64decode(base64_annotated_image)))
                    return ann_img, center_point
                else:
                    # rtext = await response.text()
                    raise ConnectionError(
                        f'Failed to fetch RefExpGPT API. Server status response: {response.status}')
