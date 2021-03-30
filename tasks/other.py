import discord
import datetime

from core.bases.cog_base import BaseCog
from discord.ext import tasks


class TasksOther(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.reminders_loop.start()

	@tasks.loop(seconds=30.0)
	async def reminders_loop(self):
		await self.client.wait_until_ready()
		for reminder in await self.client.database.get_reminders():
			guild = self.client.get_guild(int(reminder.guild_id))
			if guild is not None:
				member = guild.get_member(int(reminder.user_id))
				channel = guild.get_channel(int(reminder.channel_id))
				if float(reminder.time) <= float((await self.client.utils.get_guild_time(guild)).timestamp()):
					emb = discord.Embed(
						title="Напоминания!",
						description=f"**Текст**:\n```{reminder.text}```",
						colour=discord.Color.green(),
					)
					emb.set_author(
						name=self.client.user.name, icon_url=self.client.user.avatar_url
					)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await self.client.database.del_reminder(reminder.id)
					if member is not None and channel is not None:
						if channel in guild.channels:
							await channel.send(embed=emb, content=member.mention)
						else:
							try:
								await member.send(embed=emb)
							except:
								pass

def setup(client):
	client.add_cog(TasksOther(client))
