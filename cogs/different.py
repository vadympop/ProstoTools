import time
import datetime
import discord
import requests
from discord.ext import commands
from discord.utils import get
from tools.paginator import Paginator
from random import randint


class Different(commands.Cog, name="Different"):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT

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
			if not reminder_id:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Превишен лимит напоминалок(25)!**",
				)
				await ctx.send(embed=emb)
				return

			emb = discord.Embed(
				title=f"Созданно новое напоминая #{reminder_id}",
				description=f"**Текст напоминая:**\n```{text}```\n**Действует до:**\n`{datetime.datetime.fromtimestamp(times).strftime('%d %B %Y %X')}`",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif action == "list":
			data = await self.client.database.get_reminder(target=ctx.author)
			if data != ():
				embeds = []
				for reminder in data:
					active_to = datetime.datetime.fromtimestamp(reminder[4]).strftime('%d %B %Y %X')
					emb = discord.Embed(
						title="Список напоминаний",
						description=f"Id: **{reminder[0]}**\nДействует до: `{active_to}`\nТекст:\n>>> {reminder[5][:1024]}",
						colour=discord.Color.green(),
					)
					emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					embeds.append(emb)

				message = await ctx.send(embed=embeds[0])
				paginator = Paginator(ctx, message, embeds, footer=True)
				await paginator.start()
			else:
				emb = discord.Embed(
					title="Список напоминаний",
					description="У вас нету напоминаний",
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
					state = await self.client.database.del_reminder(ctx.guild.id, int(type_time))
					if state:
						emb = discord.Embed(
							description=f"Напоминания `#{type_time}` было успешно удалено",
							colour=discord.Color.green(),
						)
						emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
						emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
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

	@commands.group(
		name="status-reminder",
		aliases=[
			"sr",
			"statusreminder",
			"status_reminder",
			"status-remin",
			"statusremin",
			"status_remin"
		],
		usage="status-reminder [create/delete] |Id - если указано действия delete| |repeated/default| |@Участник| |Ожидаемый статус|",
		description="",
		help=""
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def status_reminder(self, ctx):
		if ctx.invoked_subcommand is None:
			emb = discord.Embed(
				title="Напоминания статусов",
				description=f"`create` - создаст новое напоминания\n`delete` - удалит напоминания\n`list` - покажет список ваших напоминаний статусов",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

	@status_reminder.command()
	async def create(self, ctx, type_reminder: str, member: discord.Member, *, status: str):
		types = ("default", "repeated")
		convert_shorts = {
			"r": "repeated",
			"d": "default"
		}
		statuses = ("dnd", "online", "offline", "idle")
		convert_statuses = {
			"не беспокоить": "dnd",
			"онлайн": "online",
			"оффлайн": "offline",
			"отошел": "idle"
		}
		if type_reminder.lower() in convert_shorts.keys():
			type_reminder = convert_shorts[type_reminder.lower()]

		if type_reminder.lower() not in types:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите один из этих типов: default, repeated!**"
			)
			await ctx.send(embed=emb)
			return

		if status.lower() in convert_statuses.keys():
			status = convert_statuses[status.lower()]

		if status.lower() not in statuses:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите один из этих статусов: dnd, online, offline, idle!**"
			)
			await ctx.send(embed=emb)
			return

		state = await self.client.database.set_status_reminder(
			member.id, ctx.author.id, status.lower(), type_reminder.lower()
		)
		if not state:
			emb = await self.client.utils.create_error_embed(
				ctx, "**У вас уже есть напоминания статуса на этого участника/вы превысили максимальное количество напоминания(20)!**"
			)
			await ctx.send(embed=emb)
			return

		invert_convert_statuses = {k: x for x, k in convert_statuses.items()}
		emb = discord.Embed(
			title=f"Созданно новое напоминая статуса #{state}",
			description=f"Смотрит за: `{member}`\nЖдет статус: `{invert_convert_statuses[status.lower()]}`",
			colour=discord.Color.green(),
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@status_reminder.command()
	async def delete(self, ctx, reminder_id: int):
		state = await self.client.database.del_status_reminder(reminder_id)
		if not state:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Напоминания с указаным id не существует!**"
			)
			await ctx.send(embed=emb)
			return

		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@status_reminder.command()
	async def list(self, ctx):
		data = await self.client.database.get_status_reminder(member_id=ctx.author.id)
		if data != ():
			convert_statuses = {
				"dnd": "не беспокоить",
				"online": "онлайн",
				"offline": "оффлайн",
				"idle": "отошел"
			}

			description = "\n".join([
				f"Id: `{setting[0]}` Пользователь: `{self.client.get_user(setting[1])}` Ждет: `{convert_statuses[setting[3]]}` Повторяемый: `{'Да' if setting[4] == 'repeated' else 'Нет'}`"
				for setting in data
			])
		else:
			description = "У вас нету напоминаний статуса"

		emb = discord.Embed(
			title="Список напоминаний статуса",
			description=description,
			colour=discord.Color.green(),
		)
		emb.set_author(
			name=self.client.user.name, icon_url=self.client.user.avatar_url
		)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
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
				emb = await ctx.bot.utils.create_error_embed(
					ctx, "У вас нет роли цвета!"
				)
				await ctx.send(embed=emb)
				return

			try:
				await ctx.message.add_reaction("✅")
			except discord.errors.Forbidden:
				pass
			except discord.errors.HTTPException:
				pass
			return

		if color.startswith("#"):
			hex = color[1:]
			if len(hex) == 6:
				if (ctx.author.top_role.position + 1) >= ctx.guild.me.top_role.position:
					emb = await ctx.bot.utils.create_error_embed(
						ctx, "У меня не хватает прав на добавления роли к вам!"
					)
					await ctx.send(embed=emb)
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
				try:
					await ctx.message.add_reaction("✅")
				except discord.errors.Forbidden:
					pass
				except discord.errors.HTTPException:
					pass
			else:
				emb = await ctx.bot.utils.create_error_embed(
					ctx, "Указан не правильный формат цвета!"
				)
				await ctx.send(embed=emb)
				return
		else:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Указан не правильный формат цвета!"
			)
			await ctx.send(embed=emb)
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

		if cur_items != []:
			if "sim" in cur_items and "tel" in cur_items and coins_member > 50:
				await self.client.database.update(
					"users",
					where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
					coins=coins_member-50
				)

				emb = discord.Embed(
					title=f"Новое сообщения от {ctx.author.name}",
					description=f"**{message}**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await member.send(embed=emb)
			else:
				emb = await ctx.bot.utils.create_error_embed(
					ctx, "У вас нет необходимых предметов или не достаточно коинов!"
				)
				await ctx.send(embed=emb)
				self.send.reset_cooldown(ctx)
				return
		else:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "У вас нет необходимых предметов!"
			)
			await ctx.send(embed=emb)
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
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не правильно указали флаг!"
			)
			await ctx.send(embed=emb)
			self.devs.reset_cooldown(ctx)
			return

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
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Не указан канал идей. Обратитесь к администации сервера"
			)
			await ctx.send(embed=emb)
			self.idea.reset_cooldown(ctx)
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
				emb = await ctx.bot.utils.create_error_embed(
					ctx, "Не указан канал идей. Обратитесь к администации сервера"
				)
				await ctx.send(embed=emb)
				self.idea.reset_cooldown(ctx)
				return

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
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Отказанно в доступе! Вы не имеете прав в указаном канале"
			)
			await ctx.send(embed=emb)
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
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Укажите число меньше 64 в длинне"
			)
			await ctx.send(embed=emb)
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
			try:
				await ctx.message.add_reaction("✅")
			except discord.errors.Forbidden:
				pass
			except discord.errors.HTTPException:
				pass
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
			try:
				await ctx.message.add_reaction("❌")
			except discord.errors.Forbidden:
				pass
			except discord.errors.HTTPException:
				pass
			return

		await self.client.database.update(
			"users",
			where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
			bio=text
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

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
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Укажите пример!"
			)
			await ctx.send(embed=emb)
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
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Что-то пошло не так :("
			)
			await ctx.send(embed=emb)
			return


def setup(client):
	client.add_cog(Different(client))
