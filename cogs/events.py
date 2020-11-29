import discord
import os
import json
import random
import asyncio
import math
import datetime
import colorama
import mysql.connector

from .tools import Commands
from .tools import DB

from colorama import *
from discord.ext import commands
from discord.utils import get
from random import randint
from configs import configs

init()


class Events(commands.Cog, name="Events"):
	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(
			user="root",
			password=os.environ["DB_PASSWORD"],
			host="localhost",
			database="data",
		)
		self.cursor = self.conn.cursor(buffered=True)
		self.FOOTER = configs["FOOTER_TEXT"]
		self.MUTE_ROLE = configs["MUTE_ROLE"]
		self.HELP_SERVER = configs["HELP_SERVER"]


	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		emb = discord.Embed(
			title="Спасибо за приглашения нашего бота! Мы вам всегда рады",
			description=f"**Стандартний префикс - *, команда помощи - *help, \nкоманда настроёк - *settings. Наш сервер поддержки: \n {self.HELP_SERVER}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(
			text="ProstoChelovek and Mr.Kola Copyright",
			icon_url=self.client.user.avatar_url,
		)
		await guild.text_channels[0].send(embed=emb)

		DB().sel_guild(guild=guild)
		DB().add_amout_command(entity="guilds", add_counter=len(self.client.guilds))

		for member in guild.members:
			if not member.bot:
				DB().sel_user(target=member)

		guild_owner_bot = self.client.get_guild(717776571406090310)
		channel = guild_owner_bot.text_channels[3]
		invite = await guild.text_channels[0].create_invite(
			reason="For more information"
		)

		emb_info = discord.Embed(
			title=f"Бот добавлен на новый сервер, всего серверов - {len(self.client.guilds)}",
			description=f"Названия сервера - `{guild.name}`\nАйди сервера - `{guild.id}`\nИнвайт - {invite}\nВладелец - `{guild.owner}`\nКол-во участников - `{guild.member_count}`",
		)
		emb_info.set_thumbnail(url=guild.icon_url)
		await channel.send(embed=emb_info)

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		DB().add_amout_command(entity="guilds", add_counter=len(self.client.guilds))

		val = (guild.id, guild.id)
		sql_1 = """DELETE FROM guilds WHERE guild_id = %s AND guild_id = %s"""
		sql_2 = """DELETE FROM mutes WHERE guild_id = %s AND guild_id = %s"""
		sql_3 = """DELETE FROM punishments WHERE guild_id = %s AND guild_id = %s"""
		sql_4 = """DELETE FROM reminders WHERE guild_id = %s AND guild_id = %s"""
		sql_5 = """DELETE FROM warns WHERE guild_id = %s AND guild_id = %s"""

		self.cursor.execute(sql_1, val)
		self.cursor.execute(sql_2, val)
		self.cursor.execute(sql_3, val)
		self.cursor.execute(sql_4, val)
		self.cursor.execute(sql_5, val)
		self.conn.commit()

		for member in guild.members:
			sql_2 = """DELETE FROM users WHERE user_id = %s AND guild_id = %s"""
			val_2 = (member.id, guild.id)

			self.cursor.execute(sql_2, val_2)
			self.conn.commit()

		guild_owner_bot = self.client.get_guild(717776571406090310)
		channel = guild_owner_bot.text_channels[3]

		emb_info = discord.Embed(
			title=f"Бот изгнан из сервера, всего серверов - {len(self.client.guilds)}",
			description=f"Названия сервера - `{guild.name}`\nАйди сервера - `{guild.id}`\nВладелец - `{guild.owner}`\nКол-во участников - `{guild.member_count}`",
		)
		emb_info.set_thumbnail(url=guild.icon_url)

		await channel.send(embed=emb_info)

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		reaction = payload.emoji
		author = payload.member
		channel = self.client.get_channel(payload.channel_id)
		message = await channel.fetch_message(payload.message_id)
		member = message.author
		guild = message.guild
		if guild:
			data = DB().sel_guild(guild=guild)

			if data["auto_mod"]["react_coomands"]:
				if not author.bot:
					if author.guild_permissions.administrator:
						if reaction.name == "❌":
							try:
								await member.ban(reason="Нарушения правил")
							except:
								return

							emb = discord.Embed(
								description=f"**{author.mention} Забанил {member.mention}**",
								colour=discord.Color.green(),
							)
							emb.set_author(name=author.name, icon_url=author.avatar_url)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await message.channel.send(embed=emb)

							emb = discord.Embed(
								description=f"**Вы были забанены на сервере {message.guild.name}**",
								colour=discord.Color.green(),
							)
							emb.set_author(name=author.name, icon_url=author.avatar_url)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await member.send(embed=emb)
						elif reaction.name == "🤐":
							emb = await Commands(self.client).main_mute(
								ctx=message,
								member=member,
								reason="Команды по реакциям: Нарушения правил",
								check_role=True,
							)
							await message.channel.send(embed=emb)
						elif reaction.name == "💀":
							await member.kick(reason="Нарушения правил")

							emb = discord.Embed(
								description=f"**{author.mention} Кикнул {member.mention}**",
								colour=discord.Color.green(),
							)
							emb.set_author(name=author.name, icon_url=author.avatar_url)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await message.channel.send(embed=emb)

							emb = discord.Embed(
								description=f"**Администратор {author.mention} кикнул вас из сервера** ***{guild.name}***",
								colour=discord.Color.green(),
							)
							emb.set_author(name=author.name, icon_url=author.avatar_url)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await member.send(embed=emb)

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		val = (member.id, member.id)
		sql_1 = """DELETE FROM mutes WHERE user_id = %s AND user_id = %s"""
		sql_2 = """DELETE FROM punishments WHERE member_id = %s AND member_id = %s"""
		sql_3 = """DELETE FROM reminders WHERE user_id = %s AND user_id = %s"""
		sql_4 = """DELETE FROM warns WHERE user_id = %s AND user_id = %s"""

		self.cursor.execute(sql_1, val)
		self.cursor.execute(sql_2, val)
		self.cursor.execute(sql_3, val)
		self.cursor.execute(sql_4, val)
		self.conn.commit()

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		channel_id = DB().sel_guild(guild=before.guild)["log_channel"]
		if channel_id == 0:
			return
		channel = self.client.get_channel(channel_id)

		if not len(before.roles) == len(after.roles):
			roles = []
			if len(before.roles) > len(after.roles):
				for i in before.roles:
					if not i in after.roles:
						roles.append(f"➖ Была убрана роль {i.name}(<@&{i.id}>)\n")
			elif len(before.roles) < len(after.roles):
				for i in after.roles:
					if not i in before.roles:
						roles.append(f"➕ Была добавлена роль {i.name}(<@&{i.id}>)\n")

			e = discord.Embed(
				description=f"У пользователя `{str(after)}` были изменены роли",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name="Было сделано", value=f"**{''.join(roles)}**", inline=False
			)
			e.add_field(name="Id Участника", value=f"`{after.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Изменение ролей участника",
				icon_url=before.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await channel.send(embed=e)

		if not before.display_name == after.display_name:
			e = discord.Embed(
				description=f"Пользователь `{str(before)}` изменил ник",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name="Действующее имя",
				value=f"`{after.display_name+'#'+after.discriminator}`",
				inline=False,
			)
			e.add_field(
				name="Предыдущее имя",
				value=f"`{before.display_name+'#'+before.discriminator}`",
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{after.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Изменение ника участника",
				icon_url=before.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_member_ban(self, guild, user):
		if user.bot:
			return

		channel_id = DB().sel_guild(guild=guild)["log_channel"]
		if channel_id == 0:
			return
		channel = self.client.get_channel(channel_id)
		ban = await guild.fetch_ban(user)
		e = discord.Embed(
			description=f"Пользователь `{str(user)}` был забанен",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow(),
		)
		e.add_field(
			name="Причина бана",
			value=f"""`{'Причина не указана' if not ban.reason else ban.reason}`""",
			inline=False,
		)
		e.add_field(name="Id Участника", value=f"`{user.id}`", inline=False)
		e.set_author(name="Журнал аудита | Бан пользователя", icon_url=user.avatar_url)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_member_unban(self, guild, user):
		if user.bot:
			return

		channel_id = DB().sel_guild(guild=guild)["log_channel"]
		if channel_id == 0:
			return
		channel = self.client.get_channel(channel_id)
		e = discord.Embed(
			description=f"Пользователь `{str(user)}` был разбанен",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow(),
		)
		e.add_field(name="Id Участника", value=f"`{user.id}`", inline=False)
		e.set_author(
			name="Журнал аудита | Разбан пользователя", icon_url=user.avatar_url
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_command(self, ctx):
		DB().add_amout_command(entity=ctx.command.name)

	@commands.Cog.listener()
	async def on_message_delete(self, message):
		if message.author.bot:
			return

		channel_id = DB().sel_guild(guild=message.guild)["log_channel"]
		if channel_id == 0:
			return
		channel = self.client.get_channel(channel_id)
		e = discord.Embed(
			colour=discord.Color.green(), timestamp=datetime.datetime.utcnow()
		)
		e.add_field(
			name="Удалённое сообщение",
			value=f"```{message.content}```"
			if message.content
			else "Сообщения отсутствует ",
			inline=False,
		)
		e.add_field(
			name="Автор сообщения", value=f"`{str(message.author)}`", inline=False
		)
		e.add_field(name="Канал", value=f"`{message.channel.name}`", inline=False)
		e.add_field(name="Id Сообщения", value=f"`{message.id}`", inline=False)
		e.set_author(
			name="Журнал аудита | Удаление сообщения",
			icon_url=message.author.avatar_url,
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_message_edit(self, before, after):
		if before.content == after.content:
			return

		if before.author.bot:
			return

		channel_id = DB().sel_guild(guild=before.guild)["log_channel"]
		if channel_id == 0:
			return
		channel = self.client.get_channel(channel_id)
		e = discord.Embed(
			description=f"**[Сообщение]({before.jump_url}) было изменено**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow(),
		)
		e.add_field(
			name="Старое содержимое", value=f"```{before.content}```", inline=False
		)
		e.add_field(
			name="Новое соодержиое", value=f"```{after.content}```", inline=False
		)
		e.add_field(name="Автор", value=f"`{str(before.author)}`", inline=False)
		e.add_field(name="Канал", value=f"`{before.channel.name}`", inline=False)
		e.add_field(name="Id Сообщения", value=f"`{before.id}`", inline=False)
		e.set_author(
			name="Журнал аудита | Изменение сообщения",
			icon_url=before.author.avatar_url,
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author.bot:
			return
		elif not message.guild:
			return
		else:
			role = get(message.guild.roles, name=self.MUTE_ROLE)
			if role in message.author.roles:
				await message.delete()

			guild_data = DB().sel_guild(guild=message.guild)
			data = DB().sel_user(target=message.author)

			if message.channel.id in guild_data["react_channels"]:
				await message.add_reaction("👍")
				await message.add_reaction("👎")

			all_message = guild_data["all_message"]
			guild_moder_settings = guild_data["auto_mod"]
			multi = guild_data["exp_multi"]
			ignored_channels = guild_data["ignored_channels"]
			all_message += 1

			scr = """UPDATE guilds SET all_message = %s WHERE guild_id = %s AND guild_id = %s"""
			val_1 = (all_message, message.guild.id, message.guild.id)

			self.cursor.execute(scr, val_1)
			self.conn.commit()

			if ignored_channels != []:
				if message.channel.id in ignored_channels:
					return

			rand_number_1 = randint(1, 5)
			exp_first = rand_number_1
			coins_first = exp_first // 2 + 1

			exp_member = data["exp"]
			coins_member = data["coins"]
			exp = exp_first + exp_member
			coins = coins_first + coins_member
			reputation = data["reputation"]
			messages = data["messages"]
			lvl_member = data["lvl"]
			last_msg = messages[2]

			reput_msg = 150
			messages[0] += 1
			messages[1] += 1
			messages[2] = message.content

			exp_end = math.floor(9 * (lvl_member ** 2) + 50 * lvl_member + 125 * multi)
			if exp_end < exp:
				lvl_member += 1
				emb_lvl = discord.Embed(
					title="Сообщения о повышении уровня",
					description=f"Участник {message.author.mention} повысил свой уровень! Текущий уровень - `{lvl_member}`",
					timestamp=datetime.datetime.utcnow(),
					colour=discord.Color.green(),
				)

				emb_lvl.set_author(
					name=message.author.name, icon_url=message.author.avatar_url
				)
				emb_lvl.set_footer(
					text=self.FOOTER, icon_url=self.client.user.avatar_url
				)

				await message.channel.send(embed=emb_lvl)

			if messages[0] >= reput_msg:
				reputation += 1
				messages[0] = 0

			if reputation >= 100:
				reputation = 100

			sql = """UPDATE users SET exp = %s, coins = %s, reputation = %s, messages = %s, level = %s WHERE user_id = %s AND guild_id = %s"""
			val = (
				exp,
				coins,
				reputation,
				json.dumps(messages),
				lvl_member,
				message.author.id,
				message.guild.id,
			)

			self.cursor.execute(sql, val)
			self.conn.commit()

			try:
				await self.client.wait_for("message", check=lambda m: m.content == last_msg and m.channel == message.channel, timeout=2.0)
			except asyncio.TimeoutError:
				pass
			else:
				if guild_moder_settings["anti_flud"]:
					emb = await Commands(self.client).main_mute(
						ctx=message,
						member=message.author,
						mute_time=4,
						mute_typetime="h",
						reason="Авто-модерация: Флуд",
					)
					if emb is not None:
						await message.channel.send(embed=emb)

	@commands.Cog.listener()
	async def on_voice_state_update(self, member, before, after):
		data = DB().sel_guild(guild=member.guild)["voice_channel"]
		if data != {}:
			main_channel = data["channel_id"]
			main_channel_obj = self.client.get_channel(int(main_channel))
			category = main_channel_obj.category

		try:
			if after.channel.id == main_channel:
				if before.channel is None and after.channel:

					overwrites = {
						member.guild.default_role: discord.PermissionOverwrite(
							connect=False, manage_permissions=False
						),
						member: discord.PermissionOverwrite(
							connect=True, manage_permissions=True, manage_channels=True
						),
						self.client.user: discord.PermissionOverwrite(
							connect=True, manage_permissions=True, manage_channels=True
						),
					}

					member_channel = await member.guild.create_voice_channel(
						name=f"{member.name} Channel",
						overwrites=overwrites,
						category=category,
						guild=member.guild,
					)
					await member.move_to(member_channel)
					await self.client.wait_for(
						"voice_state_update", 
						check=lambda a, b, c: len(member_channel.members) <= 0
					)
					await member_channel.delete()
			else:
				return
		except:
			pass


def setup(client):
	client.add_cog(Events(client))
