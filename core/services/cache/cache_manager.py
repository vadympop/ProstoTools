import aioredis
import json
import typing
from core.bases import AbcCacheManager


class CacheManager(AbcCacheManager):
    async def run(self):
        self.conn = await aioredis.create_redis(
            "redis://redis-14597.c135.eu-central-1-1.ec2.cloud.redislabs.com:14597",
            password="d9hCden7eEqDeez1XHd05Bkt3IziDM9v"
        )

    async def set(self, key: str, value: dict):
        await self.conn.set(key, json.dumps(value))

    async def get(self, key: str) -> typing.Union[dict, list, None]:
        response = await self.conn.get(key)
        if response is None:
            return None

        return json.loads(response)

    async def exists(self, key: str) -> bool:
        return await self.conn.exists(key) == 1

    async def delete(self, key: str) -> bool:
        return await self.conn.delete(key) == 1

    async def update(self, key: str, value: dict) -> typing.Optional[dict]:
        data = await self.get(key)
        if data is None:
            return None

        data.update(value)
        await self.set(key, data)
        return data

    async def append(self, key: str, value: dict) -> typing.Optional[list]:
        data = await self.get(key)
        if data is None:
            data = []

        data.append(value)
        await self.set(key, data)
        return data