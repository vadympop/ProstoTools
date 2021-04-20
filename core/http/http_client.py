import aiohttp
import typing
import logging
import json

from .exceptions import *

logger = logging.getLogger(__name__)


class HTTPClient:
    session: typing.Optional[aiohttp.ClientSession]

    def __init__(self):
        self.session = None

    def prepare(self, session: aiohttp.ClientSession):
        self.session = session

    async def _json_or_text(self, response: aiohttp.ClientResponse) -> typing.Union[dict, str]:
        text = await response.text()
        if 'application/json' in response.headers.get('Content-Type', 'text/plain'):
            return json.loads(text)
        return text

    async def request(self, method: str, url: str, **kwargs):
        logger.info(f"Make request for {url} with method {method}")

        async with self.session.request(method, url=url, **kwargs) as response:
            response_json = await self._json_or_text(response)
            logger.info(f"Response of request to {url} with method {method}: {response_json}")
            logger.info(f"Response status of request to {url} with method {method}: {response.status}")

            if 300 > response.status >= 200:
                return response_json

            if response.status == 404:
                raise NotFound(response_json)
            elif response.status == 400:
                raise BadRequest(response_json)
            elif response.status == 403:
                raise Forbidden(response_json)
            elif response.status == 429:
                raise RateLimited(response_json)
            else:
                raise ServerError(response_json)

    async def get(self, url: str, **kwargs):
        return await self.request(
            method="GET",
            url=url,
            **kwargs
        )

    async def post(self, url: str, **kwargs):
        return await self.request(
            method="POST",
            url=url,
            **kwargs
        )

    async def close(self):
        if self.session:
            await self.session.close()
