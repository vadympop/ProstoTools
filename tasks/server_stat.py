import discord
import os
import json
import mysql.connector

from tools import DB

from configs import configs
from discord.ext import commands, tasks
from discord.utils import get


class TasksServerStat(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(
			user="root",
			password=os.environ["DB_PASSWORD"],
			host="localhost",
			database="data",
		)
		self.cursor = self.conn.cursor(buffered=True)
		self.server_stat_loop.start()
		self.FOOTER = configs["FOOTER_TEXT"]

	@tasks.loop(minutes=10)
	async def server_stat_loop(self):
		data = [
			(stat[0], json.loads(stat[1]))
			for stat in DB().query_execute(
				"""SELECT guild_id, server_stats FROM guilds"""
			)
		]

		for stat in data:
			if stat[1] != {}:
				for stat_type, channel_id in stat[1].items():
					if stat_type != "message":
						guild = self.client.get_guild(stat[0])
						if guild:
							try:
								counters = {
									"members": len(
										[
											member.id
											for member in guild.members
											if not member.bot
											and member.id != self.client.user.id
										]
									),
									"bots": len(
										[bot.id for bot in guild.members if bot.bot]
									),
									"channels": len(
										[channel.id for channel in guild.channels]
									),
									"roles": len([role.id for role in guild.roles]),
									"all": guild.member_count,
								}
								counter = counters[stat_type]
								channel = guild.get_channel(channel_id)
								numbers = "".join(
									char for char in channel.name if char.isdigit()
								)
								new_name = channel.name.replace(numbers, str(counter))

								await channel.edit(name=new_name)
							except:
								pass


def setup(client):
	client.add_cog(TasksServerStat(client))
