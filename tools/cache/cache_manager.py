import json
from aiocache import MemcachedCache
from aiocache.serializers import JsonSerializer
from .exceptions import ValueIsNone, NotFoundKey
from tools.abc import AbcCacheManager


class CacheManager(AbcCacheManager):
    def __init__(self):
        self.client = MemcachedCache(
            serializer=JsonSerializer(), endpoint="localhost", port=11211, timeout=10
        )

    async def set(self, key: str, value):
        await self.client.set(key, value, ttl=3600)

    async def get(self, key: str):
        data = await self.client.get(key)
        if data is not None:
            for key, value in data.items():
                if isinstance(value, str):
                    if value is not None:
                        if (value.startswith("{") and value.endswith("}")) or (value.startswith("[") and value.endswith("]")):
                            data[key] = json.loads(value)
        return data

    async def exists(self, key: str):
        return await self.client.exists(key)

    async def update(self, key: str, data_key: str, new_value):
        data = await self.get(key)
        if data is None:
            raise ValueIsNone

        if data_key not in data.keys():
            raise NotFoundKey

        data[data_key] = new_value
        await self.set(key, data)
