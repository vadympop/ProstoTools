import discord
import json
import typing
import time
import os
import uuid
import datetime
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


class Moderate(commands.Cog, name="Moderate"):
	def __init__(self, client):
		self.client = client
		self.TEMP_PATH = self.client.config.TEMP_PATH
		self.MUTE_ROLE = self.client.config.MUTE_ROLE
		self.VMUTE_ROLE = self.client.config.VMUTE_ROLE
		self.SOFTBAN_ROLE = self.client.config.SOFTBAN_ROLE
		self.FOOTER = self.client.config.FOOTER_TEXT

	@commands.command(
		description="**Удаляет указаное число сообщений**",
		usage="clear |@Участник| [Число удаляемых сообщений]",
		help="**Полезное:**\nМаксимальное число удаляемых сообщений равняется 100\nБот не может удалить сообщения старше 14 дней\n\n**Примеры использования:**\n1. {Prefix}clear 10\n2. {Prefix}clear @Участник 10\n3. {Prefix}clear 660110922865704980 10\n\n**Пример 1:** Удалит 10 сообщений\n**Пример 2:** Удалит 10 сообщений упомянотого участника в текущем канале\n**Пример 3:** Удалит 10 сообщений участника с указаным id",
	)
	@commands.check(check_role)
	async def clear(self, ctx, member: typing.Optional[discord.Member], amount: int):
		if amount <= 0:
			emb = await self.client.utils.create_error_embed(ctx, "Укажите число удаляемых сообщения больше 0!")
			await ctx.send(embed=emb)
			return

		if amount >= 100:
			emb = await self.client.utils.create_error_embed(ctx, "Укажите число удаляемых сообщения меньше 100!")
			await ctx.send(embed=emb)
			return

		number = 0
		delete_messages = ""
		delete_messages_objs = []
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]
		if member is None:
			async with ctx.typing():
				delete_messages_fp = self.TEMP_PATH + str(uuid.uuid4()) + ".txt"
				num_channel_messages = len(await ctx.channel.history().flatten())
				async for msg in ctx.channel.history():
					if (datetime.datetime.utcnow()-msg.created_at) >= datetime.timedelta(weeks=2):
						emb = await self.client.utils.create_error_embed(
							ctx, "Я не могу удалить сообщения старше 14 дней!"
						)
						await ctx.send(embed=emb)
						return

					if "moderate" in audit.keys():
						delete_messages += f"""\n{msg.created_at.strftime("%H:%M:%S %d-%m-%Y")} -- {str(msg.author)}\n{msg.content}\n\n"""
					delete_messages_objs.append(msg)
					number += 1
					if number >= amount or number >= num_channel_messages:
						await ctx.channel.delete_messages(delete_messages_objs)
						emb = discord.Embed(
							description=f"** :white_check_mark: Удаленно {number} сообщений**",
							colour=discord.Color.green(),
						)
						emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)

						if "moderate" in audit.keys():
							self.client.txt_dump(delete_messages_fp, delete_messages)
							e = discord.Embed(
								colour=discord.Color.orange(), timestamp=datetime.datetime.utcnow()
							)
							e.add_field(
								name=f"Модератор {str(ctx.author)}",
								value=f"Удалил {number} сообщений",
								inline=False,
							)
							e.set_author(
								name="Журнал аудита | Модерация",
								icon_url=ctx.author.avatar_url,
							)
							e.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							channel = ctx.guild.get_channel(audit["moderate"])
							if channel is not None:
								await channel.send(
									embed=e, file=discord.File(fp=delete_messages_fp)
								)
							os.remove(
								"/home/PROSTO-TOOLS-DiscordBot"+delete_messages_fp[1:]
							)
						break

		elif member is not None and member in ctx.guild.members:
			async with ctx.typing():
				async for msg in ctx.channel.history().filter(lambda m: m.author == member):
					await msg.delete()
					number += 1
					if number >= amount:
						emb = discord.Embed(
							description=f"** :white_check_mark: Удаленно {number} сообщений от пользователя {member.mention}**",
							colour=discord.Color.green(),
						)
						emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
						break

	@commands.command(
		aliases=["temprole"],
		name="temp-role",
		description="**Дает указаную роль учаснику на время**",
		usage="temp-role [@Участник] [@Роль] [Длительность]",
		help="**Примеры использования:**\n1. {Prefix}temp-role @Участник @Роль 10m\n2. {Prefix}temp-role 660110922865704980 717776604461531146 10m\n3. {Prefix}temp-role @Участник 717776604461531146 10m\n4. {Prefix}temp-role 660110922865704980 @Роль 10m\n\n**Пример 1:** Даёт упомянутую роль упомянутому участнику\n**Пример 2:** Даёт роль с указаным id участнику с указаным id\n**Пример 3:** Даёт роль с указаным id упомянутому участнику\n**Пример 4:** Даёт упомянутую роль участнику с указаным id",
	)
	@commands.check(check_role)
	async def temprole(
		self, ctx, member: discord.Member, role: discord.Role, type_time: str
	):
		if member == ctx.author:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
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

		if role >= ctx.guild.me.top_role:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Указаная роль выше моей роли!"
			)
			await ctx.send(embed=emb)
			return

		if ctx.author.top_role <= role and ctx.author != ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете выдать роль которая выше вашей роли!"
			)
			await ctx.send(embed=emb)
			return

		if type_time.isalpha():
			emb = await self.client.utils.create_error_embed(
				ctx, "Время указано в неправильном формате!"
			)
			await ctx.send(embed=emb)
			return

		role_time = self.client.utils.time_to_num(type_time)
		times = time.time() + role_time[0]

		await member.add_roles(role)
		emb = discord.Embed(
			description=f"**{member}**({member.mention}) Была виданна роль\nРоль: `{role.name}`\nВремя: `{role_time[1]}{role_time[2]}`",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		if role_time[0] > 0:
			await self.client.database.set_punishment(
				type_punishment="temprole",
				time=times,
				member=member,
				role_id=int(role.id),
			)

	@commands.command(
		aliases=["slowmode"],
		name="slow-mode",
		description="**Ставить медленный режим указаному каналу(Если канал не указан медленный режим ставиться всем каналам, 0 - выключает медленный режим, длительность не указывать меньше нуля)**",
		usage="slow-mode [Время] |Канал|",
		help="**Примеры использования:**\n1. {Prefix}slow-mode 10 #Канал\n2. {Prefix}slow-mode 10 717776571406090313\n\n**Пример 1:** Ставит упомянутому канала медленный режим на 10 секунд\n**Пример 2:** Ставит каналу с указаным id медленный режим на 10 секунд",
	)
	@commands.check(check_role)
	async def slowmode(self, ctx, delay: int, channel: discord.TextChannel = None):
		if delay > 21000:
			emb = await self.client.utils.create_error_embed(
				ctx, "Укажите задержку меньше 21000!"
			)
			await ctx.send(embed=emb)
			return

		if channel is None:
			guild_text_channels = ctx.guild.text_channels
			for channel in guild_text_channels:
				await channel.edit(slowmode_delay=delay)

			if delay > 0:
				emb = discord.Embed(
					description=f"**Для всех каналов этого сервера был поставлен медленний режим на {delay}сек**",
					colour=discord.Color.green(),
				)
			elif delay == 0:
				emb = discord.Embed(
					description=f"**Для всех каналов этого сервера был снят медленний режим**",
					colour=discord.Color.green(),
				)
			elif delay < 0:
				emb = discord.Embed(
					description=f"**Вы не правильно указали время, укажите длительность медленого режима больше ноля**",
					colour=discord.Color.green(),
				)

		elif channel is not None:
			slowmode_channel = channel
			await slowmode_channel.edit(slowmode_delay=delay)
			if delay > 0:
				emb = discord.Embed(
					description=f"**Для канала {slowmode_channel.name} был поставлен медленний режим на {delay}сек**",
					colour=discord.Color.green(),
				)
			elif delay == 0:
				emb = discord.Embed(
					description=f"**Для канала {slowmode_channel.name} был снят медленний**",
					colour=discord.Color.green(),
				)
			elif delay < 0:
				emb = discord.Embed(
					description=f"**Вы не правильно указали время, укажыте длительность медленого режима больше ноля**",
					colour=discord.Color.green(),
				)

		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Кикает учасника из сервера**",
		usage="kick [@Участник] |Причина|",
		help="**Примеры использования:**\n1. {Prefix}kick @Участник Нарушения правил сервера\n2. {Prefix}kick 660110922865704980 Нарушения правил сервера\n3. {Prefix}kick @Участник\n4. {Prefix}kick 660110922865704980\n\n**Пример 1:** Кикает с сервера упомянутого участника по причине `Нарушения правил сервера`\n**Пример 2:** Кикает с сервера участника с указаным id по причине `Нарушения правил сервера`\n**Пример 3:** Кикает с сервера упомянутого участника без причины\n**Пример 4:** Кикает с сервера участника с указаным id без причины",
	)
	@commands.check(check_role)
	async def kick(self, ctx, member: discord.Member, *, reason: str = "Причина не указана"):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if member == ctx.author:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return

		if member == ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете выгнать владельца сервера"
			)
			await ctx.send(embed=emb)
			return

		if member.top_role >= ctx.guild.me.top_role:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Я не могу выгнать этого участника!"
			)
			await ctx.send(embed=emb)
			return

		if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете можете выгнать участника который имеет больше прав чем у вас!"
			)
			await ctx.send(embed=emb)
			return

		await member.kick(reason=reason)

		emb = discord.Embed(
			description=f"**{member}**({member.mention}) Был выгнан\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были выгнаны с сервера\nСервер: `{ctx.guild.name}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"Пользователь `{str(member)}` был выгнан",
				colour=discord.Color.dark_gold(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name="Модератором",
				value=str(ctx.author),
				inline=False,
			)
			e.add_field(
				name="Причина",
				value=reason,
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Кик пользователя", icon_url=ctx.author.avatar_url
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)

	@commands.command(
		aliases=["softban"],
		name="soft-ban",
		description="**Апаратно банит указаного участника - участник имеет доступ к серверу, но к каналам доступа нет**",
		usage="soft-ban [@Участник] |Длительность| |Причина|",
		help="**Полезное:**\n\n**Примеры использования:**\n1. {Prefix}soft-ban @Участник 10d Нарушения правил сервера\n2. {Prefix}soft-ban 660110922865704980 10d Нарушения правил сервера\n3. {Prefix}soft-ban @Участник 10d\n4. {Prefix}soft-ban 660110922865704980 10d\n5. {Prefix}soft-ban @Участник\n6. {Prefix}soft-ban 660110922865704980\n7. {Prefix}soft-ban @Участник Нарушения правил сервера\n8. {Prefix}soft-ban 660110922865704980 Нарушения правил сервера\n\n**Пример 1:** Апапаратно банит упомянутого участника по причине `Нарушения правил сервера` на 10 дней\n**Пример 2:** Апапаратно банит участника с указаным id по причине\n`Нарушения правил сервера` на 10 дней\n**Пример 3:** Апапаратно банит упомянутого участника без причины на 10 дней\n**Пример 4:** Апапаратно банит участника с указаным id без причины на 10 дней\n**Пример 5:** Даёт перманентный апапаратный бан упомянутому участнику без причины\n**Пример 6:** Даёт перманентный апапаратный бан участнику с указаным id без причины\n**Пример 7:** Даёт перманентный апапаратный бан упомянутому участнику по причине\n`Нарушения правил сервера`\n**Пример 8:** Даёт апапаратный апапаратный бан участнику с указаным id по причине\n`Нарушения правил сервера`",
	)
	@commands.check(check_role)
	async def softban(
		self, ctx, member: discord.Member, *options: str
	):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if member == ctx.author:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return

		if member == ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете забанить владельца сервера!"
			)
			await ctx.send(embed=emb)
			return

		if member.top_role >= ctx.guild.me.top_role:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Я не могу забанить этого участника"
			)
			await ctx.send(embed=emb)
			return

		if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
			emb = ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете можете забанить участника который имеет больше прав чем у вас!"
			)
			await ctx.send(embed=emb)
			return

		options = list(options)
		if len(options) > 0:
			if not options[0].isalpha():
				type_time = options.pop(0)
				softban_time = self.client.utils.time_to_num(type_time)
				times = time.time() + softban_time[0]
				reason = " ".join(options) if len(options) > 0 else "Причина не указана"
			else:
				reason = " ".join(options)
				softban_time = [0, 0]
		else:
			reason = "Причина не указана"
			softban_time = [0, 0]

		emb = discord.Embed(
			description=f"**{member}**({member.mention}) Был апаратно забанен\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были апаратно забанены на сервере\nСервер: `{ctx.guild.name}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass

		overwrite = discord.PermissionOverwrite(
			connect=False, view_channel=False, send_messages=False
		)
		role = get(ctx.guild.roles, name=self.SOFTBAN_ROLE)

		if role is None:
			role = await ctx.guild.create_role(name=self.SOFTBAN_ROLE)

		await member.edit(voice_channel=None)
		for channel in ctx.guild.channels:
			await channel.set_permissions(role, overwrite=overwrite)

		await member.add_roles(role)

		if softban_time[0] > 0:
			await self.client.database.set_punishment(
				type_punishment="temprole", time=times, member=member, role=role.id
			)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"Пользователь `{str(member)}` был апаратно забанен",
				colour=discord.Color.red(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name=f"Модератором {str(ctx.author)}",
				value=f"На {softban_time[1]} {softban_time[2]}"
				if softban_time[1] != 0
				else "Перманентно",
				inline=False,
			)
			e.add_field(
				name="Причина",
				value=reason,
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Апаратный бан пользователя",
				icon_url=ctx.author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)

	@commands.command(
		aliases=["unsoftban"],
		name="unsoft-ban",
		description="**Снимает апаратный с указаного участника**",
		usage="unsoft-ban [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}unsoft-ban @Участник\n2. {Prefix}unsoft-ban 660110922865704980\n\n**Пример 1:** Снимает апаратный бан с упомянутого участника\n**Пример 2:** Снимает апаратный бан с участника с указаным id",
	)
	@commands.check(check_role)
	async def unsoftban(self, ctx, member: discord.Member):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if member == ctx.author:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return

		if member.top_role >= ctx.guild.me.top_role:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Я не могу разбанить этого участника!"
			)
			await ctx.send(embed=emb)
			return

		emb = discord.Embed(
			description=f"`{ctx.author}` **Снял апаратный бан с** `{member}`({member.mention})",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"**С вас был снят апаратный бан на сервере** `{ctx.guild.name}`",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass

		role = get(ctx.guild.roles, name=self.SOFTBAN_ROLE)
		if role is None:
			role = await ctx.guild.create_role(name=self.SOFTBAN_ROLE)

		if role in member.roles:
			await member.remove_roles(role)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"С пользователя `{str(member)}` был снят апаратный бан",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name="Модератором",
				value=str(ctx.author),
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Апаратный разбан пользователя",
				icon_url=ctx.author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)

	@commands.command(
		description="**Банит учасника по указаной причине (Перманентно или на время)**",
		usage="ban [@Участник] |Длительность| |Причина|",
		help="**Примеры использования:**\n1. {Prefix}ban @Участник 10d Нарушения правил сервера\n2. {Prefix}ban 660110922865704980 10d Нарушения правил сервера\n3. {Prefix}ban @Участник 10d\n4. {Prefix}ban 660110922865704980 10d\n5. {Prefix}ban @Участник\n6. {Prefix}ban 660110922865704980\n7. {Prefix}ban @Участник Нарушения правил сервера\n8. {Prefix}ban 660110922865704980 Нарушения правил сервера\n\n**Пример 1:** Банит упомянутого участника по причине `Нарушения правил сервера` на 10 дней\n**Пример 2:** Банит участника с указаным id по причине\n`Нарушения правил сервера` на 10 дней\n**Пример 3:** Банит упомянутого участника без причины на 10 дней\n**Пример 4:** Банит участника с указаным id без причины на 10 дней\n**Пример 5:** Перманентно банит упомянутого участника без причины\n**Пример 6:** Перманентно банит участника с указаным id без причины\n**Пример 7:** Перманентно банит упомянутого участника по причине\n`Нарушения правил сервера`\n**Пример 8:** Перманентно банит участника с указаным id по причине\n`Нарушения правил сервера`",
	)
	@commands.check(check_role)
	async def ban(
		self, ctx, member: discord.Member, *options: str
	):
		if member == ctx.author:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return
		
		if member == ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете забанить владельца сервера!"
			)
			await ctx.send(embed=emb)
			return

		if member.top_role >= ctx.guild.me.top_role:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Я не могу забанить этого участника!"
			)
			await ctx.send(embed=emb)
			return

		if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете можете забанить участника который имеет больше прав чем у вас!"
			)
			await ctx.send(embed=emb)
			return

		options = list(options)
		if len(options) > 0:
			if not options[0].isalpha():
				type_time = options.pop(0)
				ban_time = self.client.utils.time_to_num(type_time)
				times = time.time() + ban_time[0]
				reason = " ".join(options) if len(options) > 0 else "Причина не указана"
			else:
				reason = " ".join(options)
				ban_time = [0, 0]
		else:
			reason = "Причина не указана"
			ban_time = [0, 0]

		await member.ban(reason=reason)
		emb = discord.Embed(
			description=f"**{member}**(`{member.id}`) Был забанен\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были забанены на сервере\nСервер: `{ctx.guild.name}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass

		if ban_time[0] > 0:
			await self.client.database.update(
				"users",
				where={"user_id": member.id, "guild_id": ctx.guild.id},
				clan="",
				items=json.dumps([]),
				money=0,
				coins=0,
				reputation=-100
			)
			await self.client.database.set_punishment(type_punishment="ban", time=times, member=member)

	@commands.command(
		aliases=["unban"],
		name="un-ban",
		description="**Снимает бан из указаного учасника**",
		usage="un-ban [@Пользователь]",
		help="**Примеры использования:**\n1. {Prefix}un-ban @Ник+тэг\n2. {Prefix}un-ban 660110922865704980\n\n**Пример 1:** Разбанит указаного пользователя\n**Пример 2:** Разбанит пользователя с указаным id",
	)
	@commands.check(check_role)
	async def unban(self, ctx, *, member: discord.User):
		if member == ctx.author:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return

		async with ctx.typing():
			banned_users = await ctx.guild.bans()
			state = False
			for ban_entry in banned_users:
				user = ban_entry.user

				if user.id == member.id:
					state = True
					await ctx.guild.unban(user)
					await self.client.database.del_punishment(
						member=member, guild_id=ctx.guild.id, type_punishment="ban"
					)

					emb = discord.Embed(
						description=f"`{ctx.author}` **Разбанил** `{member}`({member.mention})",
						colour=discord.Color.green(),
						timestamp=datetime.datetime.utcnow()
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await ctx.send(embed=emb)

					emb = discord.Embed(
						description=f"**Вы были разбанены на сервере** `{ctx.guild.name}`",
						colour=discord.Color.green(),
						timestamp=datetime.datetime.utcnow()
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					try:
						await member.send(embed=emb)
					except:
						pass
					break

			if not state:
				emb = await self.client.utils.create_error_embed(ctx, "Указаный пользователь не забанен!")
				await ctx.send(embed=emb)
				return

	@commands.command(
		description="**Мьютит указаного участника в голосовых каналах**",
		usage="vmute [@Участник] |Длительность| |Причина|",
		help="**Примеры использования:**\n1. {Prefix}vmute @Участник 10d Нарушения правил сервера\n2. {Prefix}vmute 660110922865704980 10d Нарушения правил сервера\n3. {Prefix}vmute @Участник 10d\n4. {Prefix}vmute 660110922865704980 10d\n5. {Prefix}vmute @Участник\n6. {Prefix}vmute 660110922865704980\n7. {Prefix}vmute @Участник Нарушения правил сервера\n8. {Prefix}vmute 660110922865704980 Нарушения правил сервера\n\n**Пример 1:** Мьютит упомянутого участника в голосовых каналах по причине `Нарушения правил сервера` на 10 дней\n**Пример 2:** Мьютит участника с указаным id в голосовых каналах по причине\n`Нарушения правил сервера` на 10 дней\n**Пример 3:** Мьютит упомянутого участника в голосовых каналах без причины на 10 дней\n**Пример 4:** Мьютит участника с указаным id в голосовых каналах без причины на 10 дней\n**Пример 5:** Перманентно мьютит упомянутого участника в голосовых каналах без причины\n**Пример 6:** Перманентно мьютит участника с указаным id в голосовых каналах без причины\n**Пример 7:** Перманентно мьютит упомянутого участника в голосовых каналах по причине\n`Нарушения правил сервера`\n**Пример 8:** Перманентно мьютит участника с указаным id в голосовых каналах по причине\n`Нарушения правил сервера`",
	)
	@commands.check(check_role)
	async def vmute(
		self, ctx, member: discord.Member, *options: str
	):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if member == ctx.author:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return

		if member == ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете замьютить в голосовых каналах владельца сервера!"
			)
			await ctx.send(embed=emb)
			return

		if member.top_role >= ctx.guild.me.top_role:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Я не могу замьютить этого участника в голосовых каналах!"
			)
			await ctx.send(embed=emb)
			return

		if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете можете замьютить участника который имеет больше прав чем у вас!"
			)
			await ctx.send(embed=emb)
			return

		options = list(options)
		if len(options) > 0:
			if not options[0].isalpha():
				type_time = options.pop(0)
				vmute_time = self.client.utils.time_to_num(type_time)
				times = time.time() + vmute_time[0]
				reason = " ".join(options) if len(options) > 0 else "Причина не указана"
			else:
				reason = " ".join(options)
				vmute_time = [0, 0]
		else:
			reason = "Причина не указана"
			vmute_time = [0, 0]

		overwrite = discord.PermissionOverwrite(connect=False)
		role = get(ctx.guild.roles, name=self.VMUTE_ROLE)

		if role is None:
			role = await ctx.guild.create_role(name=self.VMUTE_ROLE)
		for channel in ctx.guild.voice_channels:
			await channel.set_permissions(role, overwrite=overwrite)

		await member.add_roles(role)
		await member.edit(voice_channel=None)

		description_time = str(vmute_time[1])+str(vmute_time[2]) if vmute_time[0] != 0 else "Перманентно"
		emb = discord.Embed(
			description=f"**{member}**({member.mention}) Был замьючен в голосовых каналах\nВремя: `{description_time}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были замьчены в голосовых каналах на сервере\nСервер: `{ctx.guild.name}`\nВремя: `{description_time}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass

		if vmute_time[0] > 0:
			await self.client.database.set_punishment(
				type_punishment="vmute", time=times, member=member, role_id=int(role.id)
			)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"Пользователь `{str(member)}` был замьючен в голосовых каналах",
				colour=discord.Color.teal(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name=f"Модератором {str(ctx.author)}",
				value=f"На {vmute_time[1]} {vmute_time[2]}"
				if vmute_time[0] != 0
				else "Перманентно",
				inline=False,
			)
			e.add_field(
				name="Причина",
				value=reason,
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Голосовой мьют пользователя",
				icon_url=ctx.author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)

	@commands.command(
		aliases=["unvmute"],
		name="un-vmute",
		description="**Снимает мьют с указаного участника в голосовых каналах**",
		usage="un-vmute [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}un-vmute @Участник\n2. {Prefix}un-vmute 660110922865704980\n\n**Пример 1:** Размьютит указаного участника в голосовых каналах\n**Пример 2:** Размьютит участника с указаным id в голосовых каналах",
	)
	@commands.check(check_role)
	async def unvmute(self, ctx, member: discord.Member):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if member == ctx.author:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return

		if member == ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете размьють в голосовых каналах владельца сервера!"
			)
			await ctx.send(embed=emb)
			return

		if member.top_role >= ctx.guild.me.top_role:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Я не могу размьютить этого участника в голосовых каналах!"
			)
			await ctx.send(embed=emb)
			return

		for vmute_role in ctx.guild.roles:
			if vmute_role.name == self.VMUTE_ROLE:
				await self.client.database.del_punishment(
					member=member, guild_id=ctx.guild.id, type_punishment="vmute"
				)
				await member.remove_roles(vmute_role)
				overwrite = discord.PermissionOverwrite(connect=None)

				for channel in ctx.guild.voice_channels:
					await channel.set_permissions(vmute_role, overwrite=overwrite)

				emb = discord.Embed(
					description=f"`{ctx.author}` **Размьютил** `{member}`({member.mention}) **в голосовых каналах**",
					colour=discord.Color.green(),
					timestamp=datetime.datetime.utcnow()
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)

				emb = discord.Embed(
					description=f"**Вы были размьючены в голосовых каналах на сервере** `{ctx.guild.name}`",
					colour=discord.Color.green(),
					timestamp=datetime.datetime.utcnow()
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				try:
					await member.send(embed=emb)
				except:
					pass

				if "moderate" in audit.keys():
					e = discord.Embed(
						description=f"Пользователь `{str(member)}` был размьючен в голосовых каналах",
						colour=discord.Color.green(),
						timestamp=datetime.datetime.utcnow(),
					)
					e.add_field(
						name="Модератором",
						value=str(ctx.author),
						inline=False,
					)
					e.add_field(
						name="Id Участника", value=f"`{member.id}`", inline=False
					)
					e.set_author(
						name="Журнал аудита | Голосовой размьют пользователя",
						icon_url=ctx.author.avatar_url,
					)
					e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					channel = ctx.guild.get_channel(audit["moderate"])
					if channel is not None:
						await channel.send(embed=e)
				return

	@commands.command(
		description="**Мютит учасника по указаной причине (На выбор, можно без причины)**",
		usage="mute [@Участник] |Длительность| |Причина|",
		help="**Примеры использования:**\n1. {Prefix}mute @Участник 10d Нарушения правил сервера\n2. {Prefix}mute 660110922865704980 10d Нарушения правил сервера\n3. {Prefix}mute @Участник 10d\n4. {Prefix}mute 660110922865704980 10d\n5. {Prefix}mute @Участник\n6. {Prefix}mute 660110922865704980\n7. {Prefix}mute @Участник Нарушения правил сервера\n8. {Prefix}mute 660110922865704980 Нарушения правил сервера\n\n**Пример 1:** Мьютит упомянутого участника по причине `Нарушения правил сервера` на 10 дней\n**Пример 2:** Мьютит участника с указаным id по причине\n`Нарушения правил сервера` на 10 дней\n**Пример 3:** Мьютит упомянутого участника без причины на 10 дней\n**Пример 4:** Мьютит участника с указаным id без причины на 10 дней\n**Пример 5:** Перманентно мьютит упомянутого участника без причины\n**Пример 6:** Перманентно мьютит участника с указаным id без причины\n**Пример 7:** Перманентно мьютит упомянутого участника по причине\n`Нарушения правил сервера`\n**Пример 8:** Перманентно мьютит участника с указаным id по причине\n`Нарушения правил сервера`",
	)
	@commands.check(check_role)
	async def mute(
		self, ctx, member: discord.Member, *options: str
	):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if member == ctx.author:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return

		if member == ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете замьютить владельца сервера!"
			)
			await ctx.send(embed=emb)
			return

		if member.top_role >= ctx.guild.me.top_role:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Я не могу замьютить этого участника!"
			)
			await ctx.send(embed=emb)
			return

		if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете можете замьютить участника который имеет больше прав чем у вас!"
			)
			await ctx.send(embed=emb)
			return

		options = list(options)
		if len(options) > 0:
			if not options[0].isalpha():
				type_time = options.pop(0)
				mute_time = self.client.utils.time_to_num(type_time)
				times = time.time() + mute_time[0]
				reason = " ".join(options) if len(options) > 0 else "Причина не указана"
			else:
				reason = " ".join(options)
				mute_time = [0, 0]
		else:
			reason = "Причина не указана"
			mute_time = [0, 0]

		data = await self.client.database.sel_user(target=member)
		role = get(ctx.guild.roles, name=self.MUTE_ROLE)
		if role is None:
			role = await ctx.guild.create_role(name=self.MUTE_ROLE)

		if role in member.roles:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Указаный пользователь уже замьючен!"
			)
			await ctx.send(embed=emb)
			return

		async with ctx.typing():
			overwrite = discord.PermissionOverwrite(send_messages=False)
			await member.add_roles(role)
			for channel in ctx.guild.text_channels:
				await channel.set_permissions(role, overwrite=overwrite)

			cur_lvl = data["level"]
			cur_coins = data["coins"] - 1500
			cur_money = data["money"]
			cur_reputation = data["reputation"] - 15
			cur_items = data["items"]
			prison = data["prison"]

			if cur_reputation < -100:
				cur_reputation = -100

			if cur_lvl <= 3:
				cur_money -= 250
			elif 3 < cur_lvl <= 5:
				cur_money -= 500
			elif cur_lvl > 5:
				cur_money -= 1000

			if cur_coins <= 0:
				cur_coins = 0

			if cur_money <= -5000:
				prison = True
				cur_items = []
				emb = discord.Embed(
					description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Текущий баланс - `{cur_money}`**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				try:
					await member.send(embed=emb)
				except:
					pass

			await self.client.database.update(
				"users",
				where={"user_id": member.id, "guild_id": ctx.guild.id},
				money=cur_money,
				coins=cur_coins,
				reputation=cur_reputation,
				items=json.dumps(cur_items),
				prison=str(prison)
			)

			description_time = str(mute_time[1]) + str(mute_time[2]) if mute_time[0] != 0 else "Перманентно"
			emb = discord.Embed(
				description=f"**{member}**({member.mention}) Был замьючен\nВремя: `{description_time}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow()
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			emb = discord.Embed(
				description=f"Вы были замьчены на сервере\nСервер: `{ctx.guild.name}`\nВремя: `{description_time}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow()
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			try:
				await member.send(embed=emb)
			except:
				pass

			if mute_time[0] > 0:
				await self.client.database.set_punishment(
					type_punishment="mute",
					time=times,
					member=member,
					role_id=int(role.id),
					reason=reason,
					author=ctx.author.id,
				)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"Пользователь `{str(member)}` был замьючен",
				colour=discord.Color.teal(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name=f"Модератором {str(ctx.author)}",
				value=f"На {mute_time[1]} {mute_time[2]}"
				if mute_time[0] != 0
				else "Перманентно",
				inline=False,
			)
			e.add_field(
				name="Причина",
				value=reason,
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Мьют пользователя", icon_url=ctx.author.avatar_url
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)

	@commands.command(
		aliases=["unmute"],
		name="un-mute",
		description="**Размютит указаного учасника**",
		usage="un-mute [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}un-mute @Участник\n2. {Prefix}un-mute 660110922865704980\n\n**Пример 1:** Размьютит указаного участника\n**Пример 2:** Размьютит участника с указаным id",
	)
	@commands.check(check_role)
	async def unmute(self, ctx, member: discord.Member):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if member == ctx.author:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return

		if member == ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете размьютить владельца сервера"
			)
			await ctx.send(embed=emb)
			return

		if member.top_role >= ctx.guild.me.top_role:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Я не могу размьютить этого участника"
			)
			await ctx.send(embed=emb)
			return

		for role in ctx.guild.roles:
			if role.name == self.MUTE_ROLE:
				await self.client.database.del_punishment(
					member=member, guild_id=ctx.guild.id, type_punishment="mute"
				)
				await member.remove_roles(role)

				emb = discord.Embed(
					description=f"`{ctx.author}` **Размьютил** `{member}`({member.mention})",
					colour=discord.Color.green(),
					timestamp=datetime.datetime.utcnow()
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)

				emb = discord.Embed(
					description=f"**Вы были размьючены на сервере** `{ctx.guild.name}`",
					colour=discord.Color.green(),
					timestamp=datetime.datetime.utcnow()
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				try:
					await member.send(embed=emb)
				except:
					pass

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"Пользователь `{str(member)}` был размьючен",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name="Модератором",
				value=str(ctx.author),
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Размьют пользователя",
				icon_url=ctx.author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)

	@commands.command(
		aliases=["clearwarns"],
		name="clear-warns",
		description="**Очищает предупреждения в указаного пользователя**",
		usage="clear-warns [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}clear-warns @Участник\n2. {Prefix}clear-warns 660110922865704980\n\n**Пример 1:** Очищает все предупреждения указаного участника\n**Пример 2:** Очищает все предупреждения участника с указаным id",
	)
	@commands.check(check_role)
	async def clearwarn(self, ctx, member: discord.Member):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if member == ctx.author:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return

		async with ctx.typing():
			warns = (await self.client.database.sel_user(target=member))["warns"]
			warns_ids = [warn["id"] for warn in warns]
			for warn_id in warns_ids:
				await self.client.database.del_warn(ctx.guild.id, warn_id)

			emb = discord.Embed(
				description=f"**У пользователя** `{member}`({member.mention}) **были сняты предупреждения**",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow()
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"У пользователя `{str(member)}` были сняты все предупреждения",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name="Модератором",
				value=str(ctx.author),
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Снятия всех предупреждений пользователя",
				icon_url=ctx.author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)

	@commands.command(
		description="**Дает придупреждения учаснику по указаной причине**",
		usage="warn [@Участник] |Причина|",
		help="**Примеры использования:**\n1. {Prefix}warn @Участник Нарушения правил сервера\n2. {Prefix}warn 660110922865704980 Нарушения правил сервера\n3. {Prefix}warn @Участник\n4. {Prefix}warn 660110922865704980\n\n**Пример 1:** Даёт предупреждения упомянутого участнику по причине `Нарушения правил сервера`\n**Пример 2:** Даёт предупреждения участнику с указаным id по причине\n`Нарушения правил сервера`\n**Пример 3:** Даёт предупреждения упомянутого участнику без причины\n**Пример 4:** Даёт предупреждения участнику с указаным id без причины",
	)
	@commands.check(check_role)
	async def warn(self, ctx, member: discord.Member, *, reason: str = "Причина не указана"):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if member == ctx.author:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return

		if member == ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете дать предупреждения владельцу сервера!"
			)
			await ctx.send(embed=emb)
			return

		if member.top_role >= ctx.guild.me.top_role:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете дать предупреждения этому участника!"
			)
			await ctx.send(embed=emb)
			return

		if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете можете дать предупреждения участнику который имеет больше прав чем у вас!"
			)
			await ctx.send(embed=emb)
			return

		if member.bot:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете дать предупреждения боту!"
			)
			await ctx.send(embed=emb)
			return

		async with ctx.typing():
			data = await self.client.database.sel_user(target=member)
			info = await self.client.database.sel_guild(guild=ctx.guild)
			max_warns = int(info["warns_settings"]["max"])
			warn_punishment = info["warns_settings"]["punishment"]

			cur_lvl = data["level"]
			cur_coins = data["coins"]
			cur_money = data["money"]
			cur_warns = data["warns"]
			cur_state_pr = data["prison"]
			cur_reputation = data["reputation"] - 10

			warn_id = await self.client.database.set_warn(
				target=member,
				reason=reason,
				author=ctx.author.id,
				time=str(datetime.datetime.utcnow()),
			)

			if cur_lvl <= 3:
				cur_money -= 250
			elif 3 < cur_lvl <= 5:
				cur_money -= 500
			elif cur_lvl > 5:
				cur_money -= 1000

			if cur_money <= -5000:
				cur_state_pr = True
				emb = discord.Embed(
					description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Текущий баланс - {cur_money}**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				try:
					await member.send(embed=emb)
				except:
					pass

			if cur_reputation < -100:
				cur_reputation = -100

			if len(cur_warns) >= 20:
				await self.client.database.del_warn(
					guild_id=ctx.guild.id,
					warn_id=[warn for warn in cur_warns if not warn["state"]][0]["id"]
				)

			if len([warn for warn in cur_warns if warn["state"]]) >= max_warns:
				cur_coins -= 1000

				if cur_reputation < -100:
					cur_reputation = -100

				if cur_coins < 0:
					cur_coins = 0

				if warn_punishment is not None:
					if warn_punishment["type"] == "mute":
						await self.client.support_commands.main_mute(
							ctx=ctx,
							member=member,
							type_time=warn_punishment["time"],
							reason=reason,
							author=ctx.author,
						)
					elif warn_punishment["type"] == "kick":
						try:
							await member.kick(reason=reason)
						except discord.errors.Forbidden:
							pass
					elif warn_punishment["type"] == "ban":
						ban_time = self.client.utils.time_to_num(
							data["auto_mod"]["anti_invite"]["punishment"]["time"]
						)
						times = time.time() + ban_time[0]
						try:
							await member.ban(reason=reason)
						except discord.errors.Forbidden:
							pass
						else:
							if ban_time > 0:
								await self.client.database.update(
									"users",
									where={"user_id": member.id, "guild_id": ctx.guild.id},
									money=0,
									coins=0,
									reputation=-100,
									items=json.dumps([]),
									clan=""
								)
								await self.client.database.set_punishment(
									type_punishment="ban", time=times, member=member
								)
					elif warn_punishment["type"] == "soft-ban":
						softban_time = self.client.utils.time_to_num(
							data["auto_mod"]["anti_invite"]["punishment"]["time"]
						)
						times = time.time() + softban_time[0]
						overwrite = discord.PermissionOverwrite(
							connect=False, view_channel=False, send_messages=False
						)
						role = discord.utils.get(
							ctx.guild.roles, name=self.SOFTBAN_ROLE
						)
						if role is None:
							role = await ctx.guild.create_role(name=self.SOFTBAN_ROLE)

						await member.edit(voice_channel=None)
						for channel in ctx.guild.channels:
							await channel.set_permissions(role, overwrite=overwrite)

						await member.add_roles(role)
						if softban_time[0] > 0:
							await self.client.database.set_punishment(
								type_punishment="temprole", time=times, member=member, role=role.id
							)

				emb = discord.Embed(
					description=f"**{member}**({member.mention}) Достиг максимальное количество предупреждений и получил наказания\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns)+1}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
					colour=discord.Color.green(),
					timestamp=datetime.datetime.utcnow()
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)

				emb = discord.Embed(
					description=f"Вы достигли максимальное количество предупреждений и получили наказания\nСервер: `{ctx.guild.name}`\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns)+1}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
					colour=discord.Color.green(),
					timestamp=datetime.datetime.utcnow()
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				try:
					await member.send(embed=emb)
				except:
					pass

				for warn_id in [warn["id"] for warn in cur_warns]:
					await self.client.database.del_warn(ctx.guild.id, warn_id)
			else:
				emb = discord.Embed(
					description=f"**{member}**({member.mention}) Получил предупреждения\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns)+1}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
					colour=discord.Color.green(),
					timestamp=datetime.datetime.utcnow()
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)

				emb = discord.Embed(
					description=f"Вы получили предупреждения на сервере\nСервер: `{ctx.guild.name}`\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns)+1}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
					colour=discord.Color.green(),
					timestamp=datetime.datetime.utcnow()
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				try:
					await member.send(embed=emb)
				except:
					pass

			await self.client.database.update(
				"users",
				where={"user_id": member.id, "guild_id": ctx.guild.id},
				money=cur_money,
				coins=cur_coins,
				reputation=cur_reputation,
				prison=str(cur_state_pr)
			)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"Пользователь `{str(member)}` получил предупреждения",
				colour=discord.Color.teal(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name=f"Модератором {str(ctx.author)}",
				value=f"Id предупреждения - {warn_id}",
				inline=False,
			)
			e.add_field(
				name="Причина",
				value=reason,
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Предупреждения пользователя",
				icon_url=ctx.author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)

	@commands.command(
		aliases=["remwarn", "rem-warn"],
		name="remove-warn",
		description="**Снимает указаное предупреждения в участика**",
		usage="remove-warn [Id предупреждения]",
		help="**Примеры использования:**\n1. {Prefix}remove-warn 1\n\n**Пример 1:** Снимает прежупреждения с id - `1`",
	)
	@commands.check(check_role)
	async def rem_warn(self, ctx, warn_id: int):
		data = await self.client.database.del_warn(ctx.guild.id, warn_id)
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if data is None:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Предупреждения с таким айди не существует!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return
		elif data is not None:
			emb = discord.Embed(
				description=f"**Предупреждения успешно было снято с участника** `{ctx.guild.get_member(data[0])}`",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow()
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"У пользователь `{str(ctx.guild.get_member(data[0]))}` было снято предупреждения",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name=f"Модератором {str(ctx.author)}",
				value=f"Id предупреждения - {warn_id}",
				inline=False,
			)
			e.add_field(
				name="Id Участника",
				value=f"`{ctx.guild.get_member(data[0]).id}`",
				inline=False,
			)
			e.set_author(
				name="Журнал аудита | Снятий предупреждения пользователя",
				icon_url=ctx.author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)

	@commands.command(
		description="**Показывает список предупреждений**",
		usage="warns |@Участник|",
		help="**Примеры использования:**\n1. {Prefix}warns @Участник\n2. {Prefix}warns 660110922865704980\n\n**Пример 1:** Показывает предупреждения указаного участника\n**Пример 2:** Показывает предупреждения участника с указаным id",
	)
	async def warns(self, ctx, member: discord.Member = None):
		if member is None:
			member = ctx.author

		if member.bot:
			emb = await ctx.bot.utils.create_error_embed(
				ctx, "Вы не можете просмотреть предупреждения бота!"
			)
			await ctx.send(embed=emb)
			return

		data = await self.client.database.sel_user(target=member)
		warns = data["warns"]

		if warns == []:
			emb = discord.Embed(
				title=f"Предупреждения пользователя - `{member}`",
				description="Список предупреждений пуст.",
				colour=discord.Color.green(),
			)
		else:
			emb = discord.Embed(
				title=f"Предупреждения пользователя - `{member}`",
				colour=discord.Color.green(),
			)

		for warn in warns:
			id_warn = warn["id"]
			time_warn = warn["time"]
			author_warn = str(ctx.guild.get_member(warn["author"]))
			reason = warn["reason"]
			state = warn["state"]

			if state:
				emb.add_field(
					value=f"**Причина:** {reason}",
					name=f"Id - {id_warn}, время - {time_warn}, автор - {author_warn}",
					inline=False,
				)
			elif not state:
				emb.add_field(
					value=f"~~**Причина:** {reason}~~",
					name=f"Не активный - |Id - {id_warn}, время - {time_warn}, автор - {author_warn}|",
					inline=False,
				)

		emb.set_author(name=member.name, icon_url=member.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)


def setup(client):
	client.add_cog(Moderate(client))
