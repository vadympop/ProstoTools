import discord
import json
import asyncio
import time
import os
import mysql.connector

from tools import DB

from discord.ext import commands
from discord.utils import get
from random import randint
from configs import configs


def check_role(ctx):
	data = DB().sel_guild(guild=ctx.guild)["moder_roles"]
	roles = ctx.guild.roles[::-1]
	data.append(roles[0].id)

	if data != []:
		for role in data:
			role = get(ctx.guild.roles, id=role)
			yield role in ctx.author.roles
	else:
		return roles[0] in ctx.author.roles


class Utils(commands.Cog, name="Utils"):
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

	@commands.command(
		brief="True",
		description="**Устанавливает анти-рейд режим. Есть не сколько режимов, 1 - Слабый 5сек задержка в текстовых каналах и средний уровень модерации, 2 - Сильний 10сек задержка в текстовых каналах и високий уровень модерации, 3 - Найвисшый 15сек задержка в текстовых каналах и найвисшый уровень модерации**",
		usage="anti-rade [Время действия] [Уровень защиты]",
		help="**Примеры использования:**\n1. {Prefix}anti-rade 10 2\n\n**Пример 1:** Ставит анти-рейд режим второго уровня на 10 минут",
	)
	@commands.check(check_role)
	async def antirade(self, ctx, time: int, mode: int):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		first_verfLevel = ctx.guild.verification_level

		if mode == 1:
			emb = discord.Embed(
				title=f"**Уставлен анти-рейд режим 1-го уровня на {time}мин**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			await ctx.guild.edit(verification_level=discord.VerificationLevel.medium)
			for i in ctx.guild.text_channels:
				await i.edit(slowmode_delay=5)

			await asyncio.sleep(time * 60)
			await ctx.guild.edit(verification_level=first_verfLevel)

			for k in ctx.guild.text_channels:
				await k.edit(slowmode_delay=0)
		elif mode == 2:
			emb = discord.Embed(
				title=f"**Уставлен анти-рейд режим 2-го уровня на {time}мин**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			await ctx.guild.edit(verification_level=discord.VerificationLevel.high)
			for i in ctx.guild.text_channels:
				await i.edit(slowmode_delay=10)

			await asyncio.sleep(time * 60)
			await ctx.guild.edit(verification_level=first_verfLevel)

			for k in ctx.guild.text_channels:
				await k.edit(slowmode_delay=0)
		elif mode == 3:
			emb = discord.Embed(
				title=f"**Уставлен анти-рейд режим 3-го уровня на {time}мин**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			await ctx.guild.edit(verification_level=discord.VerificationLevel.extreme)
			for i in ctx.guild.text_channels:
				await i.edit(slowmode_delay=15)

			await asyncio.sleep(time * 60)
			await ctx.guild.edit(verification_level=first_verfLevel)

			for k in ctx.guild.text_channels:
				await k.edit(slowmode_delay=0)

	@commands.command(
		aliases=["banlist"],
		brief="True",
		name="ban-list",
		description="**Показывает заблокированных пользователей**",
		usage="ban-list",
		help="**Примеры использования:**\n1. {Prefix}ban-list\n\n**Пример 1:** Показывает все баны сервера",
	)
	@commands.check(check_role)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def bannedusers(self, ctx):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		banned_users = await ctx.guild.bans()

		if banned_users == []:
			emb = discord.Embed(
				title="На этом сервере нету заблокированых участников",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		else:
			emb = discord.Embed(
				title="Список заблокированных участников", colour=discord.Color.green()
			)
			for user in banned_users:
				emb.add_field(
					name=f"Участник: {user.user}",
					value=f"**Причина бана: {user.reason}**"
					if user.reason
					else "**Причина бана: Причина не указана**",
				)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

	@commands.command(
		aliases=["voicerooms"],
		name="voice-rooms",
		hidden=True,
		description="**Создает голосовой канал для создания приватных голосовых комнат**",
		usage="voice-rooms [Вкл/Выкл]",
		help="**Примеры использования:**\n1. {Prefix}voice-rooms вкл\n2. {Prefix}voice-rooms выкл\n\n**Пример 1:** Включает приватные голосовые комнаты на сервере\n**Пример 2:** Выключает приватные голосовые комнаты на сервере",
	)
	@commands.check(lambda ctx: ctx.author == ctx.guild.owner)
	@commands.cooldown(1, 60, commands.BucketType.member)
	async def voicechannel(self, ctx, state: str):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		channel_category = await ctx.guild.create_category("Голосовые комнаты")
		await asyncio.sleep(1)

		on_answers = ["on", "вкл", "включить", "true"]
		off_answers = ["off", "выкл", "выключить", "false"]

		if state.lower() in on_answers:
			data = DB().sel_guild(guild=ctx.guild)["voice_channel"]

			if "channel_id" not in data:
				voice_channel = await ctx.guild.create_voice_channel(
					"Нажми на меня", category=channel_category
				)
				await ctx.message.add_reaction("✅")
				data.update({"channel_id": voice_channel.id})

				sql = """UPDATE guilds SET voice_channel = %s WHERE guild_id = %s AND guild_id = %s"""
				val = (json.dumps(data), ctx.guild.id, ctx.guild.id)

				self.cursor.execute(sql, val)
				self.conn.commit()
			else:
				emb = discord.Embed(
					desciption="**На этом сервере приватные голосовые комнаты уже включены**",
					color=discord.Color.green(),
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction("❌")
				return

		elif state in off_answers:
			await ctx.message.add_reaction("✅")

			sql = """UPDATE guilds SET voice_channel = %s WHERE guild_id = %s AND guild_id = %s"""
			val = (json.dumps({}), ctx.guild.id, ctx.guild.id)

			self.cursor.execute(sql, val)
			self.conn.commit()
		else:
			emb = discord.Embed(
				title="Ошибка!",
				desciption="**Вы не правильно указали действие! Укажите on - что бы включить, off - что бы выключить**",
				color=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

	@commands.command(
		aliases=["serverstats"],
		name="server-stats",
		hidden=True,
		description="**Создает статистику сервера**",
		usage="server-stats [Счетчик]",
		help="**Примеры использования:**\n1. {Prefix}server-stats all\n2. {Prefix}server-stats сообщения\n\n**Пример 1:** Создаёт счетчик всех пользователей сервера\n**Пример 2:** Создаёт сообщения в текущем канале с основной информацией о сервере",
	)
	@commands.check(lambda ctx: ctx.author == ctx.guild.owner)
	@commands.cooldown(1, 60, commands.BucketType.member)
	async def serverstats(self, ctx, stats_count: str):
		data = DB().sel_guild(guild=ctx.guild)["server_stats"]
		members_count = len(
			[
				member.id
				for member in ctx.guild.members
				if not member.bot and member.id != self.client.user.id
			]
		)
		bots_count = len([bot.id for bot in ctx.guild.members if bot.bot])
		channels_count = len([channel.id for channel in ctx.guild.channels])
		roles_count = len([role.id for role in ctx.guild.roles])
		counters = {
			"all": ["Пользователей", ctx.guild.member_count],
			"bots": ["Ботов", bots_count],
			"roles": ["Ролей", roles_count],
			"channels": ["Каналов", channels_count],
			"members": ["Участников", members_count],
		}

		if stats_count.lower() in ["message", "сообщения"]:
			await ctx.message.delete()
			val = (ctx.guild.id, ctx.guild.id)
			sql_1 = """SELECT user_id, exp, money, reputation, messages FROM users WHERE guild_id = %s AND guild_id = %s ORDER BY exp DESC LIMIT 20"""
			sql_2 = """SELECT exp FROM users WHERE guild_id = %s AND guild_id = %s"""

			data = DB().query_execute(sql_1, val)
			all_exp = sum([i[0] for i in DB().query_execute(sql_2, val)])
			dnd = len(
				[
					str(member.id)
					for member in ctx.guild.members
					if member.status.name == "dnd"
				]
			)
			sleep = len(
				[
					str(member.id)
					for member in ctx.guild.members
					if member.status.name == "idle"
				]
			)
			online = len(
				[
					str(member.id)
					for member in ctx.guild.members
					if member.status.name == "online"
				]
			)
			offline = len(
				[
					str(member.id)
					for member in ctx.guild.members
					if member.status.name == "offline"
				]
			)
			description = "Статистика обновляеться каждые 5 минут\n\n**20 Самых активных участников сервера**"
			num = 1
			for profile in data:
				member = ctx.guild.get_member(profile[0])
				if member is not None:
					if not member.bot:
						if len(member.name) > 15:
							member = (
								member.name[:15] + "..." + "#" + member.discriminator
							)
						description += f"""\n`{num}. {str(member)} {profile[1]}exp {profile[2]}$ {profile[3]}rep {json.loads(profile[4])[1]}msg`"""
						num += 1

			description += f"""\n\n**Общая инфомация**\n:baby:Пользователей: **{ctx.guild.member_count}**\n:family_man_girl_boy:Участников: **{len([m.id for m in ctx.guild.members if not m.bot])}**\n<:bot:731819847905837066>Ботов: **{len([m.id for m in ctx.guild.members if m.bot])}**\n<:voice_channel:730399079418429561>Голосовых подключений: **{sum([len(v.members) for v in ctx.guild.voice_channels])}**\n<:text_channel:730396561326211103>Каналов: **{len([c.id for c in ctx.guild.channels])}**\n<:role:730396229220958258>Ролей: **{len([r.id for r in ctx.guild.roles])}**\n:star:Всего опыта: **{all_exp}**\n\n**Статусы участников**\n<:online:730393440046809108>`{online}`  <:offline:730392846573633626>`{offline}`\n<:sleep:730390502972850256>`{sleep}`  <:mobile:777854822300385291>`{len([m.id for m in ctx.guild.members if m.is_on_mobile()])}`\n<:dnd:730391353929760870>`{dnd}` <:boost:777854437724127272>`{len(set(ctx.guild.premium_subscribers))}`"""

			emb = discord.Embed(
				title="Статистика сервера",
				description=description,
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			message = await ctx.send(embed=emb)
			await ctx.message.add_reaction("✅")

			data = DB().sel_guild(guild=ctx.guild)["server_stats"]
			data.update({"message": [message.id, ctx.channel.id]})

			sql = """UPDATE guilds SET server_stats = %s WHERE guild_id = %s AND guild_id = %s"""
			val = (json.dumps(data), ctx.guild.id, ctx.guild.id)

			self.cursor.execute(sql, val)
			self.conn.commit()
			return

		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if stats_count.lower() not in counters.keys():
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вы не правильно указали счетчик. Укажите из этих: bots, all, members, roles, channels**",
				color=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		stats_category = await ctx.guild.create_category("Статистика")
		await asyncio.sleep(1)

		overwrite = discord.PermissionOverwrite(connect=False)
		stats_channel = await ctx.guild.create_voice_channel(
			f"[{counters[stats_count.lower()][1]}] {counters[stats_count.lower()][0]}",
			category=stats_category,
		)
		await stats_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

		await stats_category.edit(position=0)
		await ctx.message.add_reaction("✅")

		data = DB().sel_guild(guild=ctx.guild)["server_stats"]
		data.update({stats_count.lower(): stats_channel.id})

		sql = """UPDATE guilds SET server_stats = %s WHERE guild_id = %s AND guild_id = %s"""
		val = (json.dumps(data), ctx.guild.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

	@commands.command(
		aliases=["massrole"],
		name="mass-role",
		hidden=True,
		description="**Удаляет или добавляет роль участникам с указаной ролью**",
		usage="mass-role [add/remove] [@Роль] [@Изменяемая роль]",
		help="**Примеры использования:**\n1. {Prefix}mass-role add @Роль @ИзменяемаяРоль\n2. {Prefix}mass-role add 717776604461531146 717776604461531146\n3. {Prefix}mass-role remove @Роль @ИзменяемаяРоль\n4. {Prefix}mass-role remove 717776604461531146 717776604461531146\n\n**Пример 1:** Добавляет упомянутою роль участникам с упомянутою ролью\n**Пример 2:** Добавляет роль с указаным id участникам с ролью с указаным id\n**Пример 3:** Убирает упомянутою роль в участников с упомянутой ролью\n**Пример 4:** Убирает роль с указаным id в участников с ролью с указаным id",
	)
	@commands.cooldown(1, 1800, commands.BucketType.member)
	@commands.has_permissions(administrator=True)
	async def mass_role(
		self, ctx, type_act: str, for_role: discord.Role, role: discord.Role
	):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if type_act == "add":
			for member in ctx.guild.members:
				if for_role in member.roles:
					if role not in member.roles:
						await member.add_roles(role)

			emb = discord.Embed(
				title="Операция добавления роли проведенна успешно",
				description=f"У пользователей с ролью `{for_role.name}` была добавленна роль - `{role.name}`",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif type_act == "remove" or type_act == "del":
			for member in ctx.guild.members:
				if for_role in member.roles:
					if role in member.roles:
						await member.remove_roles(role)

			emb = discord.Embed(
				title="Операция снятия роли проведенна успешно",
				description=f"У пользователей с ролью `{for_role.name}` была снята роль - `{role.name}`",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"Вы указали не правильное действие! Укажите add - для добавления, del или remove - для удаления",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

	@commands.command(
		brief="True",
		aliases=["list-moders", "moders", "moderators"],
		name="list-moderators",
		description="**Показывает список ролей модераторов**",
		usage="list-moderators",
		help="**Примеры использования:**\n1. {Prefix}list-moderators\n\n**Пример 1:** Показывает список ролей модераторов",
	)
	@commands.check(check_role)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def list_moderators(self, ctx):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		data = DB().sel_guild(guild=ctx.guild)["moder_roles"]
		if data != []:
			roles = "\n".join(f"`{get(ctx.guild.roles, id=i).name}`" for i in data)
		else:
			roles = "Роли модераторов не настроены"

		emb = discord.Embed(
			title="Роли модераторов", description=roles, colour=discord.Color.green()
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		aliases=["mutes-list", "listmutes", "muteslist"],
		name="list-mutes",
		description="Показывает все мьюты на сервере",
		usage="list-mutes",
		help="**Примеры использования:**\n1. {Prefix}list-mutes\n\n**Пример 1:** Показывает все мьюты на сервере",
	)
	@commands.check(check_role)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def mutes(self, ctx):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		data = DB().get_mutes(ctx.guild.id)

		if data != []:
			mutes = "\n\n".join(
				f"**Пользователь:** `{ctx.guild.get_member(mute[1])}`, **Причина:** `{mute[3]}`\n**Автор:** {mute[6]}, **Время мьюта:** `{mute[5]}`\n**Активный до**: `{mute[4]}`"
				for mute in data
			)
		else:
			mutes = "На сервере нету мьютов"

		emb = discord.Embed(
			title="Список всех мьютов на сервере",
			description=mutes,
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		aliases=["apikey", "api_key"],
		name="api-key",
		hidden=True,
		description="**Отправляет ключ API сервера**",
		usage="api-key",
		help="**Примеры использования:**\n1. {Prefix}api-key\n\n**Пример 1:** Отправляет ключ API сервера",
	)
	@commands.check(lambda ctx: ctx.author == ctx.guild.owner)
	@commands.cooldown(1, 60, commands.BucketType.member)
	async def api_key(self, ctx):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		key = DB().sel_guild(guild=ctx.guild)["api_key"]

		await ctx.author.send(
			f"Ключ API сервера - {ctx.guild.name}: `{key}`\n**__Никому его не передавайте. Он даёт доступ к данным сервера__**"
		)
		await ctx.message.add_reaction("✅")


def setup(client):
	client.add_cog(Utils(client))
