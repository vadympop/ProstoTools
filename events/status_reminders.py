import discord
from discord.ext import commands


class CogName(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.status == after.status:
            return

        data = await self.client.database.get_status_reminder(target_id=after.id)
        for setting in data:
            if str(after.status) == setting[3]:
                if setting[4] == "default":
                    await self.client.database.del_status_reminder(setting[0])

                user = self.client.get_user(setting[2])
                if user is None:
                    await self.client.database.del_status_reminder(setting[0])
                else:
                    emojis = {
                        "dnd": "<:dnd:730391353929760870>(`Не беспокоить`)",
                        "online": "<:online:730393440046809108>(`В сети`)",
                        "offline": "<:offline:730392846573633626>(`Не в сети`)",
                        "idle": "<:sleep:730390502972850256>(`Отошёл`)",
                    }
                    emb = discord.Embed(
                        description=f"Пользователь(`{after}`) изменил свой статус на {emojis[str(after.status)]}",
                        colour=discord.Color.blurple()
                    )
                    emb.set_author(icon_url=user.avatar_url, name=str(user))
                    emb.set_footer(icon_url=after.avatar_url, text="Напоминания статусов")
                    try:
                        await user.send(embed=emb)
                    except:
                        pass


def setup(client):
    client.add_cog(CogName(client))