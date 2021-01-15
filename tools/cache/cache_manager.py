from aiocache import MemcachedCache
from tools.abc import AbcCacheManager


class CacheManager(AbcCacheManager):
    def __init__(self):
        self.client = MemcachedCache(
            endpoint="localhost", port=11211
        )

    async def set(self, key: str, value):
        await self.client.set(key, value, 3600)

    async def get(self, key: str):
        return await self.client.get(key)

    async def exists(self, key: str):
        return await self.client.exists(key)

    async def delete(self, key: str):
        await self.client.delete(key)
