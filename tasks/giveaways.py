from core.utils.time_utils import get_timezone_obj
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
            guild = self.client.get_guild(setting.guild_id)
            if guild is not None:
                tz = get_timezone_obj(await self.client.database.get_guild_timezone(guild))
                giveaway_time = await self.client.utils.get_guild_time_from_timestamp(setting.time, guild, tz)
                guild_time = await self.client.utils.get_guild_time(guild, tz)
                if giveaway_time <= guild_time:
                    await self.client.utils.end_giveaway(setting)


def setup(client):
    client.add_cog(TasksGiveaways(client))
