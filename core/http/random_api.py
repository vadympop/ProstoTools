from . import async_requests as requests


class RandomAPI:
    def __init__(self):
        self.url = "https://some-random-api.ml/"

    async def get_dog(self):
        data = await requests.get(
            url=self.url+"img/dog"
        )
        return (await data.json())["link"]

    async def get_cat(self):
        data = await requests.get(
            url=self.url+"img/cat"
        )
        return (await data.json())["link"]

    async def get_fox(self):
        data = await requests.get(
            url=self.url+"img/fox"
        )
        return (await data.json())["link"]

    async def get_bird(self):
        data = await requests.get(
            url=self.url+"img/birb"
        )
        return (await data.json())["link"]

    async def get_koala(self):
        data = await requests.get(
            url=self.url+"img/koala"
        )
        return (await data.json())["link"]
