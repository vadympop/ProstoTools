import discord

from core.services.database.models import StatusReminder
from core.bases.cog_base import BaseCog
from discord.ext import commands


class StatusRemindersEvents(BaseCog):
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.status == after.status:
            return

        for setting in await self.client.database.get_status_reminders():
            if str(after.status) == setting.wait_for:
                if setting.type == "default":
                    await self.client.database.del_status_reminder(setting.id)

                user = self.client.get_user(setting.member_id)
                if user is None:
                    await self.client.database.del_status_reminder(setting.id)
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
    client.add_cog(StatusRemindersEvents(client))