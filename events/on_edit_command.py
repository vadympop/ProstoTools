from discord.ext import commands


class EventsOnEditProcessCommand(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        await self.client.process_commands(after)


def setup(client):
    client.add_cog(EventsOnEditProcessCommand(client))
