import re
from discord.ext import commands


class EventsAntiInvite(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.pattern = re.compile(
            "discord\s?(?:(?:.|dot|(.)|(dot))\s?gg|(?:app)?\s?.\s?com\s?/\s?invite)\s?/\s?([A-Z0-9-]{2,18})", re.I
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        invites = re.findall(self.pattern, message.content)
        guild_invites = [invite.code for invite in await message.guild.invites()]
        state_invites = {}
        for item in invites:
            for invite in item:
                if invite:
                    if invite in guild_invites:
                        state_invites.update({invite: False})
                    else:
                        state_invites.update({invite: True})


def setup(client):
    client.add_cog(EventsAntiInvite(client))
