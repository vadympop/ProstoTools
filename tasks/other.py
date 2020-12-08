import discord
import os
import json
import time
import mysql.connector

from tools import DB

from configs import configs
from discord.ext import commands, tasks
from discord.utils import get


class TasksOther(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(
			user="root",
			password=os.getenv("DB_PASSWORD"),
			host="localhost",
			database="data",
		)
		self.cursor = self.conn.cursor(buffered=True)
		self.update_messages_loop.start()
		self.ping_stat_loop.start()
		self.reminders_loop.start()
		self.channel_loop.start()
		self.FOOTER = configs["FOOTER_TEXT"]

	@tasks.loop(seconds=30)
	async def reminders_loop(self):
		for reminder in DB().get_reminder():
			reminder_time = reminder[4]
			guild = self.client.get_guild(int(reminder[2]))
			if guild is not None:
				member = guild.get_member(int(reminder[1]))
				channel = guild.get_channel(int(reminder[3]))
				emb = discord.Embed(
					title="Напоминания!",
					description=f"**Текст**:\n```{reminder[5]}```",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				if member is not None:
					if float(reminder_time) <= float(time.time()):
						DB().del_reminder(member, reminder[0])
						if channel in guild.channels:
							await channel.send(embed=emb, content=member.mention)
						else:
							try:
								await member.send(embed=emb)
							except:
								pass

	@tasks.loop(seconds=5)
	async def channel_loop(self):
		for channel in DB().get_punishment():
			channel_time = channel[2]
			guild = self.client.get_guild(int(channel[1]))
			if channel[3] == "text_channel":
				if guild is not None:
					member = guild.get_member(int(channel[0]))
					if member is not None:
						if float(channel_time) <= float(time.time()):
							DB().del_punishment(
								member=member,
								guild_id=guild.id,
								type_punishment="text_channel",
							)
							delete_channel = guild.get_channel(int(channel[4]))
							await delete_channel.delete()

	@tasks.loop(minutes=30)
	async def ping_stat_loop(self):
		if self.client.is_ready():
			try:
				ping = round(self.client.latency * 1000)
				DB().add_amout_command(entity="ping", add_counter=int(ping))
			except:
				pass

	@tasks.loop(seconds=86400)
	async def update_messages_loop(self):
		data = DB().query_execute("""SELECT user_id, guild_id, messages FROM users""")

		for profile in data:
			if profile != []:
				all_message = json.loads(profile[2])[1]
				sql = """UPDATE users SET messages = %s WHERE user_id = %s AND guild_id = %s"""
				val = (json.dumps([0, all_message, None]), profile[0], profile[1])

				self.cursor.execute(sql, val)
				self.conn.commit()


def setup(client):
	client.add_cog(TasksOther(client))
