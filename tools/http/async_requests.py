import aiohttp


async def get(url, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, **kwargs) as response:
            data = response
    return data


async def post(url, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, **kwargs) as response:
            data = response
    return data


async def get_raw_data(url, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, **kwargs) as response:
            data = await response.read()
    return data
