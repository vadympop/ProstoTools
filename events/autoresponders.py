from discord.ext import commands


class EventsAutoResponders(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is not None:
            if message.author.bot:
                return

            autoresponders = (await self.client.database.sel_guild(guild=message.guild))["autoresponders"]
            command = message.content.split(" ")[0]
            if command in autoresponders.keys():
                await message.channel.send(autoresponders[command])


def setup(client):
    client.add_cog(EventsAutoResponders(client))
