import discord
import mysql.connector
import json
import typing
import os

from tools import DB

from discord.ext import commands
from discord.utils import get
from configs import configs


def clear_commands(guild):

	data = DB().sel_guild(guild=guild)
	purge = data["purge"]
	return purge


global Footer
Footer = configs["FOOTER_TEXT"]


class Settings(commands.Cog, name="Settings"):
	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(
			user="root",
			password=os.environ["DB_PASSWORD"],
			host="localhost",
			database="data",
		)
		self.cursor = self.conn.cursor(buffered=True)

	@commands.group()
	@commands.has_permissions(administrator=True)
	async def setting(self, ctx):
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

	@setting.command(
		hidden=True,
		description="**Настройка префикса**",
		usage="setting prefix [Новый префикс]",
	)
	async def prefix(self, ctx, prefix: str):
		client = self.client
		if len(prefix) > 3:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Количество символов в новом префиксе не должно превышать 3-х!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
			return

		sql = """UPDATE guilds SET prefix = %s WHERE guild_id = %s AND guild_id = %s"""
		val = (prefix, ctx.guild.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		emb = discord.Embed(
			description=f"**Вы успешно изменили префикс бота на этом сервере. Новый префикс {prefix}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
		emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
		await ctx.send(embed=emb)

	@setting.command(
		hidden=True,
		name="moderation-role",
		description="**Настройка ролей модераторов**",
		usage="setting moderation-role [add(Добавляет указаную роль)/clear(Очищает список)/del(Удаляет указаную роль)] |@Роль|",
	)
	async def moder_role(self, ctx, type_act: str, role: discord.Role = None):
		client = self.client
		data = DB().sel_guild(guild=ctx.guild)
		cur_roles = data["moder_roles"]

		if type_act == "add":
			cur_roles.append(role.id)
			emb = discord.Embed(
				description=f"**Вы успешно добавили новую роль модератора! Добавлённая роль - `{role.name}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
		elif type_act == "clear":
			cur_roles = []
			emb = discord.Embed(
				description=f"**Вы успешно очистили список ролей модераторов!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
		elif type_act == "delete":
			try:
				cur_roles.remove(role.id)
			except ValueError:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**Такой роли нету в списке ролей модераторов!**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
				emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
				await ctx.send(embed=emb)
				return

			emb = discord.Embed(
				description=f"**Вы успешно удалили роль из ролей модераторов! Удалённая роль - `{role.name}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
		elif type_act != "clear" and type_act != "add":
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не правильно указали действие!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
			return

		sql = """UPDATE guilds SET moderators = %s WHERE guild_id = %s AND guild_id = %s"""
		val = (json.dumps(cur_roles), ctx.guild.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

	@setting.command(
		hidden=True,
		name="ignore-channels",
		description="**Игнорируемые каналы в системе уровней**",
		usage="setting ignore-channels [Действие, add - добавляет канал в исключения, clear - очищает список исключений, delete - удаляет указаный канал из списка] [Id канала]",
	)
	async def ignoredchannels(self, ctx, typech: str, channel: int = 0):
		client = self.client
		data = DB().sel_guild(guild=ctx.guild)
		channel_obg = get(ctx.guild.text_channels, id=channel)
		cur_ignchannel = data["ignored_channels"]

		if typech == "add":
			cur_ignchannel.append(channel)
			emb = discord.Embed(
				description=f"**Вы успешно добавили новий канал в исключения! Добавлённый канал - {channel_obg.mention}**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
		elif typech == "clear":
			cur_ignchannel = []
			emb = discord.Embed(
				description=f"**Вы успешно очистили список исключенных каналов!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
		elif typech == "delete":
			try:
				cur_ignchannel.remove(channel)
			except ValueError:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**Такого канала нету в списке игнорируемых каналов!**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
				emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
				await ctx.send(embed=emb)
				return

			emb = discord.Embed(
				description=f"**Вы успешно удалили канал из исключений! Удалённый канал - {channel_obg.mention}**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
		elif typech != "clear" and typech != "add":
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не правильно указали действие!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
			return

		sql = """UPDATE guilds SET ignored_channels = %s WHERE guild_id = %s AND guild_id = %s"""
		val = (json.dumps(cur_ignchannel), ctx.guild.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

	@setting.command(
		hidden=True,
		description="**Настройка авто удаления команд**",
		usage="setting purge [1 = Бот будет удалять свои команды, 0 = Бот не будет удалять свои команды]",
	)
	async def purge(self, ctx, purge_num: int):
		client = self.client
		if purge_num != 1 and purge_num != 0:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Введите значения правильно! Инструкции - {Prefix}settings **",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
			return
		elif purge_num == 1 or purge_num == 0:
			sql = """UPDATE guilds SET `purge` = %s WHERE guild_id = %s AND guild_id = %s"""
			val = (purge_num, ctx.guild.id, ctx.guild.id)

			self.cursor.execute(sql, val)
			self.conn.commit()

			emb = discord.Embed(
				description=f"**Вы успешно изменили значения! Новое значения - {purge_num}**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)

	@setting.command(
		hidden=True,
		name="shop-role",
		description="**Настройка магазина на сервере**",
		usage="setting shop-role [clear - очищает список ролей, add - добавляет роль, delete - удаляет роль] [@Роль] [Стоимость роли]",
	)
	async def shoplist(
		self, ctx, cl_add: typing.Optional[str], role: discord.Role, cost: int
	):
		client = self.client
		data = DB().sel_guild(guild=ctx.guild)
		shoplist = data["shop_list"]

		if cl_add == "add":
			shoplist.append([role.id, cost])
			emb = discord.Embed(
				description=f"**Добавленна новая роль - `{role}`, стоимость - `{cost}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
		elif cl_add == "clear":
			shoplist = []
			emb = discord.Embed(
				description=f"**Ваш список продаваемых ролей успешно очищен**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
		elif cl_add == "delete" or cl_add == "remove" or cl_add == "del":
			try:
				for shop_role in shoplist:
					if role.id in shop_role and cost in shop_role:
						shoplist.remove(shop_role)
			except:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**Такой роли не существует в списке продаваемых ролей!**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
				emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
				await ctx.send(embed=emb)
				return

			emb = discord.Embed(
				description=f"**Вы успешно удалили продаваемую роль из списка продаваемых ролей! Удалённая роль - `{role}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
		elif cl_add != "clear" and cl_add != "add":
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не правильно указали действие!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		sql = (
			"""UPDATE guilds SET shop_list = %s WHERE guild_id = %s AND guild_id = %s"""
		)
		val = (json.dumps(shoplist), ctx.guild.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

	@setting.command(
		hidden=True,
		name="text-channels-category",
		description="**Настройка категории приватных текстовых каналов**",
		usage="setting text-channels-category [Id категории]",
	)
	async def privatetextcategory(self, ctx, category: int):
		client = self.client
		category = get(ctx.guild.categories, id=category)
		if category in ctx.guild.categories:
			sql = """UPDATE guilds SET textchannels_category = %s WHERE guild_id = %s AND guild_id = %s"""
			val = (category.id, ctx.guild.id, ctx.guild.id)

			self.cursor.execute(sql, val)
			self.conn.commit()

			emb = discord.Embed(
				description=f"**Вы успешно настроили категорию для приватних текстовых каналов! Новая категория - {category.name}**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Такой категории не существует введите id правильно**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

	@setting.command(
		hidden=True,
		name="max-warns",
		description="**Настройка максимального количества предупрежденний**",
		usage="setting max-warns [Любое число]",
	)
	async def maxwarns(self, ctx, number: int):
		client = self.client
		if number >= 25:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы указали слишком большой лимит предупреждений!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		sql = (
			"""UPDATE guilds SET max_warns = %s WHERE guild_id = %s AND guild_id = %s"""
		)
		val = (number, ctx.guild.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		emb = discord.Embed(
			description=f"**Вы успешно настроили максимальное количество предупрежденний! Новое значения - `{number}`**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
		emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
		await ctx.send(embed=emb)

	@setting.command(
		hidden=True,
		name="anti-flud",
		description="**Настройка анти-флуда(Бета-тест)**",
		usage="setting anti-flud [on/off]",
	)
	async def anti_flud(self, ctx, action: str):
		client = self.client
		actions = ["on", "off", "true", "false", "0", "1"]
		if action.lower() not in actions:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не правильно указали действие! Укажите из этих вариантов: on(Вкл.), off(Выкл.), true(Вкл.), false(Выкл.), 0(Вкл.), 1(Выкл.)**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		data = DB().sel_guild(guild=ctx.guild)
		emb = discord.Embed(
			description=f"**Настройки анти-флуда успешно обновленны!**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
		emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
		await ctx.send(embed=emb)

		if action.lower() == "on" or action.lower() == "true" or action.lower() == "1":
			action = True
		elif (
			action.lower() == "off"
			or action.lower() == "false"
			or action.lower() == "0"
		):
			action = False

		settings = data["auto_mod"]
		settings.update({"anti_flud": action})

		sql = (
			"""UPDATE guilds SET auto_mod = %s WHERE guild_id = %s AND guild_id = %s"""
		)
		val = (json.dumps(settings), ctx.guild.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

	@setting.command(
		hidden=True,
		name="auto-rade-mode",
		description="**Настройка авто-рейд-режима(В разработке)**",
		usage="setting auto-rade-mode [on/off]",
	)
	async def auto_rade_mode(self, ctx, action: str):
		client = self.client
		actions = ["on", "off", "true", "false", "0", "1"]
		if action.lower() not in actions:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не правильно указали действие! Укажите из этих вариантов: on(Вкл.), off(Выкл.), true(Вкл.), false(Выкл.), 0(Вкл.), 1(Выкл.)**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		data = DB().sel_guild(guild=ctx.guild)
		emb = discord.Embed(
			description=f"**Настройки анти-рейд-режима успешно обновленны!**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
		emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
		await ctx.send(embed=emb)

		if action.lower() == "on" or action.lower() == "true" or action.lower() == "1":
			action = True
		elif (
			action.lower() == "off"
			or action.lower() == "false"
			or action.lower() == "0"
		):
			action = False

		settings = data["auto_mod"]
		settings.update({"auto_anti_rade_mode": action})

		sql = (
			"""UPDATE guilds SET auto_mod = %s WHERE guild_id = %s AND guild_id = %s"""
		)
		val = (json.dumps(settings), ctx.guild.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

	@setting.command(
		hidden=True,
		name="react-commands",
		description="**Настройка команд по реакциям**",
		usage="setting react-commands [on/off]",
	)
	async def react_commands(self, ctx, action: str):
		client = self.client
		actions = ["on", "off", "true", "false", "0", "1"]
		if action.lower() not in actions:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не правильно указали действие! Укажите из этих вариантов: on(Вкл.), off(Выкл.), true(Вкл.), false(Выкл.), 0(Вкл.), 1(Выкл.)**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		data = DB().sel_guild(guild=ctx.guild)
		emb = discord.Embed(
			description=f"**Настройки команд по реакциям успешно обновленны!**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
		emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
		await ctx.send(embed=emb)

		if action.lower() == "on" or action.lower() == "true" or action.lower() == "1":
			action = True
		elif (
			action.lower() == "off"
			or action.lower() == "false"
			or action.lower() == "0"
		):
			action = False

		settings = data["auto_mod"]
		settings.update({"react_commands": action})

		sql = (
			"""UPDATE guilds SET auto_mod = %s WHERE guild_id = %s AND guild_id = %s"""
		)
		val = (json.dumps(settings), ctx.guild.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

	@setting.command(
		hidden=True,
		name="idea-channel",
		description="**Настройка канала идей сервера**",
		usage="setting idea-channel [Id канала]",
	)
	async def ideachannel(self, ctx, channel: int):
		client = self.client
		ideachannel = get(ctx.guild.text_channels, id=channel)
		if ideachannel in ctx.guild.text_channels:
			sql = """UPDATE guilds SET idea_channel = %s WHERE guild_id = %s AND guild_id = %s"""
			val = (channel, ctx.guild.id, ctx.guild.id)

			self.cursor.execute(sql, val)
			self.conn.commit()

			emb = discord.Embed(
				description=f"**Вы успешно настроили канал идей! Новий канал - {ideachannel.name}**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Такого канала не существует введите id правильно**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

	@setting.command(
		hidden=True,
		name="time-delete-channel",
		description="**Через сколько минут будет удалять приватный текстовый канал**",
		usage="setting time-delete-channel [Любое число]",
	)
	async def timetextchannel(self, ctx, time: int):
		client = self.client
		sql = """UPDATE guilds SET timedelete_textchannel = %s WHERE guild_id = %s AND guild_id = %s"""
		val = (time, ctx.guild.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		emb = discord.Embed(
			description=f"**Вы успешно изменили значения! Новая длительность на удаления приватного текстового - {time}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
		emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
		await ctx.send(embed=emb)

	@setting.command(
		hidden=True,
		name="exp-multi",
		aliases=["exp-multiplier"],
		description="**Настройка множителя опыта на сервере**",
		usage="setting exp-multi [Множитель%(Пример - 450%)]",
	)
	async def expform(self, ctx, multiplier: str):
		client = self.client
		multi = int(multiplier[:-1])
		if multi > 10000 or multi <= 0:
			emb = discord.Embed(
				title="Ошибка!",
				description="Укажите множитель опыта в диапазоне от 1% до 10000%",
				colour=discord.Color.green(),
			)
			emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		form = float(multi / 100)
		sql = (
			"""UPDATE guilds SET exp_multi = %s WHERE guild_id = %s AND guild_id = %s"""
		)
		val = (form, ctx.guild.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		emb = discord.Embed(
			description=f"**Вы успешно настроили множитель опыта, {multiplier}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
		emb.set_footer(text=Footer, icon_url=client.user.avatar_url)
		await ctx.send(embed=emb)

	@setting.command(
		hidden=True,
		name="log-channel",
		aliases=["set-log", "set-log-channel", "log_channel", "logchannel"],
		description="**Настройка канала аудита**",
		usage="setting log-channel [Id канала]",
	)
	async def set_log_channel(self, ctx, channel_id: int):
		if channel_id not in [channel.id for channel in ctx.guild.channels]:
			return

		if isinstance(ctx.guild.get_channel(channel_id), discord.VoiceChannel):
			return

		sql = """UPDATE guilds SET log_channel = %s WHERE guild_id = %s"""
		val = (channel_id, ctx.guild.id)
		self.cursor.execute(sql, val)
		self.conn.commit()


def setup(client):
	client.add_cog(Settings(client))
