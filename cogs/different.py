import time
import datetime
import discord
import sanic
import requests
import psutil as ps
from Cybernator import Paginator
from discord.ext import commands
from discord.utils import get
from random import randint


class Different(commands.Cog, name="Different"):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT
		self.HELP_SERVER = self.client.config.HELP_SERVER

	@commands.command(
		name="reminder",
		aliases=["remin"],
		description="**Работа с напоминаниями**",
		usage="reminder [create/list/delete] |Время| |Текст|",
		help="**Полезное:**\nВремя можно указывать в таких форматах: ЧЧ:ММ.ДД.ММ.ГГГГ - 10:30.12.12.2050, кол-воТип - 10m\n\n**Примеры использования:**\n1. {Prefix}reminder create 1h Example reminder text\n2. {Prefix}reminder list\n3. {Prefix}reminder delete 1\n4. {Prefix}reminder create 10:30.12.12.2050 Example reminder text\n\n**Пример 1:** Напомнит `Example reminder text` через 1 час\n**Пример 2:** Покажет список ваших напоминаний\n**Пример 3:** Удалит напоминания с id - `1`\n**Пример 4:** Напомнит `Example reminder text` в 10:30 12.12.2050\n",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def reminder(
		self, ctx, action: str, type_time: str = None, *, text: str = None
	):
		if action == "create":
			if type_time is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите время напоминая!**",
				)
				await ctx.send(embed=emb)
				return

			if text is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите текст напоминания!**",
				)
				await ctx.send(embed=emb)
				return

			if type_time.split(".")[0] == type_time:
				reminder_time = self.client.utils.time_to_num(type_time)
				if reminder_time[0] <= 0:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите время больше 0!**",
					)
					await ctx.send(embed=emb)
					return

				times = time.time() + reminder_time[0]
			else:
				times = self.client.utils.date_to_time(type_time.split("."), type_time)
				if times == 0:
					emb = await self.client.utils.create_error_embed(
						ctx, "Указан не правильный формат времени! Укажите так: ЧЧ:ММ.ДД.ММ.ГГГГ"
					)
					await ctx.send(embed=emb)
					return

			reminder_id = await self.client.database.set_reminder(
				member=ctx.author, channel=ctx.channel, time=times, text=text
			)
			if reminder_id:
				emb = discord.Embed(
					title=f"Созданно новое напоминая #{reminder_id}",
					description=f"**Текст напоминая:**\n```{text}```\n**Действует до:**\n`{str(datetime.datetime.fromtimestamp(times))}`",
					colour=discord.Color.green(),
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				return
			elif not reminder_id:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Превишен лимит напоминалок(25)!**",
				)
				await ctx.send(embed=emb)
				return
		elif action == "list":
			data = await self.client.database.get_reminder(target=ctx.author)
			if data != []:
				reminders = "\n\n".join(
					f"**Id - {reminder[0]}**\n**Текст:** `{reminder[5]}`, **Действует до:** `{str(datetime.datetime.fromtimestamp(float(reminder[4])))}`"
					for reminder in data
				)
			else:
				reminders = "У вас нету напоминаний"

			emb = discord.Embed(
				title="Список напоминаний",
				description=reminders,
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif action == "delete":
			if type_time is not None:
				if type_time.isdigit():
					state = await self.client.database.del_reminder(ctx.author, int(type_time))
					if state:
						emb = await self.client.utils.create_error_embed(
							ctx, f"**Напоминания #{type_time} было успешно удалено**"
						)
						await ctx.send(embed=emb)
						return
					else:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Напоминания с таким id не существует!**"
						)
						await ctx.send(embed=emb)
						return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Указаное id - строка!**"
					)
					await ctx.send(embed=emb)
					return
			elif type_time is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите id напоминания!**"
				)
				await ctx.send(embed=emb)
				return
		else:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите одно из этих действий: create, list, delete!**",
			)
			await ctx.send(embed=emb)

	@commands.command(
		usage="color [Цвет]",
		description="**Устанавливает роль с указаным цветом**",
		help="**Полезное:**\nЦвет надо указывать в формате HEX - #444444\n\n**Примеры использования:**\n1. {Prefix}color #444444\n2. {Prefix}color remove\n\n**Пример 1:** Установит вам роль с указаным цветом в HEX формате(Поддерживаеться только HEX)\n**Пример 2:** Удалить у вас роль с цветом",
	)
	@commands.cooldown(1, 300, commands.BucketType.member)
	async def color(self, ctx, color: str):
		remove_words = ["del", "delete", "rem", "remove"]
		state = False
		if color.lower() in remove_words:
			for role in ctx.author.roles:
				if role.name.startswith(self.client.config.COLOR_ROLE):
					await role.delete()
					state = True
					break

			if not state:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**У вас нет роли цвета!**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction("❌")
				return

			await ctx.message.add_reaction("✅")
			return

		if color.startswith("#"):
			hex = color[1:]
			if len(hex) == 6:
				if (ctx.author.top_role.position + 1) >= ctx.guild.me.top_role.position:
					emb = discord.Embed(
						title="Ошибка!",
						description=f"**У меня не хватает прав на добавления роли к вам!**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction("❌")
					return

				for r in ctx.author.roles:
					if r.name.startswith(self.client.config.COLOR_ROLE):
						await r.delete()
						break

				name = self.client.config.COLOR_ROLE+hex
				roles = {role.name: role.id for role in ctx.guild.roles}
				if name in roles.keys():
					role = ctx.guild.get_role(roles[name])
				else:
					role = await ctx.guild.create_role(
						name=name,
						color=discord.Colour(int(hex, 16))
					)
					await role.edit(position=ctx.author.top_role.position+1)
				await ctx.author.add_roles(role)
				await ctx.message.add_reaction("✅")
			else:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**Указан не правильный формат цвета!**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction("❌")
				return
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Указан не правильный формат цвета!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

	@commands.command(
		aliases=["usersend"],
		name="user-send",
		description="**Отправляет сообщения указаному участнику(Cooldown - 1 мин после двох попыток)**",
		usage="user-send [@Участник] [Сообщения]",
		help="**Примеры использования:**\n1. `{Prefix}user-send @Участник Hello my friend`\n2. `{Prefix}user-send 660110922865704980 Hello my friend`\n\n**Пример 1:** Отправит упомянутому участнику сообщения `Hello my friend`\n**Пример 2:** Отправит участнику с указаным id сообщения `Hello my friend`",
	)
	@commands.cooldown(2, 60, commands.BucketType.member)
	async def send(self, ctx, member: discord.Member, *, message: str):
		data = await self.client.database.sel_user(target=ctx.author)
		coins_member = data["coins"]
		cur_items = data["items"]

		sql = """UPDATE users SET coins = coins - 50 WHERE user_id = %s AND guild_id = %s"""
		val = (ctx.author.id, ctx.guild.id)

		if cur_items != []:
			if "sim" in cur_items and "tel" in cur_items and coins_member > 50:
				await self.client.database.execute(sql, val)

				emb = discord.Embed(
					title=f"Новое сообщения от {ctx.author.name}",
					description=f"**{message}**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await member.send(embed=emb)
			else:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**У вас нет необходимых предметов или не достаточно коинов!**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction("❌")
				self.send.reset_cooldown(ctx)
				return
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**У вас нет необходимых предметов!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.send.reset_cooldown(ctx)
			return

	@commands.command(
		aliases=["devs"],
		name="feedback",
		description="**Отправляет описания бага в боте разработчикам или идею к боту(Cooldown - 2ч)**",
		usage="feedback [bug/idea] [Описания бага или идея к боту]",
		help="**Примеры использования:**\n1. {Prefix}feedback баг Error\n2. {Prefix}feedback идея Idea\n\n**Пример 1:** Отправит баг `Error`\n**Пример 2: Отправит идею `Idea`**",
	)
	@commands.cooldown(1, 7200, commands.BucketType.member)
	async def devs(self, ctx, typef: str, *, msg: str):
		prch = get(self.client.users, id=660110922865704980)
		mrkl = get(self.client.users, id=404224656598499348)

		if typef == "bug" or typef == "баг":
			emb = discord.Embed(
				title=f"Описания бага от пользователя - {ctx.author.name}, с сервера - {ctx.guild.name}",
				description=f"**Описания бага:\n{msg}**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await prch.send(embed=emb)
			await mrkl.send(embed=emb)
		elif typef == "idea" or typef == "идея":
			emb = discord.Embed(
				title=f"Новая идея от пользователя - {ctx.author.name}, с сервера - {ctx.guild.name}",
				description=f"**Идея:\n{msg}**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await prch.send(embed=emb)
			await mrkl.send(embed=emb)
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не правильно указали флаг!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.devs.reset_cooldown(ctx)
			return

	@commands.command(
		aliases=["userinfo", "user"],
		name="user-info",
		description="**Показывает информацию указаного учасника**",
		usage="user-info |@Участник|",
		help="**Примеры использования:**\n1. {Prefix}user-info @Участник\n2. {Prefix}user-info 660110922865704980\n3. {Prefix}user-info\n\n**Пример 1:** Покажет информацию о упомянутом участнике\n**Пример 2:** Покажет информацию о участнике с указаным id\n**Пример 3:** Покажет информацию о вас",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def userinfo(self, ctx, member: discord.Member = None):
		if member is None:
			member = ctx.author

		if member.bot:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не можете просмотреть информацию о боте!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		data = await self.client.database.sel_user(target=member)
		all_message = data["messages"][1]
		joined_at = datetime.datetime.strftime(member.joined_at, "%d %B %Y %X")
		created_at = datetime.datetime.strftime(member.created_at, "%d %B %Y %X")

		get_bio = (
			lambda: ""
			if data["bio"] == ""
			else f"""\n\n**Краткая информация о пользователе:**\n{data['bio']}\n\n"""
		)
		activity = member.activity

		def get_activity():
			if activity is None:
				return ""

			if activity.emoji is not None and activity.emoji.is_unicode_emoji():
				activity_info = (
					f"\n**Пользовательский статус:** {activity.emoji} {activity.name}"
				)
			else:
				if activity.emoji in self.client.emojis():
					activity_info = f"\n**Пользовательский статус:** {activity.emoji} {activity.name}"
				else:
					activity_info = f"\n**Пользовательский статус:** {activity.name}"

			return activity_info

		statuses = {
			"dnd": "<:dnd:730391353929760870> - Не беспокоить",
			"online": "<:online:730393440046809108> - В сети",
			"offline": "<:offline:730392846573633626> - Не в сети",
			"idle": "<:sleep:730390502972850256> - Отошёл",
		}

		emb = discord.Embed(
			title=f"Информация о пользователе - {member}", colour=discord.Color.green()
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_thumbnail(url=member.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		emb.add_field(
			name="Основная информация",
			value=f"""{get_bio()}**Имя пользователя:** {member}\n**Статус:** {statuses[member.status.name]}{get_activity()}\n**Id пользователя:** {member.id}\n**Акаунт созданн:** {created_at}\n**Присоиденился:** {joined_at}\n**Сообщений:** {all_message}\n**Вызванно команд:** {data["num_commands"]}""",
			inline=False,
		)
		await ctx.send(embed=emb)

	@commands.command(
		aliases=["useravatar", "avatar"],
		name="user-avatar",
		description="**Показывает аватар указаного учасника**",
		usage="user-avatar |@Участник|",
		help="**Примеры использования:**\n1. {Prefix}user-avatar @Участник\n2. {Prefix}user-avatar 660110922865704980\n3. {Prefix}user-avatar\n\n**Пример 1:** Покажет аватар упомянутого участника\n**Пример 2:** Покажет аватар участника с указаным id\n**Пример 3:** Покажет ваш аватар",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def avatar(self, ctx, member: discord.Member = None):
		if member is None:
			member = ctx.author

		emb = discord.Embed(title=f"Аватар {member.name}", colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_image(
			url=member.avatar_url_as(
				format="gif" if member.is_avatar_animated() else "png", size=2048
			)
		)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		name="info-bot",
		aliases=["botinfo", "infobot", "bot-info", "about", "bot"],
		usage="info-bot",
		description="Подробная информация о боте",
		help="**Примеры использования:**\n1. {Prefix}info-bot\n\n**Пример 1:** Покажет информацию обо мне",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def bot(self, ctx):
		def bytes2human(number, typer=None):
			if typer == "system":
				symbols = ("KБ", "МБ", "ГБ", "TБ", "ПБ", "ЭБ", "ЗБ", "ИБ")
			else:
				symbols = ("K", "M", "G", "T", "P", "E", "Z", "Y")

			prefix = {}
			for i, s in enumerate(symbols):
				prefix[s] = 1 << (i + 1) * 10

			for s in reversed(symbols):
				if number >= prefix[s]:
					value = float(number) / prefix[s]
					return "%.1f%s" % (value, s)

			return f"{number}B"

		commands_count = (await self.client.database.execute(
			query="""SELECT count FROM bot_stats WHERE entity = 'all commands' ORDER BY count DESC LIMIT 1""",
			fetchone=True,
		))[0]
		embed1 = discord.Embed(
			title=f"{self.client.user.name}#{self.client.user.discriminator}",
			description=f"Информация о боте **{self.client.user.name}**.\nМного-функциональный бот со своей экономикой, кланами и системой модерации!",
			color=discord.Color.green(),
		)
		embed1.add_field(
			name="Создатель бота:", value="Mr. Kola#0684, 𝚅𝚢𝚝𝚑𝚘𝚗.𝚕𝚞𝚒#9339", inline=False
		)
		embed1.add_field(
			name="Проект был созданн с помощью:",
			value=f"discord.py, sanic\ndiscord.py: {discord.__version__}, sanic: {sanic.__version__}",
			inline=False,
		)
		embed1.add_field(
			name="Статистика:",
			value=f"Участников: {len(self.client.users)}, Серверов: {len(self.client.guilds)}, Шардов: {self.client.shard_count}\nОбработано команд: {commands_count}",
			inline=False,
		)
		embed1.add_field(
			name="Uptime:",
			value=str(datetime.datetime.now()-self.client.launched_at),
			inline=False
		)
		embed1.add_field(
			name="Полезные ссылки",
			value=f"[Приглашение Бота](https://discord.com/api/oauth2/authorize?client_id=700767394154414142&permissions=8&scope=bot)\n[Сервер поддержки]({self.HELP_SERVER})\n[Patreon](https://www.patreon.com/join/prostotools)\n[API](http://api.prosto-tools.ml/)\n[Документация](https://vythonlui.gitbook.io/prostotools/)\n[SDC](https://bots.server-discord.com/700767394154414142)\n[Boticord](https://boticord.top/bot/700767394154414142)",
			inline=False,
		)
		embed1.set_thumbnail(url=self.client.user.avatar_url)
		embed1.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)

		mem = ps.virtual_memory()
		ping = self.client.latency

		ping_emoji = "🟩🔳🔳🔳🔳"
		ping_list = [
			{"ping": 0.00000000000000000, "emoji": "🟩🔳🔳🔳🔳"},
			{"ping": 0.10000000000000000, "emoji": "🟧🟩🔳🔳🔳"},
			{"ping": 0.15000000000000000, "emoji": "🟥🟧🟩🔳🔳"},
			{"ping": 0.20000000000000000, "emoji": "🟥🟥🟧🟩🔳"},
			{"ping": 0.25000000000000000, "emoji": "🟥🟥🟥🟧🟩"},
			{"ping": 0.30000000000000000, "emoji": "🟥🟥🟥🟥🟧"},
			{"ping": 0.35000000000000000, "emoji": "🟥🟥🟥🟥🟥"},
		]
		for ping_one in ping_list:
			if ping <= ping_one["ping"]:
				ping_emoji = ping_one["emoji"]
				break

		embed2 = discord.Embed(title="Статистика Бота", color=discord.Color.green())
		embed2.add_field(
			name="Использование CPU",
			value=f"В настоящее время используется: {ps.cpu_percent()}%",
			inline=True,
		)
		embed2.add_field(
			name="Использование RAM",
			value=f'Доступно: {bytes2human(mem.available, "system")}\nИспользуется: {bytes2human(mem.used, "system")} ({mem.percent}%)\nВсего: {bytes2human(mem.total, "system")}',
			inline=True,
		)
		embed2.add_field(
			name="Пинг Бота",
			value=f"Пинг: {ping * 1000:.0f}ms\n`{ping_emoji}`",
			inline=True,
		)

		for disk in ps.disk_partitions():
			usage = ps.disk_usage(disk.mountpoint)
			embed2.add_field(name="‎‎‎‎", value=f"```{disk.device}```", inline=False)
			embed2.add_field(
				name="Всего на диске",
				value=bytes2human(usage.total, "system"),
				inline=True,
			)
			embed2.add_field(
				name="Свободное место на диске",
				value=bytes2human(usage.free, "system"),
				inline=True,
			)
			embed2.add_field(
				name="Используемое дисковое пространство",
				value=bytes2human(usage.used, "system"),
				inline=True,
			)

		embeds = [embed1, embed2]
		message = await ctx.send(embed=embed1)
		page = Paginator(
			self.client,
			message,
			only=ctx.author,
			use_more=False,
			embeds=embeds,
			language="ru",
			timeout=120,
			use_exit=True,
			delete_message=False,
		)
		await page.start()

	@commands.command(
		aliases=["server", "serverinfo", "guild", "guildinfo", "guild-info"],
		name="server-info",
		description="**Показывает информацию о сервере**",
		usage="server-info",
		help="**Примеры использования:**\n1. {Prefix}server-info\n\n**Пример 1:** Покажет информацию о сервере",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def serverinfo(self, ctx):
		data = await self.client.database.sel_guild(guild=ctx.guild)
		created_at = datetime.datetime.strftime(ctx.guild.created_at, "%d %B %Y %X")
		time = data["timedelete_textchannel"]
		max_warns = data["max_warns"]
		all_message = data["all_message"]

		if data["idea_channel"] != 0:
			ideachannel = f"<#{int(data['idea_channel'])}>"
		else:
			ideachannel = "Не указан"

		if data["textchannels_category"] != 0:
			text_category = get(
				ctx.guild.categories, id=int(data["textchannels_category"])
			).name
		else:
			text_category = "Не указана"

		exp_multi = str(data["exp_multi"] * 100) + "%"
		verifications = {
			"none": ":white_circle: — Нет верификации",
			"low": ":green_circle: — Маленькая верификация",
			"medium": ":yellow_circle: — Средняя верификация",
			"high": ":orange_circle: — Большая верификация",
			"extreme": ":red_circle: - Наивысшая верификация",
		}
		regions = {
			"us_west": ":flag_us: — Запад США",
			"us_east": ":flag_us: — Восток США",
			"us_central": ":flag_us: — Центральный офис США",
			"us_south": ":flag_us: — Юг США",
			"sydney": ":flag_au: — Сидней",
			"eu_west": ":flag_eu: — Западная Европа",
			"eu_east": ":flag_eu: — Восточная Европа",
			"eu_central": ":flag_eu: — Центральная Европа",
			"singapore": ":flag_sg: — Сингапур",
			"russia": ":flag_ru: — Россия",
			"southafrica": ":flag_za:  — Южная Африка",
			"japan": ":flag_jp: — Япония",
			"brazil": ":flag_br: — Бразилия",
			"india": ":flag_in: — Индия",
			"hongkong": ":flag_hk: — Гонконг",
		}

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
		bots = len([str(member.id) for member in ctx.guild.members if member.bot])

		emb = discord.Embed(
			title="Информация о вашем сервере", colour=discord.Color.green()
		)

		emb.add_field(
			name=f"Основная информация",
			value=f"**Название сервера:** {ctx.guild.name}\n**Id сервера:** {ctx.guild.id}\n**Регион сервера:** {regions[ctx.guild.region.name]}\n**Уровень верификации:** {verifications[ctx.guild.verification_level.name]}\n**Всего сообщений:** {all_message}\n**Владелец сервера:** {ctx.guild.owner.name+ctx.guild.owner.discriminator}\n**Созданн:** {created_at}",
			inline=False,
		)
		emb.add_field(
			name="Статистика",
			value=f"**<:channels:730400768049414144> Всего каналов:** {len(ctx.guild.channels)}\n**<:text_channel:730396561326211103> Текстовых каналов:** {len(ctx.guild.text_channels)}\n**<:voice_channel:730399079418429561> Голосовых каналов:** {len(ctx.guild.voice_channels)}\n**<:category:730399838897963038> Категорий:** {len(ctx.guild.categories)}\n**<:role:730396229220958258> Количество ролей:** {len(ctx.guild.roles)}",
			inline=False,
		)
		emb.add_field(
			name="Участники",
			value=f"**:baby: Общее количество участников:** {ctx.guild.member_count}\n**<:bot:731819847905837066> Боты:** {bots}\n**<:sleep:730390502972850256> Отошли:** {sleep}\n**<:dnd:730391353929760870> Не беспокоить:** {dnd}\n**<:offline:730392846573633626> Не в сети:** {offline}\n**<:online:730393440046809108> В сети:** {online}",
			inline=False,
		)
		emb.add_field(
			name="Настройки сервера",
			value=f"**Канал идей:** {ideachannel}\n**Категория приватных текстовых каналов:** {text_category}\n**Максимальное количество предупрежденний:** {max_warns}\n**Время удаления приватного текстового канала:** {time}мин\n**Множитель опыта:** {exp_multi}",
			inline=False,
		)

		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		aliases=["idea", "guildidea"],
		name="guild-idea",
		description="**Отправляет вашу идею (Cooldown - 30мин)**",
		usage="guild-idea [Ваша идея]",
		help="**Примеры использования:**\n1. {Prefix}guild-idea I have an idea\n\n**Пример 1:** Отправит идею `I have an idea` в настроеный канал дял идей сервера",
	)
	@commands.cooldown(1, 7200, commands.BucketType.member)
	async def idea(self, ctx, *, text: str):
		data = await self.client.database.sel_guild(guild=ctx.guild)
		idea_channel_id = data["idea_channel"]

		if idea_channel_id is None:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Не указан канал идей. Обратитесь к администации сервера**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			self.idea.reset_cooldown(ctx)
			await ctx.message.add_reaction("❌")
			return
		else:
			if idea_channel_id in [channel.id for channel in ctx.guild.channels]:
				idea_channel = self.client.get_channel(int(idea_channel_id))
				emb = discord.Embed(
					title="Новая идея!",
					description=f"**От {ctx.author.mention} прийшла идея: {text}**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_thumbnail(url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await idea_channel.send(embed=emb)
			else:
				emb = discord.Embed(
					title="Ошибка!",
					description="**Канал идей удален. Обратитесь к администации сервера**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				self.idea.reset_cooldown(ctx)
				await ctx.message.add_reaction("❌")
				return

	@commands.command(
		description="**Отправляет ссылку на приглашения бота на сервер**",
		usage="invite",
		help="**Примеры использования:**\n1. {Prefix}invite\n\n**Пример 1:** Отправит приглашения на меня",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def invite(self, ctx):
		emb = discord.Embed(
			title="Пригласи бота на свой сервер =).**Жмякай!**",
			url="https://discord.com/api/oauth2/authorize?client_id=700767394154414142&permissions=8&scope=bot",
			colour=discord.Color.green(),
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_thumbnail(url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		aliases=["msg-f", "msg-forward", "msgf", "msg-forw"],
		name="message-forward",
		description="**Перенаправляет ваше сообщения в указаный канал(Cooldown - 2 мин)**",
		usage="message-forward [Канал] [Сообщения]",
		help="**Примеры использования:**\n1. {Prefix}message-forward #Канал Hello everyone\n2. {Prefix}message-forward 717776571406090313 Hello everyone\n\n**Пример 1:** Перенаправит сообщения `Hello everyone` в упомянутый канал\n**Пример 2:**  Перенаправит сообщения `Hello everyone` в канал с указаным id",
	)
	@commands.cooldown(1, 120, commands.BucketType.member)
	async def msgforw(self, ctx, channel: discord.TextChannel, *, msg: str):
		if ctx.author.permissions_in(channel).send_messages:
			emb = discord.Embed(
				title="Новое сообщения!",
				description=f"{ctx.author.mention} Перенаправил сообщения в этот канал. **Само сообщения: {msg}**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_thumbnail(url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await channel.send(embed=emb)
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Отказанно в доступе! Вы не имеете прав в указном канале**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.msgforw.reset_cooldown(ctx)
			return

	@commands.command(
		description="**Отправляет ваше сообщения от именни бота(Cooldown - 30 сек после трёх попыток)**",
		usage="say [Сообщения]",
		help="**Примеры использования:**\n1. {Prefix}say Hello, I am write a text\n\n**Пример 1:** Отправит указаное сообщения от именни бота в текущем канале и удалит сообщения участника",
	)
	@commands.cooldown(3, 30, commands.BucketType.member)
	async def say(self, ctx, *, text: str):
		try:
			await ctx.message.delete()
		except:
			pass
		await ctx.send(text)

	@commands.command(
		aliases=["rnum", "randomnumber"],
		name="random-number",
		description="**Пишет рандомное число в указаном диапазоне**",
		usage="random-number [Первое число (От)] [Второе число (До)]",
		help="**Примеры использования:**\n1. {Prefix}rnum 1 10\n\n**Пример 1:** Выберет рандомное число в диапазоне указаных",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def rnum(self, ctx, rnum1: int, rnum2: int):
		if len(str(rnum1)) > 64 or len(str(rnum2)) > 64:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Укажите число меньше 64 в длинне!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		emb = discord.Embed(
			title=f"Рандомное число от {rnum1} до {rnum2}",
			description=f"**Бот зарандомил число {randint(rnum1, rnum2)}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Устанавливает краткое описания о вас**",
		usage="bio [Текст]",
		help="**Примеры использования:**\n1. {Prefix}bio -\n2. {Prefix}bio\n3. {Prefix}bio New biography\n\n**Пример 1:** Очистит биографию\n**Пример 2:** Покажет текущую биограцию\n**Пример 3:** Поставит новую биограцию - `New biography`",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def bio(self, ctx, *, text: str = None):
		cur_bio = (await self.client.database.sel_user(target=ctx.author))["bio"]

		clears = ["clear", "-", "delete", "очистить", "удалить"]
		if text in clears:
			sql = """UPDATE users SET bio = %s WHERE user_id = %s"""
			val = ("", ctx.author.id)

			await self.client.database.execute(sql, val)

			await ctx.message.add_reaction("✅")
			return
		if text is None:
			emb = discord.Embed(
				title="Ваша биография",
				description="У вас нету биографии" if cur_bio == "" else cur_bio,
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return
		if len(text) > 1000:
			await ctx.message.add_reaction("❌")
			return

		sql = """UPDATE users SET bio = %s WHERE user_id = %s"""
		val = (text, ctx.author.id)

		await self.client.database.execute(sql, val)

		await ctx.message.add_reaction("✅")

	@commands.command(
		name="calc",
		aliases=["calculator", "c"],
		description="Выполняет математические операции",
		usage="calc [Операция]",
		help="**Примеры использования:**\n1. {Prefix}calc 2+1\n\n**Пример 1:** Вычислит уравнения `2+1`",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def calc(self, ctx, *, exp: str = None):
		if exp is None:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Укажите пример!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		link = "http://api.mathjs.org/v4/"
		data = {"expr": [exp]}

		try:
			re = requests.get(link, params=data)
			responce = re.json()

			emb = discord.Embed(title="Калькулятор", color=discord.Color.green())
			emb.add_field(name="Задача:", value=exp)
			emb.add_field(name="Решение:", value=str(responce))
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		except:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Что-то пошло не так :(**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return


def setup(client):
	client.add_cog(Different(client))
