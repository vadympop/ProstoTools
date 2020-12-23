import aiohttp


async def get(url, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, **kwargs) as response:
            return response


async def post(url, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, **kwargs) as response:
            return response
