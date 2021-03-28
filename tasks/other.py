import discord
import time

from core.bases.cog_base import BaseCog
from discord.ext import tasks


class TasksOther(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.channel_loop.start()
		self.reminders_loop.start()

	@tasks.loop(seconds=30.0)
	async def reminders_loop(self):
		await self.client.wait_until_ready()
		for reminder in await self.client.database.get_reminders():
			guild = self.client.get_guild(int(reminder.guild_id))
			if guild is not None:
				member = guild.get_member(int(reminder.user_id))
				channel = guild.get_channel(int(reminder.channel_id))
				if float(reminder.time) <= float(time.time()):
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

	@tasks.loop(minutes=1)
	async def channel_loop(self):
		await self.client.wait_until_ready()
		for channel in await self.client.database.get_punishments():
			guild = self.client.get_guild(channel.guild_id)
			if channel.type == "text_channel":
				if guild is not None:
					member = guild.get_member(channel.member_id)
					if member is not None:
						if float(channel.time) <= float(time.time()):
							await self.client.database.del_punishment(
								member=member,
								guild_id=guild.id,
								type_punishment="text_channel",
							)
							delete_channel = guild.get_channel(channel.role_id)
							if delete_channel is not None:
								await delete_channel.delete()


def setup(client):
	client.add_cog(TasksOther(client))
