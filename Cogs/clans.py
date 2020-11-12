import discord
import os
import uuid
import json
import mysql.connector
import random
from datetime import datetime
from string import ascii_uppercase
from configs import configs
from Tools.database import DB
from discord.ext import commands


class Clans(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.FOOTER = configs["FOOTER_TEXT"]
		self.conn = mysql.connector.connect(
			user="root",
			password=os.environ["DB_PASSWORD"],
			host="localhost",
			database="data",
		)
		self.cursor = self.conn.cursor(buffered=True)

	async def _add_member(self, ctx, clan_id: str, member: discord.Member):
		data = DB().sel_guild(guild=ctx.guild)["clans"]
		for clan in data:
			if clan["id"] == clan_id:
				if member.id not in clan["members"]:
					clan_id = clan["id"]
					clan["members"].append(member.id)

		self.cursor.execute(
			("""UPDATE users SET clan = %s WHERE user_id = %s AND guild_id = %s"""),
			(clan_id, member.id, ctx.guild.id),
		)
		self.cursor.execute(
			("""UPDATE guilds SET clans = %s WHERE guild_id = %s AND guild_id = %s"""),
			(json.dumps(data), ctx.guild.id, ctx.guild.id),
		)
		self.conn.commit()
		await ctx.message.add_reaction("✅")

	@commands.group(
		help=f"""**Команды групы:** buy, members, accept-join-request, send-join-request, kick, reject-join-request, list-join-requests, list, use-invite, info, create, edit, leave, create-invite, trans-owner-ship, delete\n\n"""
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def clan(self, ctx):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

	@clan.command(usage="clan create [Названия]", description="**Создаёт клан**")
	async def create(self, ctx, *, name: str):
		data = DB().sel_guild(guild=ctx.guild)["clans"]
		user_data = DB().sel_user(target=ctx.author)
		logs_channel_id = DB().sel_guild(guild=ctx.guild)["log_channel"]

		for clan in data:
			if ctx.author.id in clan["members"]:
				emb = discord.Embed(
					title="Ошибка!",
					description="**Вы уже находитесь в одном из кланов сервера!**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction("❌")
				return

		if user_data["coins"] < 15000:
			emb = discord.Embed(
				title="Ошибка!",
				description="**У вас не достаточно коинов**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		if len(data) > 20:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Превышен лимит кланов на сервере!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		role = await ctx.guild.create_role(name="PT-[CLAN]-" + name)
		await ctx.author.add_roles(role)
		coins = user_data["coins"] - 15000
		new_id = str(uuid.uuid4())
		data.append(
			{
				"id": new_id,
				"name": name,
				"role_id": role.id,
				"members": [ctx.author.id],
				"owner": ctx.author.id,
				"description": "Не указано",
				"short_desc": "Не указано",
				"size": 10,
				"type": "public",
				"invites": [],
				"join_requests": [],
			}
		)

		emb = discord.Embed(
			title=f"Успешно созданн новый клан",
			description=f"**Id -** `{new_id}`\n**Названия -** `{name}`",
			colour=discord.Color.green(),
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		sql = """UPDATE guilds SET clans = %s WHERE guild_id = %s AND guild_id = %s"""
		val = (json.dumps(data), ctx.guild.id, ctx.guild.id)
		self.cursor.execute(sql, val)
		sql = """UPDATE users SET coins = %s, clan = %s WHERE guild_id = %s AND user_id = %s"""
		val = (coins, new_id, ctx.guild.id, ctx.author.id)
		self.cursor.execute(sql, val)
		self.conn.commit()

		if logs_channel_id != 0:
			e = discord.Embed(
				description=f"Создан новый клан",
				colour=discord.Color.green(),
				timestamp=datetime.utcnow(),
			)
			e.add_field(name="Id клана", value=f"`{new_id}`", inline=False)
			e.set_author(name="Журнал аудита | Создания клана сервера", icon_url=ctx.author.avatar_url)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.guild.get_channel(logs_channel_id).send(embed=e)

	@clan.command(
		usage="clan edit [Параметр] [Новое значения]",
		description="**Изменяет настройки клана**",
	)
	async def edit(self, ctx, field: str, *, value):
		data = DB().sel_guild(guild=ctx.guild)["clans"]
		user_clan = DB().sel_user(target=ctx.author)["clan"]
		field = field.lower()

		if user_clan == "":
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вас нету ни в одном клане сервера!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		for clan in data:
			if clan["id"] == user_clan:
				if clan["owner"] == ctx.author.id:
					fields = ["name", "description", "short_desc", "type"]
					if field in fields:
						emb = discord.Embed(
							description=f"""**Был установлен новое значения - `{value}` для параметра - `{field}`**""",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("✅")

						clan[field] = value
						self.cursor.execute(
							("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""),
							(json.dumps(data), ctx.guild.id),
						)
						self.conn.commit()
					else:
						emb = discord.Embed(
							title="Ошибка!",
							description=f"""**Укажите изменяемый параметр из этих: {', '.join(fields)}!**""",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("❌")
						return
				else:
					emb = discord.Embed(
						title="Ошибка!",
						description="**Вы не владелец указаного клана!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction("❌")
					return

	@clan.command(
		name="trans-owner-ship",
		usage="clan trans-owner-ship [@Участник]",
		description="**Передаёт права владения клана указаному участнику**",
	)
	async def trans_own_ship(self, ctx, member: discord.Member):
		data = DB().sel_guild(guild=ctx.guild)["clans"]
		user_clan = DB().sel_user(target=ctx.author)["clan"]

		if user_clan == "":
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вас нету ни в одном клане сервера!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		if member == ctx.author:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вы не можете передать права на владения клана себе!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		for clan in data:
			if clan["id"] == user_clan:
				if clan["owner"] == ctx.author.id:
					emb = discord.Embed(
						description=f"**Права на владения клана успешно переданы другому участнику - `{str(member)}`!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)

					clan["owner"] = member.id
					self.cursor.execute(
						("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""),
						(json.dumps(data), ctx.guild.id),
					)
					self.conn.commit()
				else:
					emb = discord.Embed(
						title="Ошибка!",
						description="**Вы не владелец указаного клана!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction("❌")
					return

	@clan.command(usage="clan delete", description="**Удаляет клан**")
	async def delete(self, ctx):
		data = DB().sel_guild(guild=ctx.guild)["clans"]
		user_clan = DB().sel_user(target=ctx.author)["clan"]
		logs_channel_id = DB().sel_guild(guild=ctx.guild)["log_channel"]

		if user_clan == "":
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вас нету ни в одном клане сервера!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		for clan in data:
			if clan["id"] == user_clan:
				if clan["owner"] == ctx.author.id:
					delete_clan = clan
					if "category_id" in clan.keys():
						category = ctx.guild.get_channel(clan["category_id"])
						if category:
							for channel in category.channels:
								await channel.delete()
							await category.delete()
					try:
						data.remove(clan)
						for member_id in clan["members"]:
							try:
								await ctx.guild.get_member(member_id).remove_roles(
									ctx.guild.get_role(clan["role_id"])
								)
								await ctx.guild.get_role(clan["role_id"]).delete()
							except AttributeError:
								pass
					except ValueError:
						emb = discord.Embed(
							title="Ошибка!",
							description="**Клана с таким id не существует!**",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("❌")
						return
				else:
					emb = discord.Embed(
						title="Ошибка!",
						description="**Вы не владелец указаного клана!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction("❌")
					return

		sql = """UPDATE guilds SET clans = %s WHERE guild_id = %s AND guild_id = %s"""
		val = (json.dumps(data), ctx.guild.id, ctx.guild.id)
		self.cursor.execute(sql, val)
		for member_id in delete_clan["members"]:
			sql = """UPDATE users SET clan = %s WHERE guild_id = %s AND user_id = %s"""
			val = ("", ctx.guild.id, member_id)
			self.cursor.execute(sql, val)
		self.conn.commit()
		await ctx.message.add_reaction("✅")

		if logs_channel_id != 0:
			e = discord.Embed(
				description=f"Удален клан",
				colour=discord.Color.green(),
				timestamp=datetime.utcnow(),
			)
			e.add_field(name="Id клана", value=f"""`{delete_clan["id"]}`""", inline=False)
			e.set_author(name="Журнал аудита | Удаления клана сервера", icon_url=ctx.author.avatar_url)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.guild.get_channel(logs_channel_id).send(embed=e)

	@clan.command(
		usage="clan members", description="**Показывает всех участников клана**"
	)
	async def members(self, ctx, clan_id: str = None):
		data = DB().sel_guild(guild=ctx.guild)["clans"]
		state = False
		if not clan_id:
			if DB().sel_user(target=ctx.author)["clan"] != "":
				clan_id = DB().sel_user(target=ctx.author)["clan"]
			else:
				emb = discord.Embed(
					title="Ошибка!",
					description="**Вы не указали аргумент. Укажити аргумент - clan_id к указаной команде!**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction("❌")

		for clan in data:
			if clan["id"] == clan_id:
				if clan["type"] == "public":
					state = True
					members = "\n".join(
						f"**Участник -** `{str(ctx.guild.get_member(member_id))}`"
						if member_id != clan["owner"]
						else f"**Владелец -** `{str(ctx.guild.get_member(member_id))}`"
						for member_id in clan["members"]
					)
					emb = discord.Embed(
						title=f"""Список участников клана - {clan['name']}""",
						description=members,
						colour=discord.Color.green(),
					)
					break

		if state:
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Клана с таким id не существует!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")

	@clan.command(
		usage="clan kick [@Участник]",
		description="**Кикает указаного участника с клана**",
	)
	async def kick(self, ctx, member: discord.Member):
		data = DB().sel_guild(guild=ctx.guild)["clans"]
		user_clan = DB().sel_user(target=ctx.author)["clan"]
		if user_clan == "":
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вас нету ни в одном клане сервера!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		if member == ctx.author:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вы не можете кикнуть самого себя!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		for clan in data:
			if clan["id"] == user_clan:
				if clan["owner"] == ctx.author.id:
					if member.id in clan["members"]:
						clan["members"].remove(member.id)
						try:
							await member.remove_roles(
								ctx.guild.get_role(clan["role_id"])
							)
						except:
							pass
						self.cursor.execute(
							(
								"""UPDATE users SET clan = %s WHERE user_id = %s AND guild_id = %s"""
							),
							("", member.id, ctx.guild.id),
						)
						self.cursor.execute(
							("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""),
							(json.dumps(data), ctx.guild.id),
						)
						self.conn.commit()
						await ctx.message.add_reaction("✅")
						return
					else:
						emb = discord.Embed(
							title="Ошибка!",
							description="**В клане нету указаного участника!**",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("❌")
						return
				else:
					emb = discord.Embed(
						title="Ошибка!",
						description="**Вы не владелец указаного клана!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction("❌")
					return

	@clan.command(
		name="list",
		usage="clan list-clans",
		description="**Показывает все кланы сервера**",
	)
	async def list_clans(self, ctx):
		data = [
			clan
			for clan in DB().sel_guild(guild=ctx.guild)["clans"]
			if clan["type"] == "public"
		]
		if data != []:
			emb = discord.Embed(
				title="Список кланов сервера",
				description=f"**Общее количество кланов на сервере:** `{len(data)}`",
				colour=discord.Color.green(),
			)
			for clan in data:
				emb.add_field(
					name=clan["name"],
					value=f"""**Id -** `{clan['id']}`\n**Краткое описания -** `{clan['short_desc']}`\n**Максимальное количество участников -** `{clan['size']}`\n**Владелец -** `{str(ctx.guild.get_member(clan['owner']))}`""",
				)
		else:
			emb = discord.Embed(
				title="Список кланов сервера",
				description=f"**На сервере нету кланов**",
				colour=discord.Color.green(),
			)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@clan.command(
		usage="clan info |Id|", description="**Показывает полную информацию о клане**"
	)
	async def info(self, ctx, clan_id: str = None):
		data = DB().sel_guild(guild=ctx.guild)["clans"]
		user_clan = DB().sel_user(target=ctx.author)["clan"]
		state = False
		if not clan_id:
			if user_clan != "":
				clan_id = user_clan
			else:
				emb = discord.Embed(
					title="Ошибка!",
					description="**Вы не указали аргумент. Укажити аргумент - clan_id к указаной команде!**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction("❌")
				return

		for clan in data:
			if clan["id"] == clan_id:
				if clan["type"] == "public":
					state = True
					emb = discord.Embed(
						title=f"""Информация о клане - {clan['name']}""",
						description=f"""**Id -** `{clan['id']}`\n**Описания -** `{clan['description']}`\n**Владелец -** `{ctx.guild.get_member(clan['owner'])}`\n**Роль клана -** `{ctx.guild.get_role(clan['role_id']).name}`\n**Максимальное количество участников -** `{clan['size']}`\n**Участников -** `{len(clan['members'])}`""",
						colour=discord.Color.green(),
					)
					break
				else:
					if clan["id"] == user_clan:
						state = True
						emb = discord.Embed(
							title=f"""Информация о клане - {clan['name']}""",
							description=f"""**Id -** `{clan['id']}`\n**Описания -** `{clan['description']}`\n**Владелец -** `{ctx.guild.get_member(clan['owner'])}`\n**Роль клана -** `{ctx.guild.get_role(clan['role_id']).name}`\n**Максимальное количество участников -** `{clan['size']}`\n**Участников -** `{len(clan['members'])}`""",
							colour=discord.Color.green(),
						)
						break

		if state:
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Клана с таким id не существует!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")

	@clan.command(
		usage="clan leave", description="**С помощью команды вы покидаете ваш клан**"
	)
	async def leave(self, ctx):
		data = DB().sel_guild(guild=ctx.guild)["clans"]
		user_clan = DB().sel_user(target=ctx.author)["clan"]
		if user_clan == "":
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вас нету ни в одном клане сервера!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		for clan in data:
			if clan["id"] == user_clan:
				if clan["owner"] != ctx.author.id:
					try:
						await ctx.author.remove_roles(
							ctx.guild.get_role(clan["role_id"])
						)
					except:
						pass
					clan["members"].remove(ctx.author.id)
					self.cursor.execute(
						(
							"""UPDATE users SET clan = %s WHERE user_id = %s AND guild_id = %s"""
						),
						("", ctx.author.id, ctx.guild.id),
					)
					self.cursor.execute(
						("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""),
						(json.dumps(data), ctx.guild.id),
					)
					self.conn.commit()
					await ctx.message.add_reaction("✅")
					break
				else:
					emb = discord.Embed(
						title="Ошибка!",
						description="**Вы не можете покинуть свой клан!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction("❌")
					return

	@clan.command(
		name="create-invite",
		usage="clan create-invite",
		description="**Создаёт новое приглашения**",
	)
	async def create_invite(self, ctx):
		user_clan = DB().sel_user(target=ctx.author)["clan"]
		data = DB().sel_guild(guild=ctx.guild)["clans"]

		if user_clan == "":
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вас нету ни в одном клане сервера!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		for clan in data:
			if clan["id"] == user_clan:
				if clan["type"] == "public":
					if len(clan["members"]) < clan["size"]:
						new_invite = "".join(
							random.choice(ascii_uppercase) for i in range(12)
						)

						emb = discord.Embed(
							description=f"""**Для клана - `{clan['name']}` было созданно новое приглашения - `{new_invite}`**""",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)

						clan["invites"].append(new_invite)
						self.cursor.execute(
							("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""),
							(json.dumps(data), ctx.guild.id),
						)
						self.conn.commit()
					else:
						emb = discord.Embed(
							title="Ошибка!",
							description="**Указаный клан переполнен!**",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("❌")
						return
				else:
					if clan["owner"] == ctx.author.id:
						if len(clan["members"]) < clan["size"]:
							pass
						else:
							emb = discord.Embed(
								title="Ошибка!",
								description="**Указаный клан переполнен!**",
								colour=discord.Color.green(),
							)
							emb.set_author(
								name=ctx.author.name, icon_url=ctx.author.avatar_url
							)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await ctx.send(embed=emb)
							await ctx.message.add_reaction("❌")
							return
					else:
						emb = discord.Embed(
							title="Ошибка!",
							description="**Указаный клан приватный!**",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("❌")
						return

	@clan.command(
		name="use-invite",
		usage="clan use-invite [Код приглашения]",
		description="**С помощью команды вы используете указаное приглашения**",
	)
	async def use_invite(self, ctx, invite: str):
		data = DB().sel_guild(guild=ctx.guild)["clans"]
		state = False

		if DB().sel_user(target=ctx.author)["clan"] != "":
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вы уже находитесь в одном из кланов сервера!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		for clan in data:
			if invite in clan["invites"]:
				state = True
				if ctx.author.id not in clan["members"]:
					clan["invites"].remove(invite)
					clan["members"].append(ctx.author.id)
					await self._add_member(ctx, clan["id"], ctx.author)
					self.cursor.execute(
						("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""),
						(json.dumps(data), ctx.guild.id),
					)
					self.conn.commit()
					break
				else:
					emb = discord.Embed(
						title="Ошибка!",
						description="**Вы уже находитесь в этом клане!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction("❌")
					return

		if not state:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Такого приглашения не существует!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")

	@clan.command(
		name="send-join-request",
		description="**Отправляет запрос на присоиденения к клану**",
	)
	async def send_join_request(self, ctx, clan_id: str):
		data = DB().sel_guild(guild=ctx.guild)["clans"]
		state = False

		if DB().sel_user(target=ctx.author)["clan"] != "":
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вы уже находитесь в одном из кланов сервера!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		for clan in data:
			if clan["id"] == clan_id:
				state = True
				if len(clan["members"]) < clan["size"]:
					if ctx.author.id not in clan["join_requests"]:
						emb = discord.Embed(
							description=f"""**Запрос на присоединения был успешно отправлен**""",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)

						clan["join_requests"].append(ctx.author.id)
						self.cursor.execute(
							("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""),
							(json.dumps(data), ctx.guild.id),
						)
						self.conn.commit()
					else:
						emb = discord.Embed(
							title="Ошибка!",
							description="**Вы уже отправили запрос этому клану!**",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("❌")
						return
				else:
					emb = discord.Embed(
						title="Ошибка!",
						description="**Указаный клан переполнен!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction("❌")
					return

		if not state:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Клана с таким id не существует!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")

	@clan.command(
		name="list-join-requests",
		description="Показывает список всех кланов на сервере",
	)
	async def list_join_requests(self, ctx):
		user_clan = DB().sel_user(target=ctx.author)["clan"]
		data = DB().sel_guild(guild=ctx.guild)["clans"]

		if user_clan == "":
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вас нету ни в одном клане сервера!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		for clan in data:
			if clan["id"] == user_clan:
				if clan["owner"] == ctx.author.id:
					join_requests = "\n".join(
						[
							str(ctx.guild.get_member(member_id))
							for member_id in clan["join_requests"]
						]
					)
					emb = discord.Embed(
						description=f"**Запросы на приглашения к вашему клану:**\n{join_requests}",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					return
				else:
					emb = discord.Embed(
						title="Ошибка!",
						description="**Вы не владелец указаного клана!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction("❌")
					return

	@clan.command(
		name="accept-join-request",
		description="**Принимает указаный запрос на присоиденения к клану**",
	)
	async def accept_join_request(self, ctx, member: discord.Member):
		user_clan = DB().sel_user(target=ctx.author)["clan"]
		data = DB().sel_guild(guild=ctx.guild)["clans"]

		if user_clan == "":
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вас нету ни в одном клане сервера!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		for clan in data:
			if clan["id"] == user_clan:
				if clan["owner"] == ctx.author.id:
					if member.id in clan["join_requests"]:
						emb = discord.Embed(
							description=f"""**Запрос на присоиденения к клану - `{clan['name']}` был принят!**""",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						try:
							await member.send(embed=emb)
						except:
							pass
						await ctx.message.add_reaction("✅")
						await self._add_member(ctx, clan["id"], member)
						clan["join_requests"].remove(member.id)
						self.cursor.execute(
							("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""),
							(json.dumps(data), ctx.guild.id),
						)
						self.conn.commit()
					else:
						emb = discord.Embed(
							title="Ошибка!",
							description="**Указаный участник не отправлял запрос на присоиденения к клану!**",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("❌")
						return
				else:
					emb = discord.Embed(
						title="Ошибка!",
						description="**Вы не владелец указаного клана!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction("❌")
					return

	@clan.command(
		name="reject-join-request",
		description="**Отклоняет указаный запрос на присоиденения к клану**",
	)
	async def reject_join_request(self, ctx, member: discord.Member):
		user_clan = DB().sel_user(target=ctx.author)["clan"]
		data = DB().sel_guild(guild=ctx.guild)["clans"]

		if user_clan == "":
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вас нету ни в одном клане сервера!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		for clan in data:
			if clan["id"] == user_clan:
				if clan["owner"] == ctx.author.id:
					if member.id in clan["join_requests"]:
						emb = discord.Embed(
							description=f"""**Запрос на присоиденения к клану - `{clan['name']}` был отклонен!**""",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						try:
							await member.send(embed=emb)
						except:
							pass
						await ctx.message.add_reaction("✅")

						clan["join_requests"].remove(member.id)
						self.cursor.execute(
							("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""),
							(json.dumps(data), ctx.guild.id),
						)
						self.conn.commit()
					else:
						emb = discord.Embed(
							title="Ошибка!",
							description="**Указаный участник не отправлял запрос на присоиденения к клану!**",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("❌")
						return
				else:
					emb = discord.Embed(
						title="Ошибка!",
						description="**Вы не владелец указаного клана!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction("❌")
					return

	@clan.command(description="**Покупает указаный предмет для клана**")
	async def buy(self, ctx, item: str, color: str = None):
		user_data = DB().sel_user(target=ctx.author)
		data = DB().sel_guild(guild=ctx.guild)["clans"]
		item = item.lower()

		if user_data["clan"] == "":
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вас нету ни в одном клане сервера!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		for clan in data:
			if clan["id"] == user_data["clan"]:
				if item == "category" or item == "категория":
					if "category_id" not in clan.keys():
						if user_data["coins"] >= 10000:
							overwrites = {
								ctx.guild.get_member(
									member_id
								): discord.PermissionOverwrite(
									send_messages=True, read_messages=True
								)
								for member_id in clan["members"]
							}
							overwrites.update(
								{
									ctx.guild.default_role: discord.PermissionOverwrite(
										send_messages=False, read_messages=False
									),
									self.client.user: discord.PermissionOverwrite(
										send_messages=True, read_messages=True
									),
								}
							)
							category = await ctx.guild.create_category(
								name="PT-[CLAN]-" + clan["name"], overwrites=overwrites
							)
							clan.update({"category_id": category.id})
							user_data["coins"] -= 10000

							emb = discord.Embed(
								description=f"""**Вы успешно купили категорию - `{category.name}`!**""",
								colour=discord.Color.green(),
							)
							emb.set_author(
								name=ctx.author.name, icon_url=ctx.author.avatar_url
							)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await ctx.send(embed=emb)

							self.cursor.execute(
								(
									"""UPDATE guilds SET clans = %s WHERE guild_id = %s"""
								),
								(json.dumps(data), ctx.guild.id),
							)
							self.cursor.execute(
								(
									"""UPDATE users SET coins = %s WHERE user_id = %s AND guild_id = %s"""
								),
								(user_data["coins"], ctx.author.id, ctx.guild.id),
							)
							self.conn.commit()
						else:
							emb = discord.Embed(
								title="Ошибка!",
								description="**У вас не достаточно коинов!**",
								colour=discord.Color.green(),
							)
							emb.set_author(
								name=ctx.author.name, icon_url=ctx.author.avatar_url
							)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await ctx.send(embed=emb)
							await ctx.message.add_reaction("❌")
							return
					else:
						emb = discord.Embed(
							title="Ошибка!",
							description="**Клан уже имеет категорию!**",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("❌")
						return
				elif item == "size" or item == "размер":
					if user_data["coins"] >= 7500:
						if clan["size"] >= 25:
							emb = discord.Embed(
								title="Ошибка!",
								description="**Клан достиг максимального размера!**",
								colour=discord.Color.green(),
							)
							emb.set_author(
								name=ctx.author.name, icon_url=ctx.author.avatar_url
							)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await ctx.send(embed=emb)
							await ctx.message.add_reaction("❌")
							return

						emb = discord.Embed(
							description="**Вы успешно расширили клан на 5 слотов!**",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)

						clan["size"] += 5
						user_data["coins"] -= 7500
						self.cursor.execute(
							("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""),
							(json.dumps(data), ctx.guild.id),
						)
						self.cursor.execute(
							(
								"""UPDATE users SET coins = %s WHERE user_id = %s AND guild_id = %s"""
							),
							(user_data["coins"], ctx.author.id, ctx.guild.id),
						)
						self.conn.commit()
					else:
						emb = discord.Embed(
							title="Ошибка!",
							description="**У вас не достаточно коинов!**",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("❌")
						return
				elif item == "color" or item == "colour" or item == "цвет":
					colors = {
						"teal": 0x1ABC9C,
						"dark_teal": 0x11806A,
						"green": 0x2ECC71,
						"dark_green": 0x1F8B4C,
						"blue": 0x3498DB,
						"dark_blue": 0x206694,
						"purple": 0x9B59B6,
						"dark_purple": 0x71368A,
						"magenta": 0xE91E63,
						"dark_magenta": 0xAD1457,
						"gold": 0xF1C40F,
						"dark_gold": 0xC27C0E,
						"orange": 0xE67E22,
						"dark_orange": 0xA84300,
						"red": 0xE74C3C,
						"dark_red": 0x992D22,
						"lighter_gray": 0x95A5A6,
						"dark_gray": 0x607D8B,
						"light_gray": 0x979C9F,
						"darker_gray": 0x546E7A,
						"blurple": 0x7289DA,
						"greyple": 0x99AAB5,
					}
					if color not in colors.keys():
						emb = discord.Embed(
							title="Ошибка!",
							description=f"""**Указан не правильный цвет, укажите из этих: {', '.join(colors.keys())}!**""",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("❌")
						return

					if user_data["coins"] >= 5000:
						try:
							await ctx.guild.get_role(clan["role_id"]).edit(
								colour=colors[color.lower()]
							)
							emb = discord.Embed(
								description="**Вы успешно купили новый цвет для роли вашего клана!**",
								colour=discord.Color.green(),
							)
							emb.set_author(
								name=ctx.author.name, icon_url=ctx.author.avatar_url
							)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await ctx.send(embed=emb)

							user_data["coins"] -= 5000
							self.cursor.execute(
								(
									"""UPDATE users SET coins = %s WHERE user_id = %s AND guild_id = %s"""
								),
								(user_data["coins"], ctx.author.id, ctx.guild.id),
							)
							self.conn.commit()
						except:
							emb = discord.Embed(
								title="Ошибка!",
								description="**Была удалена роль клана!**",
								colour=discord.Color.green(),
							)
							emb.set_author(
								name=ctx.author.name, icon_url=ctx.author.avatar_url
							)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await ctx.send(embed=emb)
							await ctx.message.add_reaction("❌")
							return
					else:
						emb = discord.Embed(
							title="Ошибка!",
							description="**У вас не достаточно коинов!**",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction("❌")
						return
				else:
					emb = discord.Embed(
						title="Ошибка!",
						description="**Вы указали не правильный предмет!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction("❌")
					return


def setup(client):
	client.add_cog(Clans(client))
