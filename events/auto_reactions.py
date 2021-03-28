import discord

from core.bases.cog_base import BaseCog
from discord.ext import commands


class EventsAutoReactions(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.MUTE_ROLE = self.client.config.MUTE_ROLE
        self.HELP_SERVER = self.client.config.HELP_SERVER

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return
        else:
            auto_reactions = (await self.client.database.sel_guild(guild=message.guild)).auto_reactions
            if str(message.channel.id) in auto_reactions.keys():
                for reaction in auto_reactions[str(message.channel.id)]:
                    try:
                        await message.add_reaction(reaction)
                    except discord.errors.HTTPException:
                        pass


def setup(client):
    client.add_cog(EventsAutoReactions(client))
