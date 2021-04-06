import discord

from core.bases.cog_base import BaseCog
from discord.ext import commands


MIN_CYRILLIC_CODE = 1025
MAX_CYRILLIC_CODE = 1111
MIN_LATIN_CODE = 0
MAX_LATIN_CODE = 126


class EventsAutoNickCorrector(BaseCog):
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        data = await self.client.database.sel_guild(guild=member.guild)
        if not data.auto_mod["auto_nick_corrector"]["state"]:
            return

        non_unicode_chars = [
            c for c in list(member.display_name)
            if MIN_CYRILLIC_CODE <= ord(c) <= MAX_CYRILLIC_CODE or MIN_LATIN_CODE <= ord(c) <= MAX_LATIN_CODE
        ]
        unicode_percentage = 100-((len(non_unicode_chars)/len(member.display_name))*100)
        if not unicode_percentage >= data.auto_mod["auto_nick_corrector"]["percent"]:
            return

        try:
            await member.edit(nick=data.auto_mod["auto_nick_corrector"]["replace_with"])
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.display_name == before.display_name:
            return

        data = await self.client.database.sel_guild(guild=after.guild)
        if not data.auto_mod["auto_nick_corrector"]["state"]:
            return

        if "target_roles" in data.auto_mod["auto_nick_corrector"].keys():
            if data.auto_mod["auto_nick_corrector"]["target_roles"]:
                if not any([
                    role.id in data.auto_mod["auto_nick_corrector"]["target_roles"]
                    for role in after.roles
                ]):
                    return

        if "ignore_roles" in data.auto_mod["auto_nick_corrector"].keys():
            for role in after.roles:
                if role.id in data.auto_mod["auto_nick_corrector"]["ignore_roles"]:
                    return

        non_unicode_chars = [
            c for c in list(after.display_name)
            if MIN_CYRILLIC_CODE <= ord(c) <= MAX_CYRILLIC_CODE or MIN_LATIN_CODE <= ord(c) <= MAX_LATIN_CODE
        ]
        unicode_percentage = 100 - ((len(non_unicode_chars) / len(after.display_name)) * 100)
        if not unicode_percentage >= data.auto_mod["auto_nick_corrector"]["percent"]:
            return

        try:
            await after.edit(nick=data.auto_mod["auto_nick_corrector"]["replace_with"])
        except discord.Forbidden:
            pass


def setup(client):
    client.add_cog(EventsAutoNickCorrector(client))