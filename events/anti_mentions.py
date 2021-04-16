from core.bases.cog_base import BaseCog
from core.utils.other import process_auto_moderate
from discord.ext import commands


class EventsAntiMentions(BaseCog):
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        if message.author == message.guild.owner:
            return

        data = await self.client.database.sel_guild(guild=message.guild)
        if data.auto_mod["anti_mentions"]["state"]:
            if len(message.mentions) < data.auto_mod["anti_mentions"]["max_mentions"]:
                return

            await process_auto_moderate(await self.client.get_context(message), "anti_mentions", data)


def setup(client):
    client.add_cog(EventsAntiMentions(client))
