import discord
import datetime
import os
import json
import random
import asyncio
import time
from configs import configs
from Tools.database import DB
from discord.ext import commands, tasks
from discord.utils import get
from discord.ext.commands import Bot


class Loops(commands.Cog, name = 'Loops'):

	def __init__(self, client):
		self.client = client
		self.mute_loop.start()
		self.reputLoop.start()
		self.ping_stat_loop.start()


	@tasks.loop(seconds=5)
	async def mute_loop(self):
		print("Mute loop 5 second")
		print(DB().get_punishment())
		for mute in DB().get_punishment():
			print(mute)
			print("Good punishment")
			time = mute[2]
			guild = self.client.get_guild(int(mute[1]))
			if guild:
				member = guild.get_member(int(mute[0]))
				if member:
					if float(time) <= float(time.time()):
						print("Delete punishment")
						DB.set_punishment(type_punishment='mute', time=0, member=member)
						mute_role = get(guild.roles, name=configs['MUTE_ROLE'])
						await member.remove_roles(mute_role)


	@tasks.loop(seconds=5)
	async def ping_stat_loop(self):
		ping = round(self.client.latency * 1000)
		print(ping)
		DB().add_amout_command(entity='ping', add_counter=int(ping))

	
	@tasks.loop( seconds = 86400 )
	async def reputLoop(self):
		self.cursor.execute("""SELECT * FROM users""")
		data = self.cursor.fetchall()

		for profile in data:
			if profile != []:
				all_message = profile[14][1]
				self.cursor.execute("""UPDATE users SET messages = %s WHERE user_id = %s AND guild_id = %s""", (json.dumps([0, all_message, [None, None]])), profile[0], profile[1])
				self.conn.commit()



def setup( client ):
	client.add_cog(Loops(client))
		