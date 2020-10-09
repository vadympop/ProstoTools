import discord
import datetime
import os
import json
import random
import asyncio
import time
import mysql.connector
from configs import configs
from Tools.database import DB
from discord.ext import commands, tasks
from discord.utils import get
from discord.ext.commands import Bot


class Loops(commands.Cog, name = 'Loops'):

	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(user = 'root', password = os.environ['DB_PASSWORD'], host = 'localhost', database = 'data')
		self.cursor = self.conn.cursor(buffered = True)
		self.mute_loop.start()
		self.reputLoop.start()
		self.ping_stat_loop.start()


	@tasks.loop(seconds=5)
	async def mute_loop(self):
		for mute in DB().get_punishment():
			mute_time = mute[2]
			guild = self.client.get_guild(int(mute[1]))
			if guild:
				member = guild.get_member(int(mute[0]))
				if member:
					if float(mute_time) <= float(time.time()):
						DB().del_punishment(member=member, guild_id=guild.id, type_punishment='mute')
						mute_role = get(guild.roles, id=int(mute[4]))
						await member.remove_roles(mute_role)


	@tasks.loop(minutes=30)
	async def ping_stat_loop(self):
		if self.client.is_ready():
			ping = round(self.client.latency * 1000)
			DB().add_amout_command(entity='ping', add_counter=int(ping))

	
	@tasks.loop(seconds=86400)
	async def reputLoop(self):
		self.cursor.execute("""SELECT user_id, messages FROM users""")
		data = self.cursor.fetchall()

		for profile in data:
			if profile != []:
				all_message = profile[1][1]
				self.cursor.execute(("""UPDATE users SET messages = %s WHERE user_id = %s"""), (json.dumps([0, int(all_message), [None, None]]), int(profile[0])))
				self.conn.commit()



def setup( client ):
	client.add_cog(Loops(client))
		