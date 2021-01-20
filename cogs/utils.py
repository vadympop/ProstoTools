import discord
import json
import asyncio
import uuid
from discord.ext import commands
from discord.utils import get


async def check_role(ctx):
	data = json.loads(await ctx.bot.database.get_moder_roles(guild=ctx.guild))
	roles = ctx.guild.roles[::-1]
	data.append(roles[0].id)

	if data != []:
		for role_id in data:
			role = get(ctx.guild.roles, id=role_id)
			if role in ctx.author.roles:
				return True
		return ctx.author.guild_permissions.administrator
	else:
		return ctx.author.guild_permissions.administrator


class Utils(commands.Cog, name="Utils"):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT

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
		on_answers = ["on", "вкл", "включить", "true"]
		off_answers = ["off", "выкл", "выключить", "false"]

		if state.lower() in on_answers:
			data = (await self.client.database.sel_guild(guild=ctx.guild))["voice_channel"]

			if "channel_id" not in data:
				channel_category = await ctx.guild.create_category("Голосовые комнаты")
				voice_channel = await ctx.guild.create_voice_channel(
					"Нажми на меня", category=channel_category
				)
				data.update({"channel_id": voice_channel.id})
				await self.client.database.update(
					"guilds",
					where={"guild_id": ctx.guild.id},
					voice_channel=json.dumps(data)
				)
				try:
					await ctx.message.add_reaction("✅")
				except discord.errors.Forbidden:
					pass
				except discord.errors.HTTPException:
					pass
			else:
				emb = await self.client.utils.create_error_embed(
					ctx, "На этом сервере приватные голосовые комнаты уже включены!"
				)
				await ctx.send(embed=emb)
				return

		elif state in off_answers:
			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				voice_channel=json.dumps({})
			)
			try:
				await ctx.message.add_reaction("✅")
			except discord.errors.Forbidden:
				pass
			except discord.errors.HTTPException:
				pass
		else:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не правильно указали действие! Укажите из этих вариантов: on, off!"
			)
			await ctx.send(embed=emb)
			return

	@commands.command(
		aliases=["serverstats"],
		name="server-stats",
		hidden=True,
		description="**Создает статистику сервера**",
		usage="server-stats [Счетчик] |off|",
		help="**Примеры использования:**\n1. {Prefix}server-stats all\n2. {Prefix}server-stats сообщения\n\n**Пример 1:** Создаёт счетчик всех пользователей сервера\n**Пример 2:** Создаёт сообщения в текущем канале с основной информацией о сервере",
	)
	@commands.check(lambda ctx: ctx.author == ctx.guild.owner)
	@commands.cooldown(1, 60, commands.BucketType.member)
	async def serverstats(self, ctx, counter: str, action: str = None):
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

		if counter.lower() in ["message", "сообщения"]:
			async with ctx.typing():
				val = (ctx.guild.id, ctx.guild.id)
				sql_1 = """SELECT user_id, exp, money, reputation, messages FROM users WHERE guild_id = %s AND guild_id = %s ORDER BY exp DESC LIMIT 20"""
				sql_2 = """SELECT exp FROM users WHERE guild_id = %s AND guild_id = %s"""

				all_exp = sum([i[0] for i in await self.client.database.execute(sql_2, val)])
				data = await self.client.database.execute(sql_1, val)
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
							if len(member.name) > 10:
								member = (
									member.name[:10] + "..." + "#" + member.discriminator
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
				try:
					await ctx.message.add_reaction("✅")
				except discord.errors.Forbidden:
					pass
				except discord.errors.HTTPException:
					pass

				server_stats = (await self.client.database.sel_guild(guild=ctx.guild))["server_stats"]
				server_stats.update({"message": [message.id, ctx.channel.id]})
				await self.client.database.update(
					"guilds",
					where={"guild_id": ctx.guild.id},
					server_stats=json.dumps(server_stats)
				)
			await asyncio.sleep(10)
			try:
				await ctx.message.delete()
			except:
				pass
			return

		if counter.lower() not in counters.keys():
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не правильно указали счетчик. Укажите из этих: bots, all, members, roles, channels"
			)
			await ctx.send(embed=emb)
			return

		async with ctx.typing():
			data = (await self.client.database.sel_guild(guild=ctx.guild))["server_stats"]
			if action is not None:
				if action.lower() == "off":
					if counter.lower() in data.keys():
						channel_id = data.pop(counter.lower())
						channel = ctx.guild.get_channel(channel_id)
						if channel is not None:
							await channel.delete()
						if "category" in data.keys():
							category_id = data.get("category")
							category = ctx.guild.get_channel(category_id)
							if category is not None:
								if len(category.channels) <= 0:
									await category.delete()
									data.pop("category")
					else:
						emb = await self.client.utils.create_error_embed(
							ctx, "Указаный счетчик не включен!"
						)
						await ctx.send(embed=emb)
						return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите `off` чтобы выключить счетчик или не указывайте ничего для включения"
					)
					await ctx.send(embed=emb)
					return
			else:
				if "category" not in data.keys():
					stats_category = await ctx.guild.create_category("Статистика")
				else:
					stats_category = ctx.guild.get_channel(data["category"])
					if stats_category is None:
						stats_category = await ctx.guild.create_category("Статистика")
				overwrites = {
					ctx.guild.default_role: discord.PermissionOverwrite(connect=False),
					ctx.guild.me: discord.PermissionOverwrite(connect=True, manage_permissions=True, manage_channels=True)
				}
				stats_channel = await ctx.guild.create_voice_channel(
					f"[{counters[counter.lower()][1]}] {counters[counter.lower()][0]}",
					category=stats_category,
					overwrites=overwrites
				)
				await stats_category.edit(position=0)
				data.update({counter.lower(): stats_channel.id, "category": stats_category.id})
			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				server_stats=json.dumps(data)
			)
			try:
				await ctx.message.add_reaction("✅")
			except discord.errors.Forbidden:
				pass
			except discord.errors.HTTPException:
				pass

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
		if role.is_integration():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль управляется интеграцией!")
			await ctx.send(embed=emb)
			return

		if role.is_bot_managed():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль управляется ботом!")
			await ctx.send(embed=emb)
			return

		if role.is_premium_subscriber():
			emb = await self.client.utils.create_error_embed(
				ctx, "Указанная роль используеться для бустером сервера!"
			)
			await ctx.send(embed=emb)
			return

		if for_role.is_integration():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль управляется интеграцией!")
			await ctx.send(embed=emb)
			return

		if for_role.is_bot_managed():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль управляется ботом!")
			await ctx.send(embed=emb)
			return

		if for_role.is_premium_subscriber():
			emb = await self.client.utils.create_error_embed(
				ctx, "Указанная роль используеться для бустером сервера!"
			)
			await ctx.send(embed=emb)
			return

		if type_act == "add":
			async with ctx.typing():
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
			async with ctx.typing():
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
		data = (await self.client.database.sel_guild(guild=ctx.guild))["moder_roles"]
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
		brief="True",
		aliases=["mutes-list", "listmutes", "muteslist", "mutes"],
		name="list-mutes",
		description="Показывает все мьюты на сервере",
		usage="list-mutes",
		help="**Примеры использования:**\n1. {Prefix}list-mutes\n\n**Пример 1:** Показывает все мьюты на сервере",
	)
	@commands.check(check_role)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def mutes(self, ctx):
		data = await self.client.database.get_mutes(ctx.guild.id)

		if data != ():
			mutes = "\n\n".join(
				f"**Пользователь:** `{ctx.guild.get_member(mute[1])}`, **Причина:** `{mute[3]}`\n**Автор:** {str(ctx.guild.get_member(mute[6]))}, **Время мьюта:** `{mute[5]}`\n**Активный до**: `{mute[4]}`"
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
		description="**Отправляет ключ API для сервера**",
		usage="api-key",
		help="**Примеры использования:**\n1. {Prefix}api-key\n\n**Пример 1:** Отправляет ключ API сервера",
	)
	@commands.check(lambda ctx: ctx.author == ctx.guild.owner)
	@commands.cooldown(1, 60, commands.BucketType.member)
	async def api_key(self, ctx):
		key = (await self.client.database.sel_guild(guild=ctx.guild))["api_key"]

		await ctx.author.send(
			f"Ключ API сервера - {ctx.guild.name}: `{key}`\n**__Никому его не передавайте. Он даёт доступ к данным сервера__**"
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@commands.command(
		aliases=["regenerateapikey"],
		name="regenerate-api-key",
		hidden=True,
		description="**Перегенерирует ключ API для сервера**",
		usage="regenerate-api-key",
		help="**Примеры использования:**\n1. {Prefix}regenerate-api-key\n\n**Пример 1:** Перегенерирует ключ API для сервера",
	)
	@commands.check(lambda ctx: ctx.author.id == ctx.guild.owner.id)
	@commands.cooldown(1, 43200, commands.BucketType.member)
	async def regenerate_api_key(self, ctx):
		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			api_key=str(uuid.uuid4())
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass


def setup(client):
	client.add_cog(Utils(client))
