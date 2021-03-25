class RandomAPI:
    def __init__(self, client):
        self.client = client
        self.url = "https://some-random-api.ml/"

    async def get_dog(self):
        return (await self.client.http_client.get(
            url=self.url+"img/dog"
        )).get("link")

    async def get_cat(self):
        return (await self.client.http_client.get(
            url=self.url+"img/cat"
        )).get("link")

    async def get_fox(self):
        return (await self.client.http_client.get(
            url=self.url+"img/fox"
        )).get("link")

    async def get_bird(self):
        return (await self.client.http_client.get(
            url=self.url+"img/birb"
        )).get("link")

    async def get_koala(self):
        return (await self.client.http_client.get(
            url=self.url+"img/koala"
        )).get("link")
