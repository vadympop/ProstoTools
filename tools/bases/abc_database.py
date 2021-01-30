import typing
from abc import ABC


class AbcDatabase(ABC):
    async def execute(self, query: str, val: typing.Union[tuple, list] = (), fetchone: bool = False):
        pass

    async def update(self, table: str, **kwargs):
        pass
