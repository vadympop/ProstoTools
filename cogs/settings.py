import discord
import typing

from core.bases.cog_base import BaseCog
from discord.ext import commands


class Settings(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.FILTERS = self.client.config.FILTERS
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
		usage="setting [Команда]",
		description="Категория команд - настройки",
		help=f"""**Команды групы:** anti-invite, level-up-message, time-delete-channel, shop-role, exp-multi, text-channels-category, set-audit, max-warns, prefix, anti-flud, react-commands, moderation-role, ignore-channels, custom-command, auto-reactions, auto-responder\n\n"""
	)
	@commands.guild_only()
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
		name="ignore-channels",
		description="Игнорируемые каналы в системе уровней",
		usage="setting ignore-channels [Действие, add - добавляет канал в исключения, clear - очищает список исключений, delete - удаляет указаный канал из списка] [Id канала]",
	)
	@commands.has_permissions(administrator=True)
	async def ignoredchannels(self, ctx, typech: str, channel: discord.TextChannel = None):
		data = await self.client.database.sel_guild(guild=ctx.guild)
		cur_ignchannel = data.ignored_channels

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
				emb = await self.client.utils.create_error_embed(
					ctx, "**Такого канала нету в списке игнорируемых каналов!**"
				)
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
			emb = await self.client.utils.create_error_embed(
				ctx, "**Вы не правильно указали действие!**"
			)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			ignored_channels=cur_ignchannel
		)

	@setting.command(
		name="shop-role",
		description="Настройка магазина на сервере",
		usage="setting shop-role [clear - очищает список ролей, add - добавляет роль, delete - удаляет роль] [@Роль] [Стоимость роли]",
	)
	@commands.has_permissions(administrator=True)
	async def shoplist(
		self, ctx, cl_add: typing.Optional[str], role: discord.Role, cost: int
	):
		data = await self.client.database.sel_guild(guild=ctx.guild)
		shoplist = data.shop_list

		if cost <= 0:
			emb = await self.client.utils.create_error_embed(ctx, "Укажите стоимость предмета больше 0!")
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
				emb = await self.client.utils.create_error_embed(
					ctx, "**Такой роли не существует в списке продаваемых ролей!**"
				)
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
			shop_list=shoplist
		)

	@setting.command(
		name="exp-multi",
		aliases=["exp-multiplier"],
		description="Настройка множителя опыта на сервере",
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
		name="auto-reactions",
		aliases=["autoreactions"],
		description="Настройка авто-реакций",
		usage="setting auto-reactions [set/off] |Канал| |Эмодзи|",
	)
	@commands.has_permissions(administrator=True)
	async def auto_reactions(self, ctx, action: str, channel: typing.Optional[discord.TextChannel], *reactions):
		auto_reactions = (await self.client.database.sel_guild(guild=ctx.guild)).auto_reactions
		if action.lower() not in ("set", "off", "setting-filters", "sf", "set-filters"):
			emb = await self.client.utils.create_error_embed(
				ctx, "Укажите одно из этих действий: set, off, settings-filters"
			)
			await ctx.send(embed=emb)

		if channel is None:
			channel = ctx.channel

		if action.lower() == "set":
			if len(reactions) <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите эмодзи!"
				)
				await ctx.send(embed=emb)
				return

			auto_reactions.update({
				channel.id: {
					"reactions": reactions,
					"filter_mode": "all",
					"filters": []
				}
			})
		elif action.lower() == "off":
			try:
				auto_reactions.pop(channel.id)
			except KeyError:
				emb = await self.client.utils.create_error_embed(
					ctx, "Для указанного канала авто-реакции не настроены!"
				)
				await ctx.send(embed=emb)
				return
		elif action.lower() in ("setting-filters", "sf", "set-filters"):
			if len(reactions) <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите настройку изменения!"
				)
				await ctx.send(embed=emb)
				return

			if reactions[0].lower() not in ("mode", "add", "remove"):
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите одну из этих настроек: mode, add, remove"
				)
				await ctx.send(embed=emb)
				return

			if reactions[0].lower() == "mode":
				if len(reactions) <= 1:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите режим фильтров!"
					)
					await ctx.send(embed=emb)
					return

				if reactions[1].lower() not in ("any", "all"):
					emb = await self.client.utils.create_error_embed(
						ctx, "Указан неправильный режим!"
					)
					await ctx.send(embed=emb)
					return

				try:
					auto_reactions[channel.id]["filter_mode"] = reactions[1].lower()
				except KeyError:
					emb = await self.client.utils.create_error_embed(
						ctx, "Авто-реакции для указанного канала нету"
					)
					await ctx.send(embed=emb)
					return
			elif reactions[0].lower() == "add":
				if len(reactions) <= 1:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите фильтр!"
					)
					await ctx.send(embed=emb)
					return

				if reactions[1].lower() not in self.FILTERS:
					emb = await self.client.utils.create_error_embed(
						ctx, "Указан неправильный фильтр!"
					)
					await ctx.send(embed=emb)
					return

				try:
					auto_reactions[channel.id]["filters"].append(reactions[1].lower())
				except KeyError:
					emb = await self.client.utils.create_error_embed(
						ctx, "Авто-реакции для указанного канала нету"
					)
					await ctx.send(embed=emb)
					return
			elif reactions[0].lower() == "remove":
				if len(reactions) <= 1:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите фильтр!"
					)
					await ctx.send(embed=emb)
					return

				if reactions[1].lower() not in self.FILTERS:
					emb = await self.client.utils.create_error_embed(
						ctx, "Указан неправильный фильтр!"
					)
					await ctx.send(embed=emb)
					return

				try:
					auto_reactions[channel.id]["filters"].remove(reactions[1].lower())
				except KeyError:
					emb = await self.client.utils.create_error_embed(
						ctx, "Авто-реакции для указанного канала нету/В списке фильтров нету указанного"
					)
					await ctx.send(embed=emb)
					return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			auto_reactions=auto_reactions
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@setting.command(
		name="custom-command",
		aliases=["customcommand", "custom-commands", "customcommands"],
		description="Настройка кастомных команд",
		usage="setting custom-command [add/edit/delete/show] [Названия команды] |Опции|",
	)
	@commands.has_permissions(administrator=True)
	async def custom_command(self, ctx, action: str, command_name: str = None, *options):
		custom_commands = (await self.client.database.sel_guild(guild=ctx.guild)).custom_commands
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

			custom_commands.append({
				"name": command_name,
				"code": " ".join(options),
				"target_roles": [],
				"target_channels": [],
				"ignore_roles": [],
				"ignore_channels": []
			})
			await self.client.database.update(
				"guilds",
				where={"guild_id": ctx.guild.id},
				custom_commands=custom_commands
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
				custom_commands=custom_commands
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
				custom_commands=custom_commands
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
		description="Настройка авто-ответчиков",
		usage="setting auto-responder [add/edit/delete/show/list] [Названия авто-ответчика] |Текст авто-ответчика|",
	)
	@commands.has_permissions(administrator=True)
	async def auto_responder(self, ctx, action: str, responder_name: str = None, *, text: str = None):
		auto_responders = (await self.client.database.sel_guild(guild=ctx.guild)).autoresponders
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
				autoresponders=auto_responders
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
				autoresponders=auto_responders
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
				autoresponders=auto_responders
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
		description="Настройка авто-ответчиков",
		usage="setting level-up-message [channel/dm/off] |Текст|",
	)
	@commands.has_permissions(administrator=True)
	async def level_up_message(self, ctx, type: str, *, text: str = None):
		rank_message = (await self.client.database.sel_guild(guild=ctx.guild)).rank_message
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
			rank_message=rank_message
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@setting.command(
		description="Настройка команд",
		usage="setting command [Названия команды] [Настройка] |Опции|",
	)
	@commands.has_permissions(administrator=True)
	async def command(self, ctx, command_name: str, setting: str, *options):
		commands_settings = (await self.client.database.sel_guild(guild=ctx.guild)).commands_settings
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
			commands_settings=commands_settings
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@setting.command(
		description="Настройка системы приветствий",
		usage="setting welcomer [channel/dm/off] |Текст|",
	)
	@commands.has_permissions(administrator=True)
	async def welcomer(self, ctx, type: str, *options):
		welcomer_settings = (await self.client.database.sel_guild(guild=ctx.guild)).welcomer
		options = list(options)
		if type.lower() == "dm":
			if len(options) <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите текст!**",
				)
				await ctx.send(embed=emb)
				return

			welcomer_settings["join"].update({
				"state": True,
				"type": "dm",
				"text": " ".join(options)
			})
		elif type.lower() == "channel":
			if len(options) <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите канал!**",
				)
				await ctx.send(embed=emb)
				return

			channel_converter = commands.TextChannelConverter()
			channel = await channel_converter.convert(ctx, options.pop(0))
			if len(options) <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите текст!**",
				)
				await ctx.send(embed=emb)
				return

			welcomer_settings["join"].update({
				"state": True,
				"type": "channel",
				"channel": channel.id,
				"text": " ".join(options)
			})
		elif type.lower() == "off":
			if not welcomer_settings["join"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Система приветствий уже выключена!**",
				)
				await ctx.send(embed=emb)
				return

			welcomer_settings["join"].update({"state": False})
		else:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите одно из этих действий: off, dm, channel!**",
			)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			welcomer=welcomer_settings
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@setting.command(
		description="Настройка системы прощаний",
		usage="setting leaver [channel/dm/off] |Текст|",
	)
	@commands.has_permissions(administrator=True)
	async def leaver(self, ctx, type: str, *options):
		leaver_settings = (await self.client.database.sel_guild(guild=ctx.guild)).welcomer
		options = list(options)
		if type.lower() == "dm":
			if len(options) <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите текст!**",
				)
				await ctx.send(embed=emb)
				return

			leaver_settings["leave"].update({
				"state": True,
				"type": "dm",
				"text": " ".join(options)
			})
		elif type.lower() == "channel":
			if len(options) <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите канал!**",
				)
				await ctx.send(embed=emb)
				return

			channel_converter = commands.TextChannelConverter()
			channel = await channel_converter.convert(ctx, options.pop(0))
			if len(options) <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Укажите текст!**",
				)
				await ctx.send(embed=emb)
				return

			leaver_settings["leave"].update({
				"state": True,
				"type": "channel",
				"channel": channel.id,
				"text": " ".join(options)
			})
		elif type.lower() == "off":
			if not leaver_settings["leave"]["state"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Система прощаний уже выключена!**",
				)
				await ctx.send(embed=emb)
				return

			leaver_settings["leave"].update({"state": False})
		else:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите одно из этих действий: off, dm, channel!**",
			)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			welcomer=leaver_settings
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass


def setup(client):
	client.add_cog(Settings(client))
