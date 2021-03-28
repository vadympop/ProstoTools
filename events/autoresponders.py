from core.bases.cog_base import BaseCog
from discord.ext import commands


class EventsAutoResponders(BaseCog):
    def __init__(self, client):
        super().__init__(client)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is not None:
            if message.author.bot:
                return

            autoresponders = (await self.client.database.sel_guild(guild=message.guild)).autoresponders
            command = message.content.split(" ")[0]
            if command in autoresponders.keys():
                await message.channel.send(autoresponders[command])


def setup(client):
    client.add_cog(EventsAutoResponders(client))
