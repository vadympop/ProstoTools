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
		self.ban_loop.start()
		self.update_messages_loop.start()
		self.ping_stat_loop.start()
		self.FOOTER = configs['FOOTER_TEXT']


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

						emb = discord.Embed(description=f'**Вы были размьючены на сервере `{guild.name}`**', colour=discord.Color.green())
						emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
						emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
						await member.send(embed=emb)

	
	@tasks.loop(seconds=5)
	async def ban_loop(self):
		for ban in DB().get_punishment():
			ban_time = ban[2]
			guild = self.client.get_guild(int(ban[1]))
			if guild:
				bans = await guild.bans()
				for ban_entry in bans:
					user = ban_entry.user
					if user.id == ban[0]:
						if float(ban_time) <= float(time.time()):
							DB().del_punishment(member=user, guild_id=guild.id, type_punishment='ban')
							await guild.unban(user)

							emb = discord.Embed(description=f'**Вы были разбанены на сервере `{guild.name}`**', colour=discord.Color.green())
							emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
							emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
							try:
								await user.send(embed=emb)
							except:
								pass


	@tasks.loop(minutes=30)
	async def ping_stat_loop(self):
		if self.client.is_ready():
			ping = round(self.client.latency * 1000)
			DB().add_amout_command(entity='ping', add_counter=int(ping))

	
	@tasks.loop(seconds=86400)
	async def update_messages_loop(self):
		self.cursor.execute("""SELECT user_id, messages FROM users""")
		data = self.cursor.fetchall()

		for profile in data:
			if profile != []:
				all_message = profile[1][1]
				self.cursor.execute(("""UPDATE users SET messages = %s WHERE user_id = %s"""), (json.dumps([0, int(all_message), [None, None]]), int(profile[0])))
				self.conn.commit()



def setup( client ):
	client.add_cog(Loops(client))
		