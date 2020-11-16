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


class Loops(commands.Cog, name="Loops"):
	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(
			user="root",
			password=os.environ["DB_PASSWORD"],
			host="localhost",
			database="data",
		)
		self.cursor = self.conn.cursor(buffered=True)
		self.mute_loop.start()
		self.ban_loop.start()
		self.temprole_loop.start()
		self.vmute_loop.start()
		self.update_messages_loop.start()
		self.ping_stat_loop.start()
		self.server_stats.start()
		self.reminders_loop.start()
		self.message_stat_loop.start()
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
						DB().del_reminder(reminder[2], reminder[0])
						if channel in guild.channels:
							await channel.send(embed=emb, content=member.mention)
						else:
							try:
								await member.send(embed=emb)
							except:
								pass

	@tasks.loop(seconds=5)
	async def mute_loop(self):
		for mute in DB().get_punishment():
			mute_time = mute[2]
			guild = self.client.get_guild(int(mute[1]))
			if mute[3] == "mute":
				if guild is not None:
					member = guild.get_member(int(mute[0]))
					if member is not None:
						if float(mute_time) <= float(time.time()):
							DB().del_punishment(
								member=member, guild_id=guild.id, type_punishment="mute"
							)
							mute_role = await guild.get_role(int(mute[4]))
							await member.remove_roles(mute_role)

							emb = discord.Embed(
								description=f"**Вы были размьючены на сервере `{guild.name}`**",
								colour=discord.Color.green(),
							)
							emb.set_author(
								name=self.client.user.name,
								icon_url=self.client.user.avatar_url,
							)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							try:
								await member.send(embed=emb)
							except:
								pass

	@tasks.loop(seconds=5)
	async def ban_loop(self):
		for ban in DB().get_punishment():
			ban_time = ban[2]
			guild = self.client.get_guild(int(ban[1]))
			if ban[3] == "ban":
				if guild is not None:
					bans = await guild.bans()
					for ban_entry in bans:
						user = ban_entry.user
						if user.id == ban[0]:
							if float(ban_time) <= float(time.time()):
								DB().del_punishment(
									member=user,
									guild_id=guild.id,
									type_punishment="ban",
								)
								await guild.unban(user)

								emb = discord.Embed(
									description=f"**Вы были разбанены на сервере `{guild.name}`**",
									colour=discord.Color.green(),
								)
								emb.set_author(
									name=self.client.user.name,
									icon_url=self.client.user.avatar_url,
								)
								emb.set_footer(
									text=self.FOOTER,
									icon_url=self.client.user.avatar_url,
								)
								try:
									await user.send(embed=emb)
								except:
									pass

	@tasks.loop(seconds=5)
	async def temprole_loop(self):
		for temprole in DB().get_punishment():
			temprole_time = temprole[2]
			guild = self.client.get_guild(int(temprole[1]))
			if temprole[3] == "temprole":
				if guild is not None:
					member = guild.get_member(int(temprole[0]))
					if member is not None:
						if float(temprole_time) <= float(time.time()):
							DB().del_punishment(
								member=member,
								guild_id=guild.id,
								type_punishment="temprole",
							)
							temprole_role = get(guild.roles, id=int(temprole[4]))
							await member.remove_roles(temprole_role)

	@tasks.loop(seconds=5)
	async def vmute_loop(self):
		for vmute in DB().get_punishment():
			vmute_time = vmute[2]
			guild = self.client.get_guild(int(vmute[1]))
			if vmute[3] == "vmute":
				if guild is not None:
					member = guild.get_member(int(vmute[0]))
					if member is not None:
						if float(vmute_time) <= float(time.time()):
							DB().del_punishment(
								member=member,
								guild_id=guild.id,
								type_punishment="vmute",
							)
							vmute_role = await guild.get_role(int(vmute[4]))
							await member.remove_roles(vmute_role)

							overwrite = discord.PermissionOverwrite(connect=None)
							for channel in guild.voice_channels:
								await channel.set_permissions(
									vmute_role, overwrite=overwrite
								)

							emb = discord.Embed(
								description=f"**Вы были размьючены в голосовых каналах на сервере `{guild.name}`**",
								colour=discord.Color.green(),
							)
							emb.set_author(
								name=self.client.user.name,
								icon_url=self.client.user.avatar_url,
							)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
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

	@tasks.loop(minutes=5)
	async def message_stat_loop(self):
		for guild in self.client.guilds:
			data_guild = DB().sel_guild(guild=guild)
			if "message" in data_guild["server_stats"].keys():
				message = await guild.get_channel(data_guild["server_stats"]["message"][1]).fetch_message(
					data_guild["server_stats"]["message"][0]
				)
				if message is not None:
					val = (guild.id, guild.id)
					sql_1 = """SELECT user_id, exp, money, reputation, messages FROM users WHERE guild_id = %s AND guild_id = %s ORDER BY exp DESC LIMIT 20"""
					sql_2 = """SELECT exp FROM users WHERE guild_id = %s AND guild_id = %s"""

					data = DB().query_execute(sql_1, val)
					all_exp = sum([i[0] for i in DB().query_execute(sql_2, val)])
					dnd = len(
						[
							str(member.id)
							for member in guild.members
							if member.status.name == "dnd"
						]
					)
					sleep = len(
						[
							str(member.id)
							for member in guild.members
							if member.status.name == "idle"
						]
					)
					online = len(
						[
							str(member.id)
							for member in guild.members
							if member.status.name == "online"
						]
					)
					offline = len(
						[
							str(member.id)
							for member in guild.members
							if member.status.name == "offline"
						]
					)
					description = "Статистика обновляеться каждые 5 минут\n\n**20 Самых активных участников сервера**"
					num = 1
					for profile in data:
						member = guild.get_member(profile[0])
						if member is not None:
							if not member.bot:
								if len(member.name) > 15:
									member = member.name[:len(member.name)-15]+"..."+member.discriminator
								description += f"""\n`{num}. {str(member)} {profile[1]}exp {profile[2]}$ {profile[3]}rep {json.loads(profile[4])[1]}msg`"""
								num += 1
					
					description += f"""
					\n**Общая инфомация**
					:baby:Пользователей: **{guild.member_count}**
					:family_man_girl_boy:Участников: **{len([m.id for m in guild.members if not m.bot])}**
					<:bot:731819847905837066>Ботов: **{len([m.id for m in guild.members if m.bot])}**
					<:voice_channel:730399079418429561>Голосовых подключений: **{sum([len(v.members) for v in guild.voice_channels])}**
					<:text_channel:730396561326211103>Каналов: **{len([c.id for c in guild.channels])}**
					<:role:730396229220958258>Ролей: **{len([r.id for r in guild.roles])}**
					:star:Всего опыта: **{all_exp}**\n
					**Статусы участников**
					<:online:730393440046809108>`{online}`  <:offline:730392846573633626>`{offline}`
					<:sleep:730390502972850256>`{sleep}`  <:mobile:777854822300385291>`{len([m.id for m in guild.members if m.is_on_mobile()])}`
					<:dnd:730391353929760870>`{dnd}`  <:boost:777854437724127272>`{len(set(guild.premium_subscribers))}`
					"""

					emb = discord.Embed(
						title="Статистика сервера",
						description=description,
						colour=discord.Color.green()
					)
					emb.set_author(
						name=self.client.user.name, icon_url=self.client.user.avatar_url
					)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await message.edit(embed=emb)

	@tasks.loop(minutes=10)
	async def server_stats(self):
		data = [(stat[0], json.loads(stat[1])) for stat in DB().query_execute("""SELECT guild_id, server_stats FROM guilds""")]

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
							except Exception as e:
								raise (e)


def setup(client):
	client.add_cog(Loops(client))
