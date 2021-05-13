import re
import discord

from core.bases.cog_base import BaseCog
from core.utils.other import process_auto_moderate
from discord.ext import commands


class EventsAntiInvite(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.pattern = re.compile(
            "discord\s?(?:(?:.|dot|(.)|(dot))\s?gg|(?:app)?\s?.\s?com\s?/\s?invite)\s?/\s?([A-Z0-9-]{2,18})", re.I
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        if message.author == message.guild.owner:
            return

        data = await self.client.database.sel_guild(guild=message.guild)
        if data.auto_mod["anti_invite"]["state"]:
            found_codes = re.findall(self.pattern, message.content)
            try:
                guild_invites_codes = [invite.code for invite in await message.guild.invites()]
            except discord.errors.Forbidden:
                return

            invites = [
                invite
                for item in found_codes
                for invite in item
                if invite
                if invite not in guild_invites_codes
            ]
            if invites == []:
                return

            await process_auto_moderate(
                await self.client.get_context(message), "anti_invite", data, "Авто-модерация: Приглашения"
            )


def setup(client):
    client.add_cog(EventsAntiInvite(client))
