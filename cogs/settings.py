import discord
import json
import typing
from discord.ext import commands


class Settings(commands.Cog, name="Settings"):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT
		self.commands = [
			command.name
			for cog in self.client.cogs
			for command in self.client.get_cog(cog).get_commands()
			if cog.lower() not in ("help", "owner", "jishaku")
		]

	def find_custom_command(self, command_name: str, commands: list):
		for command in commands:
			if command["name"] == command_name:
				return command
		return None

	@commands.group(
		help=f"""**Команды групы:** anti-invite, level-up-message, time-delete-channel, shop-role, exp-multi, text-channels-category, set-audit, max-warns, prefix, anti-flud, react-commands, moderation-role, ignore-channels, custom-command, auto-reactions, auto-responder\n\n"""
	)
	@commands.has_permissions(administrator=True)
	async def setting(self, ctx):
		if ctx.invoked_subcommand is None:
			PREFIX = str(await self.client.database.get_prefix(ctx.guild))
			commands = "\n".join(
				[f"`{PREFIX}setting {c.name}`" for c in self.client.get_command("setting").commands]
			)
			emb = discord.Embed(
				title="Команды настройки",
				description=commands,
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

	@setting.command(
		description="**Настройка префикса**",
		usage="setting prefix [Новый префикс]",
	)
	@commands.has_permissions(administrator=True)
	async def prefix(self, ctx, prefix: str):
		if len(prefix) > 3:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Количество символов в новом префиксе не должно превышать 3-х!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			prefix=prefix
		)

		emb = discord.Embed(
			description=f"**Вы успешно изменили префикс бота на этом сервере. Новый префикс {prefix}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@setting.command(
		aliases=["moder-role"],
		name="moderation-role",
		description="**Настройка ролей модераторов**",
		usage="setting moderation-role [add(Добавляет указаную роль)/clear(Очищает список)/del(Удаляет указаную роль)] |@Роль|",
	)
	@commands.has_permissions(administrator=True)
	async def moder_role(self, ctx, type_act: str, role: discord.Role = None):
		data = await self.client.database.sel_guild(guild=ctx.guild)
		cur_roles = data["moder_roles"]

		if type_act == "add":
			if role is None:
				emb = await self.client.utils.create_error_embed(ctx, "Укажите добавляемую роль!")
				await ctx.send(embed=emb)
				return

			if role.is_integration():
				emb = await self.client.utils.create_error_embed(ctx, "Указанная роль управляется интеграцией!")
				await ctx.send(embed=emb)
				return

			if role.is_bot_managed():
				emb = await self.client.utils.create_error_embed(ctx, "Указанная роль управляется ботом!")
				await ctx.send(embed=emb)
				return

			if role.is_premium_subscriber():
				emb = await self.client.utils.create_error_embed(ctx, "Указанная роль используеться для бустером сервера!")
				await ctx.send(embed=emb)
				return

			cur_roles.append(role.id)
			emb = discord.Embed(
				description=f"**Вы успешно добавили новую роль модератора! Добавленная роль - `{role.name}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif type_act == "clear":
			cur_roles = []
			emb = discord.Embed(
				description=f"**Вы успешно очистили список ролей модераторов!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif type_act == "delete":
			if role is None:
				emb = await self.client.utils.create_error_embed(ctx, "Укажите удаляемую роль!")
				await ctx.send(embed=emb)
				return

			try:
				cur_roles.remove(role.id)
			except ValueError:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**Такой роли нету в списке ролей модераторов!**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				return

			emb = discord.Embed(
				description=f"**Вы успешно удалили роль из ролей модераторов! Удалённая роль - `{role.name}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Укажите одно из этих действий: clear, delete, add!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			moderators=json.dumps(cur_roles)
		)

	@setting.command(
		name="ignore-channels",
		description="**Игнорируемые каналы в системе уровней**",
		usage="setting ignore-channels [Действие, add - добавляет канал в исключения, clear - очищает список исключений, delete - удаляет указаный канал из списка] [Id канала]",
	)
	@commands.has_permissions(administrator=True)
	async def ignoredchannels(self, ctx, typech: str, channel: discord.TextChannel = None):
		data = await self.client.database.sel_guild(guild=ctx.guild)
		cur_ignchannel = data["ignored_channels"]

		if typech == "add":
			if channel is None:
				emb = await self.client.utils.create_error_embed(ctx, "Укажите добавляемый канал!")
				await ctx.send(embed=emb)
				return

			cur_ignchannel.append(channel.id)
			emb = discord.Embed(
				description=f"**Вы успешно добавили новий канал в исключения! Добавлённый канал - {channel.mention}**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif typech == "clear":
			cur_ignchannel = []
			emb = discord.Embed(
				description=f"**Вы успешно очистили список исключенных каналов!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif typech == "delete":
			if channel is None:
				emb = await self.client.utils.create_error_embed(ctx, "Укажите удаляемый канал!")
				await ctx.send(embed=emb)
				return

			try:
				cur_ignchannel.remove(channel.id)
			except ValueError:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**Такого канала нету в списке игнорируемых каналов!**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				return

			emb = discord.Embed(
				description=f"**Вы успешно удалили канал из исключений! Удалённый канал - {channel.mention}**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не правильно указали действие!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			ignored_channels=json.dumps(cur_ignchannel)
		)

	@setting.command(
		name="shop-role",
		description="**Настройка магазина на сервере**",
		usage="setting shop-role [clear - очищает список ролей, add - добавляет роль, delete - удаляет роль] [@Роль] [Стоимость роли]",
	)
	@commands.has_permissions(administrator=True)
	async def shoplist(
		self, ctx, cl_add: typing.Optional[str], role: discord.Role, cost: int
	):
		data = await self.client.database.sel_guild(guild=ctx.guild)
		shoplist = data["shop_list"]

		if cost <= 0:
			emb = await self.client.create_error_embed(ctx, "Укажите стоимость предмета больше 0!")
			await ctx.send(embed=emb)
			return

		if role.is_integration():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль управляется интеграцией!")
			await ctx.send(embed=emb)
			return

		if role.is_bot_managed():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль управляется ботом!")
			await ctx.send(embed=emb)
			return

		if role.is_premium_subscriber():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль используеться для бустером сервера!")
			await ctx.send(embed=emb)
			return

		if cl_add == "add":
			shoplist.append([role.id, cost])
			emb = discord.Embed(
				description=f"**Добавленна новая роль - `{role}`, стоимость - `{cost}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif cl_add == "clear":
			shoplist = []
			emb = discord.Embed(
				description=f"**Ваш список продаваемых ролей успешно очищен**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
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
				emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				return

			emb = discord.Embed(
				description=f"**Вы успешно удалили продаваемую роль из списка продаваемых ролей! Удалённая роль - `{role}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif cl_add != "clear" and cl_add != "add":
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите одно из этих действий: add, clear, delete!**",
			)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			shop_list=json.dumps(shoplist)
		)

	@setting.command(
		name="text-channels-category",
		description="**Настройка категории приватных текстовых каналов**",
		usage="setting text-channels-category [Id категории]",
	)
	@commands.has_permissions(administrator=True)
	async def privatetextcategory(self, ctx, category: discord.CategoryChannel):
		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			textchannels_category=category.id
		)

		emb = discord.Embed(
			description=f"**Вы успешно настроили категорию для приватних текстовых каналов! Новая категория - {category.name}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@setting.command(
		description="**Настройка максимального количества предупрежденний**",
		usage="setting warns [count/punishment] [Опции...]",
	)
	@commands.has_permissions(administrator=True)
	async def warns(self, ctx, action: str, *options):
		warns_settings = (await self.client.database.sel_guild(guild=ctx.guild))["warns_settings"]
		if action.lower() == "count":
			if len(options) <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите максимальное количество предупреждений!"
				)
				await ctx.send(embed=emb)
				return

			number = list(options).pop(0)

			if not number.isdigit():
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите число!"
				)
				await ctx.send(embed=emb)
				return

			if number <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите максимальное количество предупреждений больше 0!"
				)
				await ctx.send(embed=emb)
				return

			if number >= 25:
				emb = await self.client.utils.create_error_embed(
					ctx, "Вы указали слишком большой лимит предупреждений!"
				)
				await ctx.send(embed=emb)
				return

			warns_settings.update({"max": number})
			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				warns_settings=json.dumps(warns_settings)
			)

			emb = discord.Embed(
				description=f"**Вы успешно настроили максимальное количество предупрежденний! Новое значения - `{number}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif action.lower() == "punishment":
			punishments = ("mute", "ban", "soft-ban", "kick")
			if options[0].lower() not in punishments:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите одно из этих наказаний: mute, ban, soft-ban, kick!**",
				)
				await ctx.send(embed=emb)
				return

			if len(options) < 2:
				list(options).append("-")

			warns_settings.update({"punishment": {
				"type": options[0],
				"time": options[1]
			}})

			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				warns_settings=json.dumps(warns_settings)
			)

			emb = discord.Embed(
				description=f"**Вы успешно настроили наказания после максимального количества предупреждений**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

	@setting.command(
		name="anti-flud",
		description="**Настройка анти-флуда(Бета-тест)**",
		usage="setting anti-flud [on/off/setting] |Настройка| |Опции...|",
	)
	@commands.has_permissions(administrator=True)
	async def anti_flud(self, ctx, action: str, setting: str = None, *options):
		ons = ("on", "вкл", "включить", "+", "1")
		offs = ("off", "выкл", "выключить", "-", "0")
		auto_mod = (await self.client.database.sel_guild(guild=ctx.guild))["auto_mod"]
		options = list(options)
		if action.lower() in ons:
			if auto_mod["anti_flud"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Анти-флуд уже включен!"
				)
				await ctx.send(embed=emb)
				return

			auto_mod["anti_flud"]["state"] = True

		elif action.lower() in offs:
			if not auto_mod["anti_flud"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Анти-флуд и так выключен!"
				)
				await ctx.send(embed=emb)
				return

			auto_mod["anti_flud"] = {"state": False}

		elif action.lower() == "setting":
			settings = ("message", "punishment", "target-channel", "ignore-channel", "target-role", "ignore-role")
			punishments = ("mute", "ban", "soft-ban", "warn", "kick")
			if setting is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите изменяемую настройку!"
				)
				await ctx.send(embed=emb)
				return

			if setting.lower() not in settings:
				emb = await self.client.utils.create_error_embed(
					ctx,
					"Укажите одну из этих настроек: message, punishment, target-channel, ignore-channel, target-role, ignore-role!"
				)
				await ctx.send(embed=emb)
				return

			if not auto_mod["anti_flud"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Сначала включите анти-флуд!"
				)
				await ctx.send(embed=emb)
				return

			if len(options) < 1:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите значения для настройки!"
				)
				await ctx.send(embed=emb)
				return

			if setting.lower() == "message":
				types = ("channel", "dm")
				if options[0] == "off":
					if "message" not in auto_mod["anti_flud"].keys():
						emb = await self.client.utils.create_error_embed(
							ctx, "**Сообщения не настроено!**",
						)
						await ctx.send(embed=emb)
						return

					auto_mod["anti_flud"].pop("message")
				elif options[0] in types:
					if len(options) < 2:
						emb = await self.client.utils.create_error_embed(
							ctx, "Укажите значения для настройки!"
						)
						await ctx.send(embed=emb)
						return

					auto_mod["anti_flud"].update({"message": {"type": options[0]}})
					options = list(options)
					options.pop(0)
					auto_mod["anti_flud"]["message"].update({"text": " ".join(options)})
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите один из этих типов: dm, channel!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "punishment":
				if options[0].lower() not in punishments:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих наказаний: mute, ban, soft-ban, warn, kick!**",
					)
					await ctx.send(embed=emb)
					return

				if len(options) < 2:
					options.append(None)

				auto_mod["anti_flud"].update({"punishment": {
					"type": options[0],
					"time": options[1]
				}})
			elif setting.lower() == "target-channel":
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите значения для настройки!"
					)
					await ctx.send(embed=emb)
					return

				channel_converter = commands.TextChannelConverter()
				channel = await channel_converter.convert(ctx, options[1])
				if options[0].lower() == "add":
					if "target_channels" not in auto_mod["anti_flud"]:
						auto_mod["anti_flud"].update({"target_channels": [channel.id]})
					else:
						auto_mod["anti_flud"]["target_channels"].append(channel.id)
				elif options[0].lower() == "delete":
					if "target_channels" not in auto_mod["anti_flud"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список каналов пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						try:
							auto_mod["anti_flud"]["target_channels"].remove(channel.id)
						except ValueError:
							emb = await self.client.utils.create_error_embed(
								ctx, "**В списке каналов нету указаного канала!**",
							)
							await ctx.send(embed=emb)
							return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: add, delete!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "ignore-channel":
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите значения для настройки!"
					)
					await ctx.send(embed=emb)
					return

				channel_converter = commands.TextChannelConverter()
				channel = await channel_converter.convert(ctx, options[1])
				if options[0].lower() == "add":
					if "ignore_channels" not in auto_mod["anti_flud"]:
						auto_mod["anti_flud"].update({"ignore_channels": [channel.id]})
					else:
						auto_mod["anti_flud"]["ignore_channels"].append(channel.id)
				elif options[0].lower() == "delete":
					if "ignore_channels" not in auto_mod["anti_flud"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список каналов пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						try:
							auto_mod["anti_flud"]["ignore_channels"].remove(channel.id)
						except ValueError:
							emb = await self.client.utils.create_error_embed(
								ctx, "**В списке каналов нету указаного канала!**",
							)
							await ctx.send(embed=emb)
							return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: add, delete!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "target-role":
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите значения для настройки!"
					)
					await ctx.send(embed=emb)
					return

				role_converter = commands.RoleConverter()
				role = await role_converter.convert(ctx, options[1])

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

				if options[0].lower() == "add":
					if "target_roles" not in auto_mod["anti_flud"]:
						auto_mod["anti_flud"].update({"target_roles": [role.id]})
					else:
						auto_mod["anti_flud"]["target_roles"].append(role.id)
				elif options[0].lower() == "delete":
					if "target_roles" not in auto_mod["anti_flud"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список ролей пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						try:
							auto_mod["anti_flud"]["target_roles"].remove(role.id)
						except ValueError:
							emb = await self.client.utils.create_error_embed(
								ctx, "**В списке ролей нету указаной роли!**",
							)
							await ctx.send(embed=emb)
							return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: add, delete!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "ignore-role":
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите значения для настройки!"
					)
					await ctx.send(embed=emb)
					return

				role_converter = commands.RoleConverter()
				role = await role_converter.convert(ctx, options[1])

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

				if options[0].lower() == "add":
					if "ignore_roles" not in auto_mod["anti_flud"]:
						auto_mod["anti_flud"].update({"ignore_roles": [role.id]})
					else:
						auto_mod["anti_flud"]["ignore_roles"].append(role.id)
				elif options[0].lower() == "delete":
					if "ignore_roles" not in auto_mod["anti_flud"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список ролей пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						try:
							auto_mod["anti_flud"]["ignore_roles"].remove(role.id)
						except ValueError:
							emb = await self.client.utils.create_error_embed(
								ctx, "**В списке ролей нету указаной роли!**",
							)
							await ctx.send(embed=emb)
							return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: add, delete!**",
					)
					await ctx.send(embed=emb)
					return
		else:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите одно из этих действий: on, off, setting!**",
			)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			auto_mod=json.dumps(auto_mod)
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@setting.command(
		name="anti-invite",
		description="**Настройка анти-приглашения**",
		usage="setting anti-invite [on/off/setting] |Настройка| |Опции...|",
	)
	@commands.has_permissions(administrator=True)
	async def anti_invite(self, ctx, action: str, setting: str = None, *options):
		ons = ("on", "вкл", "включить", "+", "1")
		offs = ("off", "выкл", "выключить", "-", "0")
		auto_mod = (await self.client.database.sel_guild(guild=ctx.guild))["auto_mod"]
		options = list(options)
		if action.lower() in ons:
			if auto_mod["anti_invite"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Анти-приглашения уже включено!"
				)
				await ctx.send(embed=emb)
				return

			auto_mod["anti_invite"]["state"] = True

		elif action.lower() in offs:
			if not auto_mod["anti_invite"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Анти-приглашения и так выключено!"
				)
				await ctx.send(embed=emb)
				return

			auto_mod["anti_invite"] = {"state": False}

		elif action.lower() == "setting":
			settings = (
				"delete-message",
				"message",
				"punishment",
				"target-channel",
				"ignore-channel",
				"target-role",
				"ignore-role"
			)
			punishments = ("mute", "ban", "soft-ban", "warn", "kick")
			if setting is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите изменяемую настройку!"
				)
				await ctx.send(embed=emb)
				return

			if setting.lower() not in settings:
				emb = await self.client.utils.create_error_embed(
					ctx,
					"Укажите одну из этих настроек: delete-message, message, punishment, target-channel, ignore-channel, target-role, ignore-role!"
				)
				await ctx.send(embed=emb)
				return

			if not auto_mod["anti_invite"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Сначала включите анти-приглашения!"
				)
				await ctx.send(embed=emb)
				return

			if len(options) < 1:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите значения для настройки!"
				)
				await ctx.send(embed=emb)
				return

			if setting.lower() == "message":
				types = ("channel", "dm")
				if options[0] == "off":
					if "message" not in auto_mod["anti_invite"].keys():
						emb = await self.client.utils.create_error_embed(
							ctx, "**Сообщения не настроено!**",
						)
						await ctx.send(embed=emb)
						return

					auto_mod["anti_invite"].pop("message")
				elif options[0] in types:
					if len(options) < 2:
						emb = await self.client.utils.create_error_embed(
							ctx, "Укажите значения для настройки!"
						)
						await ctx.send(embed=emb)
						return

					auto_mod["anti_invite"].update({"message": {"type": options[0]}})
					options = list(options)
					options.pop(0)
					auto_mod["anti_invite"]["message"].update({"text": " ".join(options)})
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите один из этих типов: dm, channel!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "punishment":
				if options[0].lower() not in punishments:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих наказаний: mute, ban, soft-ban, warn, kick!**",
					)
					await ctx.send(embed=emb)
					return

				if len(options) < 2:
					options.append(None)

				auto_mod["anti_invite"].update({"punishment": {
					"type": options[0],
					"time": options[1]
				}})
			elif setting.lower() == "target-channel":
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите значения для настройки!"
					)
					await ctx.send(embed=emb)
					return

				channel_converter = commands.TextChannelConverter()
				channel = await channel_converter.convert(ctx, options[1])
				if options[0].lower() == "add":
					if "target_channels" not in auto_mod["anti_invite"]:
						auto_mod["anti_invite"].update({"target_channels": [channel.id]})
					else:
						auto_mod["anti_invite"]["target_channels"].append(channel.id)
				elif options[0].lower() == "delete":
					if "target_channels" not in auto_mod["anti_invite"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список каналов пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						try:
							auto_mod["anti_invite"]["target_channels"].remove(channel.id)
						except ValueError:
							emb = await self.client.utils.create_error_embed(
								ctx, "**В списке каналов нету указаного канала!**",
							)
							await ctx.send(embed=emb)
							return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: add, delete!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "ignore-channel":
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите значения для настройки!"
					)
					await ctx.send(embed=emb)
					return

				channel_converter = commands.TextChannelConverter()
				channel = await channel_converter.convert(ctx, options[1])
				if options[0].lower() == "add":
					if "ignore_channels" not in auto_mod["anti_invite"]:
						auto_mod["anti_invite"].update({"ignore_channels": [channel.id]})
					else:
						auto_mod["anti_invite"]["ignore_channels"].append(channel.id)
				elif options[0].lower() == "delete":
					if "ignore_channels" not in auto_mod["anti_invite"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список каналов пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						try:
							auto_mod["anti_invite"]["ignore_channels"].remove(channel.id)
						except ValueError:
							emb = await self.client.utils.create_error_embed(
								ctx, "**В списке каналов нету указаного канала!**",
							)
							await ctx.send(embed=emb)
							return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: add, delete!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "target-role":
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите значения для настройки!"
					)
					await ctx.send(embed=emb)
					return

				role_converter = commands.RoleConverter()
				role = await role_converter.convert(ctx, options[1])

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

				if options[0].lower() == "add":
					if "target_roles" not in auto_mod["anti_invite"]:
						auto_mod["anti_invite"].update({"target_roles": [role.id]})
					else:
						auto_mod["anti_invite"]["target_roles"].append(role.id)
				elif options[0].lower() == "delete":
					if "target_roles" not in auto_mod["anti_invite"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список ролей пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						try:
							auto_mod["anti_invite"]["target_roles"].remove(role.id)
						except ValueError:
							emb = await self.client.utils.create_error_embed(
								ctx, "**В списке ролей нету указаной роли!**",
							)
							await ctx.send(embed=emb)
							return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: add, delete!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "ignore-role":
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите значения для настройки!"
					)
					await ctx.send(embed=emb)
					return

				role_converter = commands.RoleConverter()
				role = await role_converter.convert(ctx, options[1])

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

				if options[0].lower() == "add":
					if "ignore_roles" not in auto_mod["anti_invite"]:
						auto_mod["anti_invite"].update({"ignore_roles": [role.id]})
					else:
						auto_mod["anti_invite"]["ignore_roles"].append(role.id)
				elif options[0].lower() == "delete":
					if "ignore_roles" not in auto_mod["anti_invite"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список ролей пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						try:
							auto_mod["anti_invite"]["ignore_roles"].remove(role.id)
						except ValueError:
							emb = await self.client.utils.create_error_embed(
								ctx, "**В списке ролей нету указаной роли!**",
							)
							await ctx.send(embed=emb)
							return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: add, delete!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "delete-message":
				if options[0].lower() == "on":
					if "delete_message" in auto_mod["anti_invite"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "Удаления сообщения уже включено"
						)
						await ctx.send(embed=emb)
						return
					else:
						auto_mod["anti_invite"].update({"delete_message": True})
				elif options[0].lower() == "off":
					if "delete_message" not in auto_mod["anti_invite"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "Удаления сообщения уже выключено"
						)
						await ctx.send(embed=emb)
						return
					else:
						auto_mod["anti_invite"].pop("delete_message")
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: on, off!**",
					)
					await ctx.send(embed=emb)
					return
		else:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите одно из этих действий: on, off, setting!**",
			)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			auto_mod=json.dumps(auto_mod)
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@setting.command(
		name="react-commands",
		description="**Настройка команд по реакциям**",
		usage="setting react-commands [on/off]",
	)
	@commands.has_permissions(administrator=True)
	async def react_commands(self, ctx, action: str):
		actions = ["on", "off", "true", "false", "0", "1"]
		if action.lower() not in actions:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не правильно указали действие! Укажите из этих вариантов: on, off!"
			)
			await ctx.send(embed=emb)
			return

		data = await self.client.database.sel_guild(guild=ctx.guild)
		emb = discord.Embed(
			description=f"**Настройки команд по реакциям успешно обновленны!**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
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

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			auto_mod=json.dumps(settings)
		)

	@setting.command(
		name="time-delete-channel",
		description="**Через сколько минут будет удалять приватный текстовый канал**",
		usage="setting time-delete-channel [Любое число]",
	)
	@commands.has_permissions(administrator=True)
	async def timetextchannel(self, ctx, time: int):
		if time <= 0:
			emb = await self.client.create_error_embed(ctx, "Укажите время удаления приватных текстовых каналов больше 0!")
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			timedelete_textchannel=time
		)

		emb = discord.Embed(
			description=f"**Вы успешно изменили значения! Новая длительность на удаления приватного текстового - {time}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@setting.command(
		name="exp-multi",
		aliases=["exp-multiplier"],
		description="**Настройка множителя опыта на сервере**",
		usage="setting exp-multi [Множитель%(Пример - 450%)]",
	)
	@commands.has_permissions(administrator=True)
	async def expform(self, ctx, multiplier: str):
		if not multiplier.endswith("%"):
			emb = await self.client.utils.create_error_embed(ctx, "Указан неправильный формат множителя!")
			await ctx.send(embed=emb)
			return

		raw_multi = multiplier[:-1]
		if not raw_multi.isdigit():
			emb = await self.client.utils.create_error_embed(ctx, "Указан неправильный формат множителя!")
			await ctx.send(embed=emb)
			return

		multi = int(raw_multi)
		if multi > 10000 or multi <= 0:
			emb = await self.client.utils.create_error_embed(
				ctx, "Укажите множитель опыта в диапазоне от 1% до 10000%!"
			)
			await ctx.send(embed=emb)
			return

		form = float(multi / 100)
		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			exp_multi=form
		)

		emb = discord.Embed(
			description=f"**Вы успешно настроили множитель опыта, {multiplier}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@setting.command(
		name="set-audit",
		aliases=["setaudit", "audit"],
		description="**Настройка канала аудита**",
		usage="setting logs [on/off] [Категория] |Канал|",
	)
	@commands.has_permissions(administrator=True)
	async def set_audit(self, ctx, action: str, category: str, channel: discord.TextChannel = None):
		ons = ("on", "вкл", "включить", "+", "1")
		offs = ("off", "выкл", "выключить", "-", "0")
		categories = {
			"модерация": "moderate",
			"экономика": "economy",
			"кланы": "clans",
			"учасник_обновился": "member_update",
			"участник_разбанен": "member_unban",
			"участник_забанен": "member_ban",
			"сообщения_изменено": "message_edit",
			"сообщения_удалено": "message_delete"
		}
		base_categories = (
			"moderate",
			"economy",
			"clans",
			"member_update",
			"member_ban",
			"member_unban",
			"message_edit",
			"message_delete"
		)
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]
		if action.lower() in ons:
			if channel is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите канал!**",
				)
				await ctx.send(embed=emb)
				return

			if category.lower() in base_categories:
				audit.update({category.lower(): channel.id})
			else:
				if category.lower() in categories.keys():
					audit.update({categories[category.lower()]: channel.id})
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Указаной категории не существует!**",
					)
					await ctx.send(embed=emb)
					return
		elif action.lower() in offs:
			if category.lower() in base_categories:
				if category.lower() not in audit.keys():
					emb = await self.client.utils.create_error_embed(
						ctx, "**Указаная категория ещё не настроена!**",
					)
					await ctx.send(embed=emb)
					return

				audit.pop(category.lower())
			else:
				if category.lower() in categories.keys():
					if categories[category.lower()] not in audit.keys():
						emb = await self.client.utils.create_error_embed(
							ctx, "**Указаная категория ещё не настроена!**",
						)
						await ctx.send(embed=emb)
						return

					audit.pop(categories[category.lower()])
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Указаной категории не существует!**",
					)
					await ctx.send(embed=emb)
					return
		else:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите одно из этих действий: on, off!**",
			)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			audit=json.dumps(audit)
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@setting.command(
		name="auto-reactions",
		aliases=["autoreactions"],
		description="**Настройка авто-реакций**",
		usage="setting auto-reactions [set/off] |Канал| |Эмодзи|",
	)
	@commands.has_permissions(administrator=True)
	async def auto_reactions(self, ctx, action: str, channel: typing.Optional[discord.TextChannel], *, reactions: str = None):
		auto_reactions = (await self.client.database.sel_guild(guild=ctx.guild))["auto_reactions"]
		if action.lower() == "set":
			if reactions is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите эмодзи!"
				)
				await ctx.send(embed=emb)
				return

			if channel is None:
				channel = ctx.channel

			emojis = [emoji for emoji in reactions.split(" ") if emoji]
			auto_reactions.update({channel.id: emojis})
			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				auto_reactions=json.dumps(auto_reactions)
			)
			try:
				await ctx.message.add_reaction("✅")
			except discord.errors.Forbidden:
				pass
			except discord.errors.HTTPException:
				pass
			return
		elif action.lower() == "off":
			if channel is None:
				channel = ctx.channel

			try:
				auto_reactions.pop(str(channel.id))
			except KeyError:
				emb = await self.client.utils.create_error_embed(
					ctx, "Для указаного канала авто-реакции не настроены!"
				)
				await ctx.send(embed=emb)
				return

			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				auto_reactions=json.dumps(auto_reactions)
			)
			try:
				await ctx.message.add_reaction("✅")
			except discord.errors.Forbidden:
				pass
			except discord.errors.HTTPException:
				pass
			return
		else:
			emb = await self.client.utils.create_error_embed(
				ctx, "Укажите одно из этих действий: set, off"
			)
			await ctx.send(embed=emb)

	@setting.command(
		name="custom-command",
		aliases=["customcommand", "custom-commands", "customcommands"],
		description="**Настройка кастомных команд**",
		usage="setting custom-command [add/edit/delete/show] [Названия команды] |Опции|",
	)
	@commands.has_permissions(administrator=True)
	async def custom_command(self, ctx, action: str, command_name: str = None, *options):
		custom_commands = (await self.client.database.sel_guild(guild=ctx.guild))["custom_commands"]
		if action.lower() == "add":
			if command_name is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите названия команды!"
				)
				await ctx.send(embed=emb)
				return

			if command_name in self.commands:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаное названия команды уже есть в командах бота!"
				)
				await ctx.send(embed=emb)
				return

			if len(command_name) > 30:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаное названия слишком большое(Максимум 30 символов)!"
				)
				await ctx.send(embed=emb)
				return

			if self.find_custom_command(command_name, custom_commands) is not None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаная команда уже есть в списке команд!"
				)
				await ctx.send(embed=emb)
				return

			if len(options) < 1:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите код к команде!"
				)
				await ctx.send(embed=emb)
				return

			if len(custom_commands) > 20:
				emb = await self.client.utils.create_error_embed(
					ctx, "Вы достигли ограничения(20 команд)!"
				)
				await ctx.send(embed=emb)
				return

			if len(" ".join(options)) > 1000:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаный код слишком большой(Максимум 1000 символов)!"
				)
				await ctx.send(embed=emb)
				return

			custom_commands.append({"name": command_name, "code": " ".join(options)})
			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				custom_commands=json.dumps(custom_commands)
			)

			emb = discord.Embed(
				description=f"**Успешно создана новая команда - `{command_name}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif action.lower() == "show":
			if command_name is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите названия команды!"
				)
				await ctx.send(embed=emb)
				return

			command = self.find_custom_command(command_name, custom_commands)
			if command is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаной команды не существует!"
				)
				await ctx.send(embed=emb)
				return

			emb = discord.Embed(
				title=f"Информация о кастомной команде - `{command_name}`",
				description=f"Код команды:\n```{command['code']}```",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif action.lower() == "delete":
			if command_name is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите названия команды!"
				)
				await ctx.send(embed=emb)
				return

			command = self.find_custom_command(command_name, custom_commands)
			if command is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаной команды не существует!"
				)
				await ctx.send(embed=emb)
				return

			custom_commands.remove(command)
			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				custom_commands=json.dumps(custom_commands)
			)

			emb = discord.Embed(
				description=f"**Команда - `{command_name}` успешно удаленна**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif action.lower() == "edit":
			if command_name is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите названия команды!"
				)
				await ctx.send(embed=emb)
				return

			command = self.find_custom_command(command_name, custom_commands)
			if command is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаной команды не существует!"
				)
				await ctx.send(embed=emb)
				return

			options = list(options)
			if len(options) < 2:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите значения к настройке!"
				)
				await ctx.send(embed=emb)
				return

			fields = ("description", "code", "function")
			if options[0].lower() not in fields:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите один из этих параметров: description, code, function!"
				)
				await ctx.send(embed=emb)
				return

			if options[0].lower() == "code":
				options.pop(0)
				if len(" ".join(options)) > 1000:
					emb = await self.client.utils.create_error_embed(
						ctx, "Указаный код слишком большой(Максимум 1000 символов)!"
					)
					await ctx.send(embed=emb)
					return

				if " ".join(options) == command["code"]:
					emb = await self.client.utils.create_error_embed(
						ctx, "Вы должны указать код отличающийся от старого!"
					)
					await ctx.send(embed=emb)
					return

				command.update({"code": " ".join(options)})
				custom_commands[custom_commands.index(command)] = command
			elif options[0].lower() == "description":
				options.pop(0)
				if len(" ".join(options)) > 50:
					emb = await self.client.utils.create_error_embed(
						ctx, "Указаное описания слишком большое(Максимум 50 символов)!"
					)
					await ctx.send(embed=emb)
					return

				if "description" in command.keys():
					if " ".join(options) == command["description"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "Вы должны указать описания отличающийся от старого!"
						)
						await ctx.send(embed=emb)
						return

				command.update({"description": " ".join(options)})
				custom_commands[custom_commands.index(command)] = command
			elif options[0].lower() == "function":
				options.pop(0)
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите настройки!"
					)
					await ctx.send(embed=emb)
					return

				functions = ("role-add", "role-remove")
				converter = commands.RoleConverter()

				if options[1].lower() not in functions:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите одну из этих функций: role-add, role-remove!"
					)
					await ctx.send(embed=emb)
					return

				if options[0].lower() == "add":
					if len(options) < 3:
						emb = await self.client.utils.create_error_embed(
							ctx, "Укажите настройки!"
						)
						await ctx.send(embed=emb)
						return

					role = await converter.convert(ctx, options[2])
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

					if options[1].lower() == "role-add":
						if "functions" not in command.keys():
							command.update({"functions": {
								"role_add": role.id
							}})
						else:
							command["functions"].update({"role_add": role.id})
					elif options[1].lower() == "role-remove":
						if "functions" not in command.keys():
							command.update({"functions": {
								"role_remove": role.id
							}})
						else:
							command["functions"].update({"role_remove": role.id})

					custom_commands[custom_commands.index(command)] = command
				elif options[0].lower() == "off":
					if "functions" not in command.keys():
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список функций пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						if options[1].lower() == "role-add":
							command["functions"].pop("role_add")
						elif options[1].lower() == "role-remove":
							command["functions"].pop("role_remove")

					custom_commands[custom_commands.index(command)] = command
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий для edit function: add, off!**",
					)
					await ctx.send(embed=emb)
					return

			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				custom_commands=json.dumps(custom_commands)
			)

			emb = discord.Embed(
				description=f"**Команда - `{command_name}` успешно изменена**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		else:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите одно из этих действий: add, delete, edit, show!**",
			)
			await ctx.send(embed=emb)

	@setting.command(
		name="auto-responder",
		aliases=["autoresponder", "auto-responders", "autoresponders"],
		description="**Настройка авто-ответчиков**",
		usage="setting auto-responder [add/edit/delete/show/list] [Названия авто-ответчика] |Текст авто-ответчика|",
	)
	@commands.has_permissions(administrator=True)
	async def auto_responder(self, ctx, action: str, responder_name: str = None, *, text: str = None):
		auto_responders = (await self.client.database.sel_guild(guild=ctx.guild))["autoresponders"]
		if action.lower() == "add":
			if responder_name is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите названия авто-ответчика!"
				)
				await ctx.send(embed=emb)
				return

			if responder_name in auto_responders.keys():
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаный авто-ответчик уже есть в списке авто-ответчиков!"
				)
				await ctx.send(embed=emb)
				return

			if text is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите текст к авто-ответчику!"
				)
				await ctx.send(embed=emb)
				return

			if len(auto_responders.keys()) > 15:
				emb = await self.client.utils.create_error_embed(
					ctx, "Вы достигли ограничения(15 авто-ответчиков)!"
				)
				await ctx.send(embed=emb)
				return

			if len(text) > 1500:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаный текст слишком большой(Максимум 1500 символов)!"
				)
				await ctx.send(embed=emb)
				return

			auto_responders.update({responder_name: text})
			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				autoresponders=json.dumps(auto_responders)
			)

			emb = discord.Embed(
				description=f"**Успешно создан новый авто-ответчик - `{responder_name}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif action.lower() == "show":
			if responder_name is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите названия авто-ответчика!"
				)
				await ctx.send(embed=emb)
				return

			if responder_name not in auto_responders.keys():
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаного авто-ответчика не существует!"
				)
				await ctx.send(embed=emb)
				return

			emb = discord.Embed(
				title=f"Информация о авто-ответчике - `{responder_name}`",
				description=f"Текст авто-ответчика:\n```{auto_responders[responder_name]}```",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif action.lower() == "delete":
			if responder_name is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите названия авто-ответчика!"
				)
				await ctx.send(embed=emb)
				return

			if responder_name not in auto_responders.keys():
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаного авто-ответчика не существует!"
				)
				await ctx.send(embed=emb)
				return

			auto_responders.pop(responder_name)
			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				autoresponders=json.dumps(auto_responders)
			)

			emb = discord.Embed(
				description=f"**Авто-ответчик - `{responder_name}` успешно удален**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif action.lower() == "edit":
			if responder_name is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите названия авто-ответчика!"
				)
				await ctx.send(embed=emb)
				return

			if responder_name not in auto_responders.keys():
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаного авто-ответчика не существует!"
				)
				await ctx.send(embed=emb)
				return

			if text is None:
				emb = await self.client.utils.create_error_embed(
					ctx,  "Укажите текст к авто-ответчику!"
				)
				await ctx.send(embed=emb)
				return

			if len(text) > 1500:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаный текст слишком большой(Максимум 1500 символов)!"
				)
				await ctx.send(embed=emb)
				return

			if text == auto_responders[responder_name]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Вы должны указать новый текст отличающийся от старого!"
				)
				await ctx.send(embed=emb)
				return

			auto_responders.update({responder_name: text})
			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				autoresponders=json.dumps(auto_responders)
			)

			emb = discord.Embed(
				description=f"**Текст к авто-ответчику - `{responder_name}` успешно измененен**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

		elif action.lower() == "list":
			commands = ("\n".join([f"`{command}`" for command in auto_responders.keys()])
						if auto_responders != {} else "На сервере ещё нет авто-ответчиков")
			emb = discord.Embed(
				title="Авто-ответчики сервера",
				description=commands,
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		else:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите одно из этих действий: add, delete, edit, show, list!**",
			)
			await ctx.send(embed=emb)

	@setting.command(
		name="level-up-message",
		aliases=["levelupmessage", "set-level-up-message", "setlevelupmessage"],
		description="**Настройка авто-ответчиков**",
		usage="setting level-up-message [channel/dm/off] |Текст|",
	)
	@commands.has_permissions(administrator=True)
	async def level_up_message(self, ctx, type: str, *, text = None):
		rank_message = (await self.client.database.sel_guild(guild=ctx.guild))["rank_message"]
		if type.lower() == "dm":
			if text is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите текст!**",
				)
				await ctx.send(embed=emb)
				return

			rank_message.update({
				"state": True,
				"type": "dm",
				"text": text
			})
		elif type.lower() == "channel":
			if text is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите текст!**",
				)
				await ctx.send(embed=emb)
				return

			rank_message.update({
				"state": True,
				"type": "channel",
				"text": text
			})
		elif type.lower() == "off":
			if "text" not in rank_message.keys():
				emb = await self.client.utils.create_error_embed(
					ctx, "**Текст ещё не настроен!**",
				)
				await ctx.send(embed=emb)
				return

			rank_message = {"state": False}
		else:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите одно из этих действий: off, dm, channel!**",
			)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			rank_message=json.dumps(rank_message)
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@setting.command(
		name="anti-caps",
		description="**Настройка анти-капса**",
		usage="setting anti-caps [on/off/setting] |Настройка| |Опции...|",
	)
	@commands.has_permissions(administrator=True)
	async def anti_caps(self, ctx, action: str, setting: str = None, *options):
		ons = ("on", "вкл", "включить", "+", "1")
		offs = ("off", "выкл", "выключить", "-", "0")
		auto_mod = (await self.client.database.sel_guild(guild=ctx.guild))["auto_mod"]
		options = list(options)
		if action.lower() in ons:
			if auto_mod["anti_caps"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Анти-капс уже включен!"
				)
				await ctx.send(embed=emb)
				return

			if setting is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите процент символов в верхнем регистре"
				)
				await ctx.send(embed=emb)
				return

			if not setting.isdigit():
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаные проценты строка! Укажите число!"
				)
				await ctx.send(embed=emb)
				return

			if int(setting) > 100:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаный процент слишком большой! Укажите меньше 100%!"
				)
				await ctx.send(embed=emb)
				return

			if int(setting) <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаный процент слишком маленький! Укажите больше 0%!"
				)
				await ctx.send(embed=emb)
				return

			auto_mod["anti_caps"]["state"] = True
			auto_mod["anti_caps"]["percent"] = int(setting)

		elif action.lower() in offs:
			if not auto_mod["anti_caps"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Анти-капс и так выключен!"
				)
				await ctx.send(embed=emb)
				return

			auto_mod["anti_caps"] = {"state": False}

		elif action.lower() == "setting":
			settings = (
				"delete-message",
				"message",
				"punishment",
				"target-channel",
				"ignore-channel",
				"target-role",
				"ignore-role",
			)
			punishments = ("mute", "ban", "soft-ban", "warn", "kick")
			if setting is None:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите изменяемую настройку!"
				)
				await ctx.send(embed=emb)
				return

			if setting.lower() not in settings:
				emb = await self.client.utils.create_error_embed(
					ctx,
					"Укажите одну из этих настроек: delete-message, message, punishment, target-channel, ignore-channel, target-role, ignore-role!"
				)
				await ctx.send(embed=emb)
				return

			if not auto_mod["anti_caps"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Сначала включите анти-капс!"
				)
				await ctx.send(embed=emb)
				return

			if len(options) < 1:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите значения для настройки!"
				)
				await ctx.send(embed=emb)
				return

			if setting.lower() == "message":
				types = ("channel", "dm")
				if options[0] == "off":
					if "message" not in auto_mod["anti_caps"].keys():
						emb = await self.client.utils.create_error_embed(
							ctx, "**Сообщения не настроено!**",
						)
						await ctx.send(embed=emb)
						return

					auto_mod["anti_caps"].pop("message")
				elif options[0] in types:
					if len(options) < 2:
						emb = await self.client.utils.create_error_embed(
							ctx, "Укажите значения для настройки!"
						)
						await ctx.send(embed=emb)
						return

					auto_mod["anti_caps"].update({"message": {"type": options[0]}})
					options = list(options)
					options.pop(0)
					auto_mod["anti_caps"]["message"].update({"text": " ".join(options)})
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите один из этих типов: dm, channel!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "punishment":
				if options[0].lower() not in punishments:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих наказаний: mute, ban, soft-ban, warn, kick!**",
					)
					await ctx.send(embed=emb)
					return

				if len(options) < 2:
					options.append(None)

				auto_mod["anti_caps"].update({"punishment": {
					"type": options[0],
					"time": options[1]
				}})
			elif setting.lower() == "target-channel":
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите значения для настройки!"
					)
					await ctx.send(embed=emb)
					return

				channel_converter = commands.TextChannelConverter()
				channel = await channel_converter.convert(ctx, options[1])
				if options[0].lower() == "add":
					if "target_channels" not in auto_mod["anti_caps"]:
						auto_mod["anti_caps"].update({"target_channels": [channel.id]})
					else:
						auto_mod["anti_caps"]["target_channels"].append(channel.id)
				elif options[0].lower() == "delete":
					if "target_channels" not in auto_mod["anti_caps"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список каналов пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						try:
							auto_mod["anti_caps"]["target_channels"].remove(channel.id)
						except ValueError:
							emb = await self.client.utils.create_error_embed(
								ctx, "**В списке каналов нету указаного канала!**",
							)
							await ctx.send(embed=emb)
							return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: add, delete!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "ignore-channel":
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите значения для настройки!"
					)
					await ctx.send(embed=emb)
					return

				channel_converter = commands.TextChannelConverter()
				channel = await channel_converter.convert(ctx, options[1])
				if options[0].lower() == "add":
					if "ignore_channels" not in auto_mod["anti_caps"]:
						auto_mod["anti_caps"].update({"ignore_channels": [channel.id]})
					else:
						auto_mod["anti_caps"]["ignore_channels"].append(channel.id)
				elif options[0].lower() == "delete":
					if "ignore_channels" not in auto_mod["anti_caps"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список каналов пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						try:
							auto_mod["anti_caps"]["ignore_channels"].remove(channel.id)
						except ValueError:
							emb = await self.client.utils.create_error_embed(
								ctx, "**В списке каналов нету указаного канала!**",
							)
							await ctx.send(embed=emb)
							return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: add, delete!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "target-role":
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите значения для настройки!"
					)
					await ctx.send(embed=emb)
					return

				role_converter = commands.RoleConverter()
				role = await role_converter.convert(ctx, options[1])

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

				if options[0].lower() == "add":
					if "target_roles" not in auto_mod["anti_caps"]:
						auto_mod["anti_caps"].update({"target_roles": [role.id]})
					else:
						auto_mod["anti_caps"]["target_roles"].append(role.id)
				elif options[0].lower() == "delete":
					if "target_roles" not in auto_mod["anti_caps"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список ролей пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						try:
							auto_mod["anti_caps"]["target_roles"].remove(role.id)
						except ValueError:
							emb = await self.client.utils.create_error_embed(
								ctx, "**В списке ролей нету указаной роли!**",
							)
							await ctx.send(embed=emb)
							return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: add, delete!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "ignore-role":
				if len(options) < 2:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите значения для настройки!"
					)
					await ctx.send(embed=emb)
					return

				role_converter = commands.RoleConverter()
				role = await role_converter.convert(ctx, options[1])

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

				if options[0].lower() == "add":
					if "ignore_roles" not in auto_mod["anti_caps"]:
						auto_mod["anti_caps"].update({"ignore_roles": [role.id]})
					else:
						auto_mod["anti_caps"]["ignore_roles"].append(role.id)
				elif options[0].lower() == "delete":
					if "ignore_roles" not in auto_mod["anti_caps"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "**Список ролей пуст!**",
						)
						await ctx.send(embed=emb)
						return
					else:
						try:
							auto_mod["anti_caps"]["ignore_roles"].remove(role.id)
						except ValueError:
							emb = await self.client.utils.create_error_embed(
								ctx, "**В списке ролей нету указаной роли!**",
							)
							await ctx.send(embed=emb)
							return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: add, delete!**",
					)
					await ctx.send(embed=emb)
					return
			elif setting.lower() == "delete-message":
				if options[0].lower() == "on":
					if "delete_message" in auto_mod["anti_caps"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "Удаления сообщения уже включено"
						)
						await ctx.send(embed=emb)
						return
					else:
						auto_mod["anti_caps"].update({"delete_message": True})
				elif options[0].lower() == "off":
					if "delete_message" not in auto_mod["anti_caps"]:
						emb = await self.client.utils.create_error_embed(
							ctx, "Удаления сообщения уже выключено"
						)
						await ctx.send(embed=emb)
						return
					else:
						auto_mod["anti_caps"].pop("delete_message")
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Укажите одно из этих действий: on, off!**",
					)
					await ctx.send(embed=emb)
					return
		else:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите одно из этих действий: on, off, setting!**",
			)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			auto_mod=json.dumps(auto_mod)
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@setting.command(
		description="**Настройка каптчи при входе участника**",
		usage="setting captcha [on/off]",
	)
	@commands.has_permissions(administrator=True)
	async def captcha(self, ctx, action: str):
		auto_mod = (await self.client.database.sel_guild(guild=ctx.guild))["auto_mod"]
		if action.lower() == "on":
			if auto_mod["captcha"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Каптча уже включена!"
				)
				await ctx.send(embed=emb)
				return

			auto_mod["captcha"]["state"] = True
		elif action.lower() == "off":
			if not auto_mod["captcha"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Каптча уже выключена!"
				)
				await ctx.send(embed=emb)
				return

			auto_mod["captcha"]["state"] = False
		else:
			emb = await self.client.utils.create_error_embed(
				ctx, "Укажите одно из этих действий: on, off"
			)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			auto_mod=json.dumps(auto_mod)
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@setting.command(
		description="**Настройка команд**",
		usage="setting command [Названия команды] [Настройка] |Опции|",
	)
	@commands.has_permissions(administrator=True)
	async def command(self, ctx, command_name: str, setting: str, *options):
		commands_settings = (await self.client.database.sel_guild(guild=ctx.guild))["commands_settings"]
		command_name = command_name.lower()
		if command_name in ("help", "setting"):
			emb = await self.client.utils.create_error_embed(
				ctx, "Нельзя управлять указаной командой!"
			)
			await ctx.send(embed=emb)
			return

		if command_name not in self.commands:
			emb = await self.client.utils.create_error_embed(
				ctx, "Такой команды не существует!"
			)
			await ctx.send(embed=emb)
			return

		if setting.lower() not in (
				"on", "off", "ignore-channel", "ignore-role", "target-role", "target-channel"
		):
			emb = await self.client.utils.create_error_embed(
				ctx, "Укажите одно из этих действий: on, off, ignore-channel, ignore-role, target-role, target-channel"
			)
			await ctx.send(embed=emb)
			return

		if setting.lower() not in ("off", "on") and len(options) < 2:
			emb = await self.client.utils.create_error_embed(
				ctx, "Укажите значения!"
			)
			await ctx.send(embed=emb)
			return

		if command_name not in commands_settings.keys():
			commands_settings.update(
				{
					command_name: {
						"state": True,
						"ignore_channels": [],
						"ignore_roles": [],
						"target_roles": [],
						"target_channels": []
					}
				})

		if setting.lower() == "on":
			if commands_settings[command_name]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаная команда уже включена!"
				)
				await ctx.send(embed=emb)
				return

			commands_settings[command_name]["state"] = True
		elif setting.lower() == "off":
			if not commands_settings[command_name]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Указаная команда уже выключена!"
				)
				await ctx.send(embed=emb)
				return

			commands_settings[command_name]["state"] = False
		elif setting.lower() == "target-channel":
			channel_converter = commands.TextChannelConverter()
			channel = await channel_converter.convert(ctx, options[1])
			if options[0].lower() == "add":
				commands_settings[command_name]["target_channels"].append(channel.id)
			elif options[0].lower() == "delete":
				try:
					commands_settings[command_name]["target_channels"].remove(channel.id)
				except ValueError:
					emb = await self.client.utils.create_error_embed(
						ctx, "**В списке каналов нету указаного канала!**",
					)
					await ctx.send(embed=emb)
					return
			else:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите одно из этих действий: add, delete!**",
				)
				await ctx.send(embed=emb)
				return
		elif setting.lower() == "ignore-channel":
			channel_converter = commands.TextChannelConverter()
			channel = await channel_converter.convert(ctx, options[1])
			if options[0].lower() == "add":
				commands_settings[command_name]["ignore_channels"].append(channel.id)
			elif options[0].lower() == "delete":
				try:
					commands_settings[command_name]["ignore_channels"].remove(channel.id)
				except ValueError:
					emb = await self.client.utils.create_error_embed(
						ctx, "**В списке каналов нету указаного канала!**",
					)
					await ctx.send(embed=emb)
					return
			else:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите одно из этих действий: add, delete!**",
				)
				await ctx.send(embed=emb)
				return
		elif setting.lower() == "target-role":
			role_converter = commands.RoleConverter()
			role = await role_converter.convert(ctx, options[1])

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

			if options[0].lower() == "add":
				commands_settings[command_name]["target_roles"].append(role.id)
			elif options[0].lower() == "delete":
				try:
					commands_settings[command_name]["target_roles"].remove(role.id)
				except ValueError:
					emb = await self.client.utils.create_error_embed(
						ctx, "**В списке ролей нету указаной роли!**",
					)
					await ctx.send(embed=emb)
					return
			else:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите одно из этих действий: add, delete!**",
				)
				await ctx.send(embed=emb)
				return
		elif setting.lower() == "ignore-role":
			role_converter = commands.RoleConverter()
			role = await role_converter.convert(ctx, options[1])

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

			if options[0].lower() == "add":
				commands_settings[command_name]["ignore_roles"].append(role.id)
			elif options[0].lower() == "delete":
				try:
					commands_settings[command_name]["ignore_roles"].remove(role.id)
				except ValueError:
					emb = await self.client.utils.create_error_embed(
						ctx, "**В списке ролей нету указаной роли!**",
					)
					await ctx.send(embed=emb)
					return
			else:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите одно из этих действий: add, delete!**",
				)
				await ctx.send(embed=emb)
				return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			commands_settings=json.dumps(commands_settings)
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass


def setup(client):
	client.add_cog(Settings(client))
