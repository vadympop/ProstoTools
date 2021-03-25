import aiohttp
from .exceptions import *


class HTTPClient:
    def __init__(self, **kwargs):
        self.session = kwargs.pop("session") or aiohttp.ClientSession()

    async def request(self, method: str, url: str, **kwargs):
        async with self.session.request(method, url=url, **kwargs) as response:
            response_json = await response.json()
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
