import typing


class CacheItem:
    def __init__(self, **kwargs):
        self._dict = {**kwargs}

    def to_dict(self):
        return self._dict

    def clear(self):
        return self._dict.clear()

    def copy(self):
        return self._dict.copy()

    def has_key(self, k):
        return k in self._dict

    def update(self, *args, **kwargs):
        return self._dict.update(*args, **kwargs)

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()

    def __setitem__(self, key, item):
        self._dict[key] = item

    def __getitem__(self, key):
        return self._dict[key]

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __repr__(self):
        return repr(self._dict)

    def __len__(self):
        return len(self._dict)

    def __delitem__(self, key):
        del self._dict[key]


class CacheManager:
    def __init__(self, name: str, max_size: int):
        self.items = []
        self._max_size = max_size
        self.name = name

    def get(self, **kwargs) -> typing.Optional[CacheItem]:
        for item in self.items:
            if all([item[key] == value for key, value in kwargs.items()]):
                return CacheItem(**item)

        return None

    def get_raw(self, **kwargs) -> typing.Optional[dict]:
        for item in self.items:
            if all([item[key] == value for key, value in kwargs.items()]):
                return item

        return None

    def find(self, **kwargs) -> typing.List[CacheItem]:
        return [
            CacheItem(**item)
            for item in self.items
            if all([item[key] == value for key, value in kwargs.items()])
        ]

    def add(self, item) -> None:
        self.items.append(item)

        if len(self.items) > self._max_size:
            self.items.pop(0)

    def _update_dict(self, item: dict, **kwargs) -> dict:
        item.update(**kwargs)
        return item

    def update(self, new_data, **kwargs) -> typing.Optional[CacheItem]:
        item = self.get_raw(**kwargs)
        if item is None:
            return None

        self.items[self.items.index(item)] = self._update_dict(item, **new_data)
        return CacheItem(**item)

    def remove(self, **kwargs) -> typing.Optional[CacheItem]:
        item = self.get_raw(**kwargs)
        if item is None:
            return None

        self.items.remove(item)
        return CacheItem(**item)

    def all(self) -> typing.List[CacheItem]:
        return [CacheItem(**item) for item in self.items]

    def count(self) -> int:
        return len(self.items)

    def __repr__(self):
        return "CacheManager(name={0.name}, max_size={0._max_size} items=[".format(self)+("\n".join([
            f"Item({CacheItem(**item)})"
            for item in self.items
        ]))+"])"