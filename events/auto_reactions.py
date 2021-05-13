import discord

from core.bases.cog_base import BaseCog
from discord.ext import commands


class EventsAutoReactions(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.FILTERS_PREDICATES = self.client.config.MESSAGES_FILTERS_PREDICATES
        self.MUTE_ROLE = self.client.config.MUTE_ROLE
        self.HELP_SERVER = self.client.config.HELP_SERVER

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        auto_reactions = (await self.client.database.sel_guild(guild=message.guild)).auto_reactions
        if message.channel.id in auto_reactions.keys():
            if auto_reactions[message.channel.id]["filters"]:
                checking_func = any if auto_reactions[message.channel.id]["filter_mode"] == "any" else all
                if not checking_func([
                    self.FILTERS_PREDICATES[i](message)
                    for i in auto_reactions[message.channel.id]["filters"]
                ]):
                    return

            for reaction in auto_reactions[message.channel.id]["reactions"]:
                try:
                    await message.add_reaction(reaction)
                except discord.errors.HTTPException:
                    pass


def setup(client):
    client.add_cog(EventsAutoReactions(client))
