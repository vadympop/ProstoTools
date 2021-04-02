import discord

from core.converters import ColorConverter
from core.bases.cog_base import BaseCog
from discord.ext import commands
from random import randint


class Different(BaseCog):
	@commands.group()
	@commands.cooldown(1, 300, commands.BucketType.member)
	async def color(self):
		pass

	@color.command(
		usage="color [Цвет]",
		description="Устанавливает роль с указанным цветом",
		help="**Полезное:**\nЦвет надо указывать в формате HEX - #444444\n\n**Примеры использования:**\n1. {Prefix}color #444444\n2. {Prefix}color remove\n\n**Пример 1:** Установит вам роль с указаным цветом в HEX формате(Поддерживаеться только HEX)\n**Пример 2:** Удалить у вас роль с цветом",
	)
	@commands.bot_has_permissions(manage_roles=True)
	async def color_set(self, ctx, color: ColorConverter):
		if ctx.invoked_subcommand is None:
			if (ctx.author.top_role.position + 1) >= ctx.guild.me.top_role.position:
				emb = await self.client.utils.create_error_embed(
					ctx, "У меня не хватает прав на добавления роли к вам!"
				)
				await ctx.send(embed=emb)
				return

			for r in ctx.author.roles:
				if r.name.startswith(self.client.config.COLOR_ROLE):
					await r.delete()
					break

			name = self.client.config.COLOR_ROLE+str(color)
			roles = {role.name: role.id for role in ctx.guild.roles}
			if name in roles.keys():
				role = ctx.guild.get_role(roles[name])
			else:
				role = await ctx.guild.create_role(
					name=name,
					color=color
				)
				await role.edit(position=ctx.author.top_role.position+1)
			await ctx.author.add_roles(role)
			try:
				await ctx.message.add_reaction("✅")
			except discord.errors.Forbidden:
				pass
			except discord.errors.HTTPException:
				pass

	@color.command(
		name="delete",
		usage="color delete",
		aliases=["rs", "reset", "rm", "remove", "del", "rem"],
		description="Удаляет роль цвета"
	)
	@commands.bot_has_permissions(manage_roles=True)
	async def color_reset(self, ctx):
		state = False
		for role in ctx.author.roles:
			if role.name.startswith(self.client.config.COLOR_ROLE):
				await role.delete()
				state = True
				break

		if not state:
			emb = await self.client.utils.create_error_embed(
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

	@commands.command(
		aliases=["usersend"],
		name="user-send",
		description="Отправляет сообщения указаному участнику",
		usage="user-send [@Участник] [Сообщения]",
		help="**Примеры использования:**\n1. {Prefix}user-send @Участник Hello my friend\n2. {Prefix}user-send 660110922865704980 Hello my friend\n\n**Пример 1:** Отправит упомянутому участнику сообщения `Hello my friend`\n**Пример 2:** Отправит участнику с указаным id сообщения `Hello my friend`",
	)
	@commands.cooldown(2, 60, commands.BucketType.member)
	async def send(self, ctx, member: discord.Member, *, message: str):
		data = await self.client.database.sel_user(target=ctx.author)

		if not data.items:
			emb = await self.client.utils.create_error_embed(
				ctx, "У вас нет необходимых предметов!"
			)
			await ctx.send(embed=emb)
			self.send.reset_cooldown(ctx)
			return

		if "sim" not in data.items and "tel" not in data.items and data.coins < 50:
			emb = await self.client.utils.create_error_embed(
				ctx, "У вас нет необходимых предметов или не достаточно коинов!"
			)
			await ctx.send(embed=emb)
			self.send.reset_cooldown(ctx)
			return

		emb = discord.Embed(
			title=f"Новое сообщения от {ctx.author.name}",
			description=f"**{message}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except discord.Forbidden:
			await ctx.send("Я не смог отправить сообщения указанному пользователю!")
		else:
			await self.client.database.update(
				"users",
				where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
				coins=data.coins - 50
			)
			await ctx.send("Успешно!")

	@commands.command(
		description="Отправляет баг",
		usage="bug [Описания]",
		help="**Примеры использования:**\n1. {Prefix}bug Я нашел баг...\n\n**Пример 1:** Отправит баг с указанным описаниям",
	)
	@commands.cooldown(1, 3600, commands.BucketType.member)
	async def bug(self, ctx, *, description: str):
		bug_channel = self.client.get_channel(792820806132564028)
		emb = discord.Embed(
			description=f"Описания бага: \n>>> {description}",
			colour=discord.Color.orange()
		)
		emb.set_author(name=f"Баг нашел {ctx.author} | {ctx.author.id}", icon_url=ctx.author.avatar_url)
		emb.set_thumbnail(url=ctx.guild.icon_url)
		emb.set_footer(text=f"Сервер: {ctx.guild.name} | {ctx.guild.id}")
		await bug_channel.send(
			embed=emb,
			files=[
				await attachment.to_file(use_cached=False, spoiler=True)
				for attachment in ctx.message.attachments
			]
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@commands.command(
		description="Отправляет идею",
		usage="idea [Описания]",
		help="**Примеры использования:**\n1. {Prefix}idea У меня появилась идея!\n\n**Пример 1:** Отправит идею с указанным описаниям",
	)
	@commands.cooldown(1, 3600, commands.BucketType.member)
	async def idea(self, ctx, *, description: str):
		idea_channel = self.client.get_channel(799635206390284298)
		emb = discord.Embed(
			description=f"Описания идеи: \n>>> {description}",
			colour=discord.Color.blurple()
		)
		emb.set_author(name=f"Идея от {ctx.author} | {ctx.author.id}", icon_url=ctx.author.avatar_url)
		emb.set_thumbnail(url=ctx.guild.icon_url)
		emb.set_footer(text=f"Сервер: {ctx.guild.name} | {ctx.guild.id}")
		await idea_channel.send(
			embed=emb,
			files=[
				await attachment.to_file(use_cached=False, spoiler=True)
				for attachment in ctx.message.attachments
			]
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@commands.command(
		aliases=["useravatar", "avatar"],
		name="user-avatar",
		description="Показывает аватар указанного участника",
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
		description="Отправляет ваше сообщения от именни бота",
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
		description="Пишет рандомное число в указаном диапазоне",
		usage="random-number [Первое число (От)] [Второе число (До)]",
		help="**Примеры использования:**\n1. {Prefix}rnum 1 10\n\n**Пример 1:** Выберет рандомное число в диапазоне указаных",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def rnum(self, ctx, rnum1: int, rnum2: int):
		if len(str(rnum1)) > 64 or len(str(rnum2)) > 64:
			emb = await self.client.utils.create_error_embed(
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
		description="Устанавливает краткое описания о вас",
		usage="bio [Текст]",
		help="**Примеры использования:**\n1. {Prefix}bio -\n2. {Prefix}bio\n3. {Prefix}bio New biography\n\n**Пример 1:** Очистит биографию\n**Пример 2:** Покажет текущую биограцию\n**Пример 3:** Поставит новую биограцию - `New biography`",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def bio(self, ctx, *, text: str = None):
		cur_bio = (await self.client.database.sel_user(target=ctx.author)).bio

		clears = ["clear", "-", "delete", "очистить", "удалить"]
		if text in clears:
			await self.client.database.update(
				"users",
				where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
				bio=""
			)
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
			emb = await self.client.utils.create_error_embed(
				ctx, "Укажите пример!"
			)
			await ctx.send(embed=emb)
			return

		link = "http://api.mathjs.org/v4/"
		data = {"expr": [exp]}

		try:
			response = await self.client.http_client.get(link, params=data)

			emb = discord.Embed(title="Калькулятор", color=discord.Color.green())
			emb.add_field(name="Задача:", value=exp)
			emb.add_field(name="Решение:", value=str(response))
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		except:
			emb = await self.client.utils.create_error_embed(
				ctx, "Что-то пошло не так :("
			)
			await ctx.send(embed=emb)
			return


def setup(client):
	client.add_cog(Different(client))
