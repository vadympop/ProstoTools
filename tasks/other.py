import discord
import time
from discord.ext import commands, tasks


class TasksOther(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.channel_loop.start()
		self.reminders_loop.start()
		self.FOOTER = self.client.config.FOOTER_TEXT

	@tasks.loop(seconds=30.0)
	async def reminders_loop(self):
		await self.client.wait_until_ready()
		data = await self.client.database.get_reminder()
		for reminder in data:
			reminder_time = reminder[4]
			guild = self.client.get_guild(int(reminder[2]))
			if guild is not None:
				member = guild.get_member(int(reminder[1]))
				channel = guild.get_channel(int(reminder[3]))
				if float(reminder_time) <= float(time.time()):
					emb = discord.Embed(
						title="Напоминания!",
						description=f"**Текст**:\n```{reminder[5]}```",
						colour=discord.Color.green(),
					)
					emb.set_author(
						name=self.client.user.name, icon_url=self.client.user.avatar_url
					)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await self.client.database.del_reminder(reminder[2], reminder[0])
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
		data = await self.client.database.get_punishment()
		for channel in data:
			channel_time = channel[2]
			guild = self.client.get_guild(int(channel[1]))
			if channel[3] == "text_channel":
				if guild is not None:
					member = guild.get_member(int(channel[0]))
					if member is not None:
						if float(channel_time) <= float(time.time()):
							await self.client.database.del_punishment(
								member=member,
								guild_id=guild.id,
								type_punishment="text_channel",
							)
							delete_channel = guild.get_channel(int(channel[4]))
							if delete_channel is not None:
								await delete_channel.delete()


def setup(client):
	client.add_cog(TasksOther(client))
