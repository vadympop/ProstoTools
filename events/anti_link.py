import re

from core.bases.cog_base import BaseCog
from core.utils.other import process_auto_moderate
from discord.ext import commands


class EventsAntiLink(BaseCog):
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        if message.author == message.guild.owner:
            return

        data = await self.client.database.sel_guild(guild=message.guild)
        if data.auto_mod["anti_link"]["state"]:
            if all([re.search(d, message.content) is None for d in data.auto_mod["domains"]]):
                return

            await process_auto_moderate(
                await self.client.get_context(message), "anti_link", data, "Авто-модерация: Ссылки"
            )


def setup(client):
    client.add_cog(EventsAntiLink(client))
