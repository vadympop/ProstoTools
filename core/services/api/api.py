import json
import discord
import logging

from aiohttp import web
from pydantic import ValidationError
from .models import CacheUpdateInRequest

logger = logging.getLogger(__name__)


class API:
    _webserver: web.TCPSite

    def __init__(self, bot: discord.Client, port: int, host: str):
        self.bot: discord.Client = bot
        self.port: int = port
        self.host: str = host
        self._app: web.Application = web.Application(middlewares=[self.middleware()])
        self._is_ran: bool = False

    def middleware(self):
        @web.middleware
        async def auth_require(request: web.Request, handler):
            if request.headers.get('authorization') != self.bot.config.LOW_LEVEL_API_KEY:
                raise web.HTTPForbidden(text='Invalid api key')

            return await handler(request)

        return auth_require

    async def _cache_update(self, request: web.Request):
        request_json = await request.json()
        try:
            CacheUpdateInRequest.validate(request_json)
        except ValidationError as e:
            raise web.HTTPUnprocessableEntity(text=e.json())

        request_model = CacheUpdateInRequest(**request_json)
        resp = self.bot.cache.__getattribute__(request_model.entity).update(
            request_model.data, **request_model.query
        )
        return (
            web.HTTPNotFound(body='Entity by query was not found')
            if resp is None
            else web.Response(status=200, text=json.dumps(resp.to_dict()))
        )

    async def run(self):
        if not self._is_ran:
            self._is_ran = True
            self._app.router.add_patch('/cache/update', self._cache_update)

            runner = web.AppRunner(self._app)
            await runner.setup()
            self._webserver = web.TCPSite(runner, self.host, self.port)
            await self._webserver.start()
            logger.info("Webserver is ran")

    async def close(self):
        if not self._is_ran:
            return

        await self._webserver.stop()
        self._is_ran = False