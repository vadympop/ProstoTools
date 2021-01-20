import uuid
import json
import random
import discord

from datetime import datetime
from string import ascii_uppercase
from discord.ext import commands


class Clans(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT

	async def _add_member(self, ctx, clan_id: str, member: discord.Member):
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
		for clan in data:
			if clan["id"] == clan_id:
				if member.id not in clan["members"]:
					clan_id = clan["id"]
					clan["members"].append(member.id)
					await member.add_roles(ctx.guild.get_role(clan["role_id"]))
					break

		await self.client.database.update(
			"users",
			where={"user_id": member.id, "guild_id": ctx.guild.id},
			clan=clan_id
		)
		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			clans=json.dumps(data)
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@commands.group(
		help=f"""**Команды групы:** buy, members, accept-join-request, send-join-request, kick, reject-join-request, list-join-requests, list, use-invite, info, create, edit, leave, create-invite, trans-owner-ship, delete\n\n"""
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def clan(self, ctx):
		pass

	@clan.command(usage="clan create [Названия]", description="**Создаёт клан**")
	async def create(self, ctx, *, name: str):
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
		user_data = await self.client.database.sel_user(target=ctx.author)
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		for clan in data:
			if ctx.author.id in clan["members"]:
				emb = await self.client.utils.create_error_embed(
					ctx, "Вы уже находитесь в одном из кланов сервера!"
				)
				await ctx.send(embed=emb)
				return

		if user_data["coins"] < 15000:
			emb = await self.client.utils.create_error_embed(
				ctx, "У вас не достаточно коинов!"
			)
			await ctx.send(embed=emb)
			return

		if len(data) > 20:
			emb = await self.client.utils.create_error_embed(
				ctx, "Превышен лимит кланов на сервере!"
			)
			await ctx.send(embed=emb)
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

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			clans=json.dumps(data)
		)
		await self.client.database.update(
			"users",
			where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
			clan=new_id,
			coins=coins
		)

		if "clans" in audit.keys():
			e = discord.Embed(
				description=f"Создан новый клан",
				colour=discord.Color.green(),
				timestamp=datetime.utcnow(),
			)
			e.add_field(name="Id клана", value=f"`{new_id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Создания клана сервера",
				icon_url=ctx.author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["clans"])
			if channel is not None:
				await channel.send(embed=e)

	@clan.command(
		usage="clan edit [Параметр] [Новое значения]",
		description="**Изменяет настройки клана**",
	)
	async def edit(self, ctx, field: str, *, value: str):
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
		user_clan = (await self.client.database.sel_user(target=ctx.author))["clan"]
		field = field.lower()

		if user_clan == "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Вас нету ни в одном клане сервера!"
			)
			await ctx.send(embed=emb)
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
						try:
							await ctx.message.add_reaction("✅")
						except discord.errors.Forbidden:
							pass
						except discord.errors.HTTPException:
							pass

						clan[field] = value
						await self.client.database.update(
							"guilds",
							where={"guild_id": ctx.guild.id},
							clans=json.dumps(data)
						)
					else:
						emb = await self.client.utils.create_error_embed(
							ctx, f"Укажите изменяемый параметр из этих: {', '.join(fields)}!"
						)
						await ctx.send(embed=emb)
						return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "Вы не владелец указаного клана!"
					)
					await ctx.send(embed=emb)
					return

	@clan.command(
		name="trans-owner-ship",
		usage="clan trans-owner-ship [@Участник]",
		description="**Передаёт права владения клана указаному участнику**",
	)
	async def trans_own_ship(self, ctx, member: discord.Member):
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
		user_clan = (await self.client.database.sel_user(target=ctx.author))["clan"]

		if user_clan == "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Вас нету ни в одном клане сервера!"
			)
			await ctx.send(embed=emb)
			return

		if (await self.client.database.sel_user(target=member))["clan"] != "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Указаный участник уже есть в одном из кланов сервера!"
			)
			await ctx.send(embed=emb)
			return

		if member == ctx.author:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете передать права на владения клана себе!"
			)
			await ctx.send(embed=emb)
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
					await member.add_roles(ctx.guild.get_role(clan["role_id"]))
					await self.client.database.update(
						"guilds",
						where={"guild_id": ctx.guild.id},
						clans=json.dumps(data)
					)
					await self.client.database.update(
						"users",
						where={"user_id": member.id, "guild_id": ctx.guild.id},
						clan=clan["id"]
					)
					return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "Вы не владелец указаного клана!"
					)
					await ctx.send(embed=emb)
					return

	@clan.command(usage="clan delete", description="**Удаляет клан**")
	async def delete(self, ctx):
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
		user_clan = (await self.client.database.sel_user(target=ctx.author))["clan"]
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if user_clan == "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Вас нету ни в одном клане сервера!"
			)
			await ctx.send(embed=emb)
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
						emb = await self.client.utils.create_error_embed(
							ctx, "Клана с таким id не существует!"
						)
						await ctx.send(embed=emb)
						return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "Вы не владелец указаного клана!"
					)
					await ctx.send(embed=emb)
					return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			clans=json.dumps(data)
		)
		for member_id in delete_clan["members"]:
			await self.client.database.update(
				"users",
				where={"user_id": member_id, "guild_id": ctx.guild.id},
				clan=""
			)

		await self.client.database.update(
			"users",
			where={"user_id": delete_clan["owner"], "guild_id": ctx.guild.id},
			clan=""
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

		if "clans" in audit.keys():
			e = discord.Embed(
				description=f"Удален клан",
				colour=discord.Color.green(),
				timestamp=datetime.utcnow(),
			)
			e.add_field(
				name="Названия клана", value=f"""`{delete_clan["name"]}`""", inline=False
			)
			e.add_field(
				name="Id клана", value=f"""`{delete_clan["id"]}`""", inline=False
			)
			e.set_author(
				name="Журнал аудита | Удаления клана сервера",
				icon_url=ctx.author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["clans"])
			if channel is not None:
				await channel.send(embed=e)

	@clan.command(
		usage="clan members", description="**Показывает всех участников клана**"
	)
	async def members(self, ctx, clan_id: str = None):
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
		state = False
		if not clan_id:
			if (await self.client.database.sel_user(target=ctx.author))["clan"] != "":
				clan_id = (await self.client.database.sel_user(target=ctx.author))["clan"]
			else:
				emb = await self.client.utils.create_error_embed(
					ctx, "Вы не указали аргумент. Укажити аргумент - clan_id к указаной команде!"
				)
				await ctx.send(embed=emb)
				return

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
			emb = await self.client.utils.create_error_embed(
				ctx, "Клана с таким id не существует!"
			)
			await ctx.send(embed=emb)
			return

	@clan.command(
		usage="clan kick [@Участник]",
		description="**Кикает указаного участника с клана**",
	)
	async def kick(self, ctx, member: discord.Member):
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
		user_clan = (await self.client.database.sel_user(target=ctx.author))["clan"]
		if user_clan == "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Вас нету ни в одном клане сервера!"
			)
			await ctx.send(embed=emb)
			return

		if member == ctx.author:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете кикнуть самого себя!"
			)
			await ctx.send(embed=emb)
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
						await self.client.database.update(
							"users",
							where={"user_id": member.id, "guild_id": ctx.guild.id},
							clan=""
						)
						await self.client.database.update(
							"guilds",
							where={"guild_id": ctx.guild.id},
							clans=json.dumps(data)
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
							ctx, "В клане нету указаного участника!"
						)
						await ctx.send(embed=emb)
						return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "Вы не владелец указаного клана!"
					)
					await ctx.send(embed=emb)
					return

	@clan.command(
		name="list",
		usage="clan list",
		description="**Показывает все кланы сервера**",
	)
	async def list_clans(self, ctx):
		data = [
			clan
			for clan in (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
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
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
		user_clan = (await self.client.database.sel_user(target=ctx.author))["clan"]
		state = False
		if clan_id is None:
			if user_clan != "":
				clan_id = user_clan
			else:
				emb = await self.client.utils.create_error_embed(
					ctx, "Вы не указали аргумент. Укажити аргумент - clan_id к указаной команде!"
				)
				await ctx.send(embed=emb)
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
			emb = await self.client.utils.create_error_embed(
				ctx, "Клана с таким id не существует!"
			)
			await ctx.send(embed=emb)
			return

	@clan.command(
		usage="clan leave", description="**С помощью команды вы покидаете ваш клан**"
	)
	async def leave(self, ctx):
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
		user_clan = (await self.client.database.sel_user(target=ctx.author))["clan"]
		if user_clan == "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Вас нету ни в одном клане сервера!"
			)
			await ctx.send(embed=emb)
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
					await self.client.database.update(
						"users",
						where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
						clan=clan["id"]
					)
					await self.client.database.update(
						"guilds",
						where={"guild_id": ctx.guild.id},
						clans=json.dumps(data)
					)
					try:
						await ctx.message.add_reaction("✅")
					except discord.errors.Forbidden:
						pass
					except discord.errors.HTTPException:
						pass
					break
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "Вы не можете покинуть свой клан!"
					)
					await ctx.send(embed=emb)
					return

	@clan.command(
		name="create-invite",
		usage="clan create-invite",
		description="**Создаёт новое приглашения**",
	)
	async def create_invite(self, ctx):
		user_clan = (await self.client.database.sel_user(target=ctx.author))["clan"]
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]

		if user_clan == "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Вас нету ни в одном клане сервера!"
			)
			await ctx.send(embed=emb)
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
						await self.client.database.update(
							"guilds",
							where={"guild_id": ctx.guild.id},
							clans=json.dumps(data)
						)
					else:
						emb = await self.client.utils.create_error_embed(
							ctx, "Указаный клан переполнен!"
						)
						await ctx.send(embed=emb)
						return
				else:
					if clan["owner"] == ctx.author.id:
						if len(clan["members"]) < clan["size"]:
							pass
						else:
							emb = await self.client.utils.create_error_embed(
								ctx, "Указаный клан переполнен!"
							)
							await ctx.send(embed=emb)
							return
					else:
						emb = await self.client.utils.create_error_embed(
							ctx, "Указаный клан приватный!"
						)
						await ctx.send(embed=emb)
						return

	@clan.command(
		name="use-invite",
		usage="clan use-invite [Код приглашения]",
		description="**С помощью команды вы используете указаное приглашения**",
	)
	async def use_invite(self, ctx, invite: str):
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
		state = False

		if (await self.client.database.sel_user(target=ctx.author))["clan"] != "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы уже находитесь в одном из кланов сервера!"
			)
			await ctx.send(embed=emb)
			return

		for clan in data:
			if invite in clan["invites"]:
				state = True
				if ctx.author.id not in clan["members"]:
					clan["invites"].remove(invite)
					clan["members"].append(ctx.author.id)
					await self._add_member(ctx, clan["id"], ctx.author)
					await self.client.database.update(
						"guilds",
						where={"guild_id": ctx.guild.id},
						clans=json.dumps(data)
					)
					break
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "Вы уже находитесь в этом клане!"
					)
					await ctx.send(embed=emb)
					return

		if not state:
			emb = await self.client.utils.create_error_embed(
				ctx, "Такого приглашения не существует!"
			)
			await ctx.send(embed=emb)
			return

	@clan.command(
		name="send-join-request",
		usage="clan send-join-request [Id клана]",
		description="**Отправляет запрос на присоиденения к клану**",
	)
	async def send_join_request(self, ctx, clan_id: str):
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
		state = False

		if (await self.client.database.sel_user(target=ctx.author))["clan"] != "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы уже находитесь в одном из кланов сервера!"
			)
			await ctx.send(embed=emb)
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
						await self.client.database.update(
							"guilds",
							where={"guild_id": ctx.guild.id},
							clans=json.dumps(data)
						)
					else:
						emb = await self.client.utils.create_error_embed(
							ctx, "Вы уже отправили запрос этому клану!"
						)
						await ctx.send(embed=emb)
						return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "Указаный клан переполнен!"
					)
					await ctx.send(embed=emb)
					return

		if not state:
			emb = await self.client.utils.create_error_embed(
				ctx, "Клана с таким id не существует!"
			)
			await ctx.send(embed=emb)
			return

	@clan.command(
		name="list-join-requests",
		usage="clan list-join-requests",
		description="**Показывает список всех запросов на присоединения к клану**",
	)
	async def list_join_requests(self, ctx):
		user_clan = (await self.client.database.sel_user(target=ctx.author))["clan"]
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]

		if user_clan == "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Вас нету ни в одном клане сервера!"
			)
			await ctx.send(embed=emb)
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
					emb = await self.client.utils.create_error_embed(
						ctx, "Вы не владелец указаного клана!"
					)
					await ctx.send(embed=emb)
					return

	@clan.command(
		name="accept-join-request",
		usage="clan accept-join-request [@Участник]",
		description="**Принимает указаный запрос на присоиденения к клану**",
	)
	async def accept_join_request(self, ctx, member: discord.Member):
		user_clan = (await self.client.database.sel_user(target=ctx.author))["clan"]
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]

		if user_clan == "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Вас нету ни в одном клане сервера!"
			)
			await ctx.send(embed=emb)
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
						except discord.errors.Forbidden:
							pass

						try:
							await ctx.message.add_reaction("✅")
						except discord.errors.Forbidden:
							pass
						except discord.errors.HTTPException:
							pass
						clan["join_requests"].remove(member.id)
						clan["members"].append(member.id)
						await self._add_member(ctx, clan["id"], member)
						await self.client.database.update(
							"guilds",
							where={"guild_id": ctx.guild.id},
							clans=json.dumps(data)
						)
					else:
						emb = await self.client.utils.create_error_embed(
							ctx, "Указаный участник не отправлял запрос на присоиденения к клану!"
						)
						await ctx.send(embed=emb)
						return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "Вы не владелец указаного клана!"
					)
					await ctx.send(embed=emb)
					return

	@clan.command(
		name="reject-join-request",
		usage="clan reject-join-request [@Участник]",
		description="**Отклоняет указаный запрос на присоиденения к клану**",
	)
	async def reject_join_request(self, ctx, member: discord.Member):
		user_clan = (await self.client.database.sel_user(target=ctx.author))["clan"]
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]

		if user_clan == "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Вас нету ни в одном клане сервера!"
			)
			await ctx.send(embed=emb)
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
						except discord.errors.Forbidden:
							pass

						try:
							await ctx.message.add_reaction("✅")
						except discord.errors.Forbidden:
							pass
						except discord.errors.HTTPException:
							pass

						clan["join_requests"].remove(member.id)
						await self.client.database.update(
							"guilds",
							where={"guild_id": ctx.guild.id},
							clans=json.dumps(data)
						)
					else:
						emb = await self.client.utils.create_error_embed(
							ctx, "Указаный участник не отправлял запрос на присоиденения к клану!"
						)
						await ctx.send(embed=emb)
						return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "Вы не владелец указаного клана!"
					)
					await ctx.send(embed=emb)
					return

	@clan.command(
		usage="clan buy [Предмет] |Цвет|",
		description="**Покупает указаный предмет для клана**",
	)
	async def buy(self, ctx, item: str, color: str = None):
		user_data = await self.client.database.sel_user(target=ctx.author)
		data = (await self.client.database.sel_guild(guild=ctx.guild))["clans"]
		item = item.lower()

		if user_data["clan"] == "":
			emb = await self.client.utils.create_error_embed(
				ctx, "Вас нету ни в одном клане сервера!"
			)
			await ctx.send(embed=emb)
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

							await self.client.database.update(
								"guilds",
								where={"guild_id": ctx.guild.id},
								clans=json.dumps(data)
							)
							await self.client.database.update(
								"users",
								where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
								coins=user_data["coins"]
							)
						else:
							emb = await self.client.utils.create_error_embed(
								ctx, "У вас не достаточно коинов!"
							)
							await ctx.send(embed=emb)
							return
					else:
						emb = await self.client.utils.create_error_embed(
							ctx, "Клан уже имеет категорию!"
						)
						await ctx.send(embed=emb)
						return
				elif item == "size" or item == "размер":
					if user_data["coins"] >= 7500:
						if clan["size"] >= 25:
							emb = await self.client.utils.create_error_embed(
								ctx, "Клан достиг максимального размера(25 участников)!"
							)
							await ctx.send(embed=emb)
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
						await self.client.database.update(
							"guilds",
							where={"guild_id": ctx.guild.id},
							clans=json.dumps(data)
						)
						await self.client.database.update(
							"users",
							where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
							coins=user_data["coins"]
						)
					else:
						emb = await self.client.utils.create_error_embed(
							ctx, "У вас не достаточно коинов!"
						)
						await ctx.send(embed=emb)
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
						emb = await self.client.utils.create_error_embed(
							ctx, f"Указан не правильный цвет, укажите из этих: {', '.join(colors.keys())}!"
						)
						await ctx.send(embed=emb)
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
							await self.client.database.update(
								"users",
								where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
								coins=user_data["coins"]
							)
						except:
							emb = await self.client.utils.create_error_embed(
								ctx, f"Роль клана удалена!"
							)
							await ctx.send(embed=emb)
							return
					else:
						emb = await self.client.utils.create_error_embed(
							ctx, "У вас не достаточно коинов!"
						)
						await ctx.send(embed=emb)
						return
				else:
					emb = await self.client.utils.create_error_embed(
						ctx, "Вы указали не правильный предмет!"
					)
					await ctx.send(embed=emb)
					return


def setup(client):
	client.add_cog(Clans(client))
