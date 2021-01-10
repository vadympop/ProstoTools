from abc import ABC


class AbcCacheManager(ABC):
    async def set(self, key: str, value):
        pass

    async def get(self, key: str):
        pass

    async def exists(self, key: str):
        pass

    async def update(self, key: str, data_key: str, new_value):
        pass
