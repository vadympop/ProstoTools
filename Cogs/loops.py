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
		self.temprole_loop.start()
		self.vmute_loop.start()
		self.update_messages_loop.start()
		self.ping_stat_loop.start()
		self.server_stats.start()
		self.reminders_loop.start()
		self.FOOTER = configs['FOOTER_TEXT']


	@tasks.loop(seconds=5)
	async def reminders_loop(self):
		for reminder in DB().get_reminder():
			reminder_time = reminder[4]
			guild = self.client.get_guild(int(reminder[2]))
			if guild:
				member = guild.get_member(int(reminder[1]))
				channel = guild.get_channel(int(reminder[3]))
				emb = discord.Embed(title='Напоминания!', description=f'**Текст**:\n```{reminder[5]}```', colour=discord.Color.green())
				emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				if member:
					if float(reminder_time) <= float(time.time()):
						DB().del_reminder(reminder[2], reminder[0])
						if channel in guild.channels:
							await channel.send(embed=emb, content=member.mention)
						else:
							await member.send(embed=emb)

	@tasks.loop(seconds=5)
	async def mute_loop(self):
		for mute in DB().get_punishment():
			mute_time = mute[2]
			guild = self.client.get_guild(int(mute[1]))
			if mute[3] == 'mute':
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
							try:
								await member.send(embed=emb)
							except:
								pass

	
	@tasks.loop(seconds=5)
	async def ban_loop(self):
		for ban in DB().get_punishment():
			ban_time = ban[2]
			guild = self.client.get_guild(int(ban[1]))
			if ban[3] == 'ban':
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


	@tasks.loop(seconds=5)
	async def temprole_loop(self):
		for temprole in DB().get_punishment():
			temprole_time = temprole[2]
			guild = self.client.get_guild(int(temprole[1]))
			if temprole[3] == 'temprole':
				if guild:
					member = guild.get_member(int(temprole[0]))
					if member:
						if float(temprole_time) <= float(time.time()):
							DB().del_punishment(member=member, guild_id=guild.id, type_punishment='temprole')
							temprole_role = get(guild.roles, id=int(temprole[4]))
							await member.remove_roles(temprole_role)

	
	@tasks.loop(seconds=5)
	async def vmute_loop(self):
		for vmute in DB().get_punishment():
			vmute_time = vmute[2]
			guild = self.client.get_guild(int(vmute[1]))
			if vmute[3] == 'vmute':
				if guild:
					member = guild.get_member(int(vmute[0]))
					if member:
						if float(vmute_time) <= float(time.time()):
							DB().del_punishment(member=member, guild_id=guild.id, type_punishment='vmute')
							vmute_role = get(guild.roles, id=int(vmute[4]))
							await member.remove_roles(vmute_role)

							overwrite = discord.PermissionOverwrite(connect=None)
							for channel in guild.voice_channels:
								await channel.set_permissions(vmute_role, overwrite=overwrite)

							emb = discord.Embed(description=f'**Вы были размьючены в голосовых каналах на сервере `{guild.name}`**', colour=discord.Color.green())
							emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
							emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
							try:
								await member.send(embed=emb)
							except:
								pass

	
	@tasks.loop(minutes=30)
	async def ping_stat_loop(self):
		if self.client.is_ready():
			try:
				ping = round(self.client.latency * 1000)
				DB().add_amout_command(entity='ping', add_counter=int(ping))
			except:
				pass

	
	@tasks.loop(seconds=86400)
	async def update_messages_loop(self):
		self.cursor.execute("""SELECT user_id, guild_id, messages FROM users""")
		data = self.cursor.fetchall()

		for profile in data:
			if profile != []:
				all_message = json.loads(profile[2])[1]
				sql = ("""UPDATE users SET messages = %s WHERE user_id = %s AND guild_id = %s""")
				val = (json.dumps([0, all_message, None]), profile[0], profile[1])

				self.cursor.execute(sql, val)
				self.conn.commit()

	
	@tasks.loop(minutes=10)
	async def server_stats(self):
		self.cursor.execute("""SELECT guild_id, server_stats FROM guilds""")
		data = self.cursor.fetchall()
		data = [(stat[0], json.loads(stat[1])) for stat in data]

		for stat in data:
			if stat[1] != {}:
				for stat_type, channel_id in stat[1].items():
					guild = self.client.get_guild(stat[0])
					if guild:
						try:
							counters = {
								'members': len([member.id for member in guild.members if not member.bot and member.id != self.client.user.id]),
								'bots': len([bot.id for bot in guild.members if bot.bot]),
								'channels': len([channel.id for channel in guild.channels]),
								'roles': len([role.id for role in guild.roles]),
								'all': guild.member_count
							}
							counter = counters[stat_type]
							channel = guild.get_channel(channel_id)
							if counter >= 100:
								stats_channel_name = channel.name[6:]
							elif counter >= 10:
								stats_channel_name = channel.name[5:]
							elif counter < 10:
								stats_channel_name = channel.name[4:]

							await channel.edit( name = f'[{counter}] {stats_channel_name}' )
						except:
							pass

					
def setup( client ):
	client.add_cog(Loops(client))
		