import datetime

from core.bases.cog_base import BaseCog
from discord.ext import tasks


class TasksGiveaways(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.giveaways_loop.start()

    @tasks.loop(minutes=1)
    async def giveaways_loop(self):
        await self.client.wait_until_ready()
        for setting in await self.client.database.get_giveaways():
            if (await self.client.utils.get_guild_time(self.client.get_guild(setting.guild_id))).timestamp() >= setting.time:
                await self.client.utils.end_giveaway(setting)


def setup(client):
    client.add_cog(TasksGiveaways(client))
