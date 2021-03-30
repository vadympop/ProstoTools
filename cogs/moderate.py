import discord
import typing
import datetime
import humanize

from core.utils.other import check_filters
from core.bases.cog_base import BaseCog
from core.utils.other import process_converters, check_moderate_roles
from core.converters import Expiry, TargetUser
from core import Paginator
from discord.ext import commands
from discord.utils import get


class Moderate(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.MUTE_ROLE = self.client.config.MUTE_ROLE
		self.VMUTE_ROLE = self.client.config.VMUTE_ROLE
		self.SOFTBAN_ROLE = self.client.config.SOFTBAN_ROLE
		self.FILTERS = self.client.config.FILTERS
		self.FILTERS_PREDICATES = self.client.config.MESSAGES_FILTERS_PREDICATES

	@commands.command(
		description="Удаляет указаное число сообщений",
		usage="clear |@Участник| [Число удаляемых сообщений]",
		help="**Полезное:**\nМаксимальное число удаляемых сообщений равняется 100\nБот не может удалить сообщения старше 14 дней\n\n**Примеры использования:**\n1. {Prefix}clear 10\n2. {Prefix}clear @Участник 10\n3. {Prefix}clear 660110922865704980 10\n\n**Пример 1:** Удалит 10 сообщений\n**Пример 2:** Удалит 10 сообщений упомянотого участника в текущем канале\n**Пример 3:** Удалит 10 сообщений участника с указаным id",
	)
	@commands.bot_has_permissions(manage_messages=True)
	@commands.check(check_moderate_roles)
	async def clear(self, ctx, member: typing.Optional[discord.Member], amount: int, *args):
		if amount <= 0:
			emb = await self.client.utils.create_error_embed(ctx, "Укажите число удаляемых сообщения больше 0!")
			await ctx.send(embed=emb)
			return

		if amount >= 100:
			emb = await self.client.utils.create_error_embed(ctx, "Укажите число удаляемых сообщения меньше 100!")
			await ctx.send(embed=emb)
			return

		number = 0
		delete_messages_objs = []
		filters = [arg for arg in args if arg in self.FILTERS]
		if member is None:
			async with ctx.typing():
				num_channel_messages = len(await ctx.channel.history().filter(
					lambda m: check_filters(m, filters, self.FILTERS_PREDICATES)
				).flatten())
				async for msg in ctx.channel.history().filter(
						lambda m: check_filters(m, filters, self.FILTERS_PREDICATES)
				):
					if (await self.client.utils.get_guild_time(ctx.guild)-msg.created_at) >= datetime.timedelta(weeks=2):
						emb = await self.client.utils.create_error_embed(
							ctx, "Я не могу удалить сообщения старше 14 дней!"
						)
						await ctx.send(embed=emb)
						return

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
						break
		elif member is not None and member in ctx.guild.members:
			async with ctx.typing():
				async for msg in ctx.channel.history().filter(
						lambda m: m.author == member and all([self.FILTERS_PREDICATES[i](m) for i in filters])
				):
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
		description="Дает указанную роль учаснику на время",
		usage="temp-role [@Участник] [@Роль] [Длительность]",
		help="**Примеры использования:**\n1. {Prefix}temp-role @Участник @Роль 10m\n2. {Prefix}temp-role 660110922865704980 717776604461531146 10m\n3. {Prefix}temp-role @Участник 717776604461531146 10m\n4. {Prefix}temp-role 660110922865704980 @Роль 10m\n\n**Пример 1:** Даёт упомянутую роль упомянутому участнику\n**Пример 2:** Даёт роль с указаным id участнику с указаным id\n**Пример 3:** Даёт роль с указаным id упомянутому участнику\n**Пример 4:** Даёт упомянутую роль участнику с указаным id",
	)
	@commands.check(check_moderate_roles)
	@commands.bot_has_permissions(manage_roles=True)
	async def temprole(self, ctx, member: discord.Member, role: discord.Role, expiry_at: Expiry):
		if member == ctx.author:
			emb = await self.client.utils.create_error_embed(
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
			emb = await self.client.utils.create_error_embed(
				ctx, "Указаная роль выше моей роли!"
			)
			await ctx.send(embed=emb)
			return

		if ctx.author.top_role <= role and ctx.author != ctx.guild.owner:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете выдать роль которая выше вашей роли!"
			)
			await ctx.send(embed=emb)
			return

		guild_time = await self.client.utils.get_guild_time(ctx.guild)
		await member.add_roles(role)
		delta = humanize.naturaldelta(
			expiry_at+datetime.timedelta(seconds=1),
			when=guild_time
		)
		emb = discord.Embed(
			description=f"**{member}**({member.mention}) Была виданна роль\nРоль: `{role.name}`\nДлительность: `{delta}`",
			colour=discord.Color.green(),
			timestamp=guild_time
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		await self.client.database.add_punishment(
			type_punishment="temprole",
			time=expiry_at.timestamp(),
			member=member,
			role_id=int(role.id),
		)

	@commands.command(
		aliases=["slowmode"],
		name="slow-mode",
		description="Ставит медленный режим указанному каналу",
		usage="slow-mode [Время] |Канал|",
		help="**Примеры использования:**\n1. {Prefix}slow-mode 10 #Канал\n2. {Prefix}slow-mode 10 717776571406090313\n\n**Пример 1:** Ставит упомянутому канала медленный режим на 10 секунд\n**Пример 2:** Ставит каналу с указаным id медленный режим на 10 секунд",
	)
	@commands.check(check_moderate_roles)
	@commands.bot_has_permissions(manage_channels=True)
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
					description=f"**Для всех каналов этого сервера был поставлен медленный режим на {delay}сек**",
					colour=discord.Color.green(),
				)
			elif delay == 0:
				emb = discord.Embed(
					description=f"**Для всех каналов этого сервера был снят медленный режим**",
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
					description=f"**Для канала {slowmode_channel.name} был поставлен медленный режим на {delay}сек**",
					colour=discord.Color.green(),
				)
			elif delay == 0:
				emb = discord.Embed(
					description=f"**Для канала {slowmode_channel.name} был снят медленный**",
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
		description="Кикает учасника из сервера",
		usage="kick [@Участник] |Причина|",
		help="**Примеры использования:**\n1. {Prefix}kick @Участник Нарушения правил сервера\n2. {Prefix}kick 660110922865704980 Нарушения правил сервера\n3. {Prefix}kick @Участник\n4. {Prefix}kick 660110922865704980\n\n**Пример 1:** Кикает с сервера упомянутого участника по причине `Нарушения правил сервера`\n**Пример 2:** Кикает с сервера участника с указаным id по причине `Нарушения правил сервера`\n**Пример 3:** Кикает с сервера упомянутого участника без причины\n**Пример 4:** Кикает с сервера участника с указаным id без причины",
	)
	@commands.check(check_moderate_roles)
	@commands.bot_has_permissions(kick_members=True)
	async def kick(self, ctx, member: TargetUser, *, reason: str = "Причина не указана"):
		await self.client.support_commands.kick(
			ctx=ctx,
			member=member,
			author=ctx.author,
			reason=reason[:1024]
		)

	@commands.command(
		aliases=["softban"],
		name="soft-ban",
		description="Апаратно банит указанного участника - участник имеет доступ к серверу, но к каналам доступа нет",
		usage="soft-ban [@Участник] |Длительность| |Причина|",
		help="**Полезное:**\n\n**Примеры использования:**\n1. {Prefix}soft-ban @Участник 10d Нарушения правил сервера\n2. {Prefix}soft-ban 660110922865704980 10d Нарушения правил сервера\n3. {Prefix}soft-ban @Участник 10d\n4. {Prefix}soft-ban 660110922865704980 10d\n5. {Prefix}soft-ban @Участник\n6. {Prefix}soft-ban 660110922865704980\n7. {Prefix}soft-ban @Участник Нарушения правил сервера\n8. {Prefix}soft-ban 660110922865704980 Нарушения правил сервера\n\n**Пример 1:** Апапаратно банит упомянутого участника по причине `Нарушения правил сервера` на 10 дней\n**Пример 2:** Апапаратно банит участника с указаным id по причине\n`Нарушения правил сервера` на 10 дней\n**Пример 3:** Апапаратно банит упомянутого участника без причины на 10 дней\n**Пример 4:** Апапаратно банит участника с указаным id без причины на 10 дней\n**Пример 5:** Даёт перманентный апапаратный бан упомянутому участнику без причины\n**Пример 6:** Даёт перманентный апапаратный бан участнику с указаным id без причины\n**Пример 7:** Даёт перманентный апапаратный бан упомянутому участнику по причине\n`Нарушения правил сервера`\n**Пример 8:** Даёт апапаратный апапаратный бан участнику с указаным id по причине\n`Нарушения правил сервера`",
	)
	@commands.check(check_moderate_roles)
	@commands.bot_has_permissions(manage_roles=True)
	async def soft_ban(self, ctx, member: TargetUser, *options: str):
		options = list(options)
		expiry_at = None
		if len(options) > 0:
			try:
				expiry_at = await process_converters(ctx, Expiry.__args__, options[0], True)
				options.pop(0)
				reason = " ".join(options) if len(options) > 0 else "Причина не указана"
			except commands.BadArgument:
				reason = " ".join(options)
		else:
			reason = "Причина не указана"

		await self.client.support_commands.soft_ban(
			ctx=ctx,
			member=member,
			author=ctx.author,
			expiry_at=expiry_at,
			reason=reason[:1024]
		)

	@commands.command(
		aliases=["unsoftban"],
		name="unsoft-ban",
		description="Снимает апаратный с указаного участника",
		usage="unsoft-ban [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}unsoft-ban @Участник\n2. {Prefix}unsoft-ban 660110922865704980\n\n**Пример 1:** Снимает апаратный бан с упомянутого участника\n**Пример 2:** Снимает апаратный бан с участника с указаным id",
	)
	@commands.check(check_moderate_roles)
	@commands.bot_has_permissions(manage_roles=True)
	async def unsoftban(self, ctx, member: TargetUser):
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit
		guild_time = await self.client.utils.get_guild_time(ctx.guild)

		emb = discord.Embed(
			description=f"`{ctx.author}` **Снял апаратный бан с** `{member}`({member.mention})",
			colour=discord.Color.green(),
			timestamp=guild_time
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"**С вас был снят апаратный бан на сервере** `{ctx.guild.name}`",
			colour=discord.Color.green(),
			timestamp=guild_time
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
				timestamp=guild_time
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
		description="Банит учасника по указанной причине",
		usage="ban [@Участник] |Длительность| |Причина|",
		help="**Примеры использования:**\n1. {Prefix}ban @Участник 10d Нарушения правил сервера\n2. {Prefix}ban 660110922865704980 10d Нарушения правил сервера\n3. {Prefix}ban @Участник 10d\n4. {Prefix}ban 660110922865704980 10d\n5. {Prefix}ban @Участник\n6. {Prefix}ban 660110922865704980\n7. {Prefix}ban @Участник Нарушения правил сервера\n8. {Prefix}ban 660110922865704980 Нарушения правил сервера\n\n**Пример 1:** Банит упомянутого участника по причине `Нарушения правил сервера` на 10 дней\n**Пример 2:** Банит участника с указаным id по причине\n`Нарушения правил сервера` на 10 дней\n**Пример 3:** Банит упомянутого участника без причины на 10 дней\n**Пример 4:** Банит участника с указаным id без причины на 10 дней\n**Пример 5:** Перманентно банит упомянутого участника без причины\n**Пример 6:** Перманентно банит участника с указаным id без причины\n**Пример 7:** Перманентно банит упомянутого участника по причине\n`Нарушения правил сервера`\n**Пример 8:** Перманентно банит участника с указаным id по причине\n`Нарушения правил сервера`",
	)
	@commands.check(check_moderate_roles)
	@commands.bot_has_permissions(ban_members=True)
	async def ban(self, ctx, member: TargetUser, *options: str):
		options = list(options)
		expiry_at = None
		if len(options) > 0:
			try:
				expiry_at = await process_converters(ctx, Expiry.__args__, options[0], True)
				options.pop(0)
				reason = " ".join(options) if len(options) > 0 else "Причина не указана"
			except commands.BadArgument:
				reason = " ".join(options)
		else:
			reason = "Причина не указана"

		await self.client.support_commands.ban(
			ctx=ctx,
			member=member,
			author=ctx.author,
			expiry_at=expiry_at,
			reason=reason[:1024]
		)

	@commands.command(
		aliases=["unban"],
		name="un-ban",
		description="Снимает бан из указанного учасника",
		usage="un-ban [@Пользователь]",
		help="**Примеры использования:**\n1. {Prefix}un-ban @Ник+тэг\n2. {Prefix}un-ban 660110922865704980\n\n**Пример 1:** Разбанит указаного пользователя\n**Пример 2:** Разбанит пользователя с указаным id",
	)
	@commands.check(check_moderate_roles)
	@commands.bot_has_permissions(ban_members=True)
	async def unban(self, ctx, *, member: TargetUser):
		async with ctx.typing():
			banned_users = await ctx.guild.bans()
			state = False
			for ban_entry in banned_users:
				user = ban_entry.user

				if user.id == member.id:
					state = True
					guild_time = await self.client.utils.get_guild_time(ctx.guild)
					await ctx.guild.unban(user)
					await self.client.database.del_punishment(
						member=member, guild_id=ctx.guild.id, type_punishment="ban"
					)

					emb = discord.Embed(
						description=f"`{ctx.author}` **Разбанил** `{member}`({member.mention})",
						colour=discord.Color.green(),
						timestamp=guild_time
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await ctx.send(embed=emb)

					emb = discord.Embed(
						description=f"**Вы были разбанены на сервере** `{ctx.guild.name}`",
						colour=discord.Color.green(),
						timestamp=guild_time
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
		description="Мьютит указанного участника в голосовых каналах",
		usage="vmute [@Участник] |Длительность| |Причина|",
		help="**Примеры использования:**\n1. {Prefix}vmute @Участник 10d Нарушения правил сервера\n2. {Prefix}vmute 660110922865704980 10d Нарушения правил сервера\n3. {Prefix}vmute @Участник 10d\n4. {Prefix}vmute 660110922865704980 10d\n5. {Prefix}vmute @Участник\n6. {Prefix}vmute 660110922865704980\n7. {Prefix}vmute @Участник Нарушения правил сервера\n8. {Prefix}vmute 660110922865704980 Нарушения правил сервера\n\n**Пример 1:** Мьютит упомянутого участника в голосовых каналах по причине `Нарушения правил сервера` на 10 дней\n**Пример 2:** Мьютит участника с указаным id в голосовых каналах по причине\n`Нарушения правил сервера` на 10 дней\n**Пример 3:** Мьютит упомянутого участника в голосовых каналах без причины на 10 дней\n**Пример 4:** Мьютит участника с указаным id в голосовых каналах без причины на 10 дней\n**Пример 5:** Перманентно мьютит упомянутого участника в голосовых каналах без причины\n**Пример 6:** Перманентно мьютит участника с указаным id в голосовых каналах без причины\n**Пример 7:** Перманентно мьютит упомянутого участника в голосовых каналах по причине\n`Нарушения правил сервера`\n**Пример 8:** Перманентно мьютит участника с указаным id в голосовых каналах по причине\n`Нарушения правил сервера`",
	)
	@commands.bot_has_permissions(manage_roles=True)
	@commands.check(check_moderate_roles)
	async def vmute(self, ctx, member: TargetUser, *options: str):
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit
		guild_time = await self.client.utils.get_guild_time(ctx.guild)
		options = list(options)
		expiry_at = None
		if len(options) > 0:
			try:
				expiry_at = await process_converters(ctx, Expiry.__args__, options[0], True)
				options.pop(0)
				reason = " ".join(options) if len(options) > 0 else "Причина не указана"
			except commands.BadArgument:
				reason = " ".join(options)
		else:
			reason = "Причина не указана"

		delta = None
		if expiry_at is not None:
			delta = humanize.naturaldelta(
				expiry_at+datetime.timedelta(seconds=1),
				when=guild_time
			)

		reason = reason[:1024]
		overwrite = discord.PermissionOverwrite(connect=False)
		role = get(ctx.guild.roles, name=self.VMUTE_ROLE)

		if role is None:
			role = await ctx.guild.create_role(name=self.VMUTE_ROLE)
		for channel in ctx.guild.voice_channels:
			await channel.set_permissions(role, overwrite=overwrite)

		await member.add_roles(role)
		await member.edit(voice_channel=None)

		description_time = delta if delta is not None else "Перманентно"
		emb = discord.Embed(
			description=f"**{member}**({member.mention}) Был замьючен в голосовых каналах\nДлительность: `{description_time}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=guild_time
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были замьчены в голосовых каналах на сервере\nСервер: `{ctx.guild.name}`\nДлительность: `{description_time}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=guild_time
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass

		if expiry_at is not None:
			await self.client.database.add_punishment(
				type_punishment="vmute",
				time=expiry_at.timestamp(),
				member=member,
				role_id=int(role.id)
			)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"Пользователь `{str(member)}` был замьючен в голосовых каналах",
				colour=discord.Color.teal(),
				timestamp=guild_time
			)
			e.add_field(
				name=f"Модератором {str(ctx.author)}",
				value=f"На {delta}"
				if delta is not None
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
		description="Снимает мьют с указанного участника в голосовых каналах",
		usage="un-vmute [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}un-vmute @Участник\n2. {Prefix}un-vmute 660110922865704980\n\n**Пример 1:** Размьютит указаного участника в голосовых каналах\n**Пример 2:** Размьютит участника с указаным id в голосовых каналах",
	)
	@commands.check(check_moderate_roles)
	@commands.bot_has_permissions(manage_roles=True)
	async def unvmute(self, ctx, member: TargetUser):
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit
		for vmute_role in ctx.guild.roles:
			if vmute_role.name == self.VMUTE_ROLE:
				guild_time = await self.client.utils.get_guild_time(ctx.guild)
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
					timestamp=guild_time
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)

				emb = discord.Embed(
					description=f"**Вы были размьючены в голосовых каналах на сервере** `{ctx.guild.name}`",
					colour=discord.Color.green(),
					timestamp=guild_time
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
						timestamp=guild_time
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
		description="Мютит учасника по указанной причине",
		usage="mute [@Участник] |Длительность| |Причина|",
		help="**Примеры использования:**\n1. {Prefix}mute @Участник 10d Нарушения правил сервера\n2. {Prefix}mute 660110922865704980 10d Нарушения правил сервера\n3. {Prefix}mute @Участник 10d\n4. {Prefix}mute 660110922865704980 10d\n5. {Prefix}mute @Участник\n6. {Prefix}mute 660110922865704980\n7. {Prefix}mute @Участник Нарушения правил сервера\n8. {Prefix}mute 660110922865704980 Нарушения правил сервера\n\n**Пример 1:** Мьютит упомянутого участника по причине `Нарушения правил сервера` на 10 дней\n**Пример 2:** Мьютит участника с указаным id по причине\n`Нарушения правил сервера` на 10 дней\n**Пример 3:** Мьютит упомянутого участника без причины на 10 дней\n**Пример 4:** Мьютит участника с указаным id без причины на 10 дней\n**Пример 5:** Перманентно мьютит упомянутого участника без причины\n**Пример 6:** Перманентно мьютит участника с указаным id без причины\n**Пример 7:** Перманентно мьютит упомянутого участника по причине\n`Нарушения правил сервера`\n**Пример 8:** Перманентно мьютит участника с указаным id по причине\n`Нарушения правил сервера`",
	)
	@commands.check(check_moderate_roles)
	@commands.bot_has_permissions(manage_roles=True)
	async def mute(self, ctx, member: TargetUser, *options: str):
		options = list(options)
		expiry_at = None
		if len(options) > 0:
			try:
				expiry_at = await process_converters(ctx, Expiry.__args__, options[0], True)
				options.pop(0)
				reason = " ".join(options) if len(options) > 0 else "Причина не указана"
			except commands.BadArgument:
				reason = " ".join(options)
		else:
			reason = "Причина не указана"

		await self.client.support_commands.mute(
			ctx=ctx,
			member=member,
			author=ctx.author,
			expiry_at=expiry_at,
			reason=reason[:1024]
		)

	@commands.command(
		aliases=["unmute"],
		name="un-mute",
		description="Размьютит указанного учасника",
		usage="un-mute [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}un-mute @Участник\n2. {Prefix}un-mute 660110922865704980\n\n**Пример 1:** Размьютит указаного участника\n**Пример 2:** Размьютит участника с указаным id",
	)
	@commands.check(check_moderate_roles)
	@commands.bot_has_permissions(manage_roles=True)
	async def unmute(self, ctx, member: TargetUser):
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit
		for role in ctx.guild.roles:
			if role.name == self.MUTE_ROLE:
				guild_time = await self.client.utils.get_guild_time(ctx.guild)
				await self.client.database.del_punishment(
					member=member, guild_id=ctx.guild.id, type_punishment="mute"
				)
				await member.remove_roles(role)

				emb = discord.Embed(
					description=f"`{ctx.author}` **Размьютил** `{member}`({member.mention})",
					colour=discord.Color.green(),
					timestamp=guild_time
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)

				emb = discord.Embed(
					description=f"**Вы были размьючены на сервере** `{ctx.guild.name}`",
					colour=discord.Color.green(),
					timestamp=guild_time
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
						timestamp=guild_time
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
				break

	@commands.command(
		aliases=["clearwarns"],
		name="clear-warns",
		description="Очищает предупреждения в указанного пользователя",
		usage="clear-warns [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}clear-warns @Участник\n2. {Prefix}clear-warns 660110922865704980\n\n**Пример 1:** Очищает все предупреждения указаного участника\n**Пример 2:** Очищает все предупреждения участника с указаным id",
	)
	@commands.check(check_moderate_roles)
	async def clearwarn(self, ctx, member: TargetUser):
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit
		guild_time = await self.client.utils.get_guild_time(ctx.guild)

		async with ctx.typing():
			await self.client.database.del_warns(user_id=member.id, guild_id=ctx.guild.id)

			emb = discord.Embed(
				description=f"**У пользователя** `{member}`({member.mention}) **были сняты предупреждения**",
				colour=discord.Color.green(),
				timestamp=guild_time
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"У пользователя `{str(member)}` были сняты все предупреждения",
				colour=discord.Color.green(),
				timestamp=guild_time
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
		description="Дает придупреждения учаснику по указанной причине",
		usage="warn [@Участник] |Причина|",
		help="**Примеры использования:**\n1. {Prefix}warn @Участник Нарушения правил сервера\n2. {Prefix}warn 660110922865704980 Нарушения правил сервера\n3. {Prefix}warn @Участник\n4. {Prefix}warn 660110922865704980\n\n**Пример 1:** Даёт предупреждения упомянутого участнику по причине `Нарушения правил сервера`\n**Пример 2:** Даёт предупреждения участнику с указаным id по причине\n`Нарушения правил сервера`\n**Пример 3:** Даёт предупреждения упомянутого участнику без причины\n**Пример 4:** Даёт предупреждения участнику с указаным id без причины",
	)
	@commands.check(check_moderate_roles)
	async def warn(self, ctx, member: TargetUser, *, reason: str = "Причина не указана"):
		if member.bot:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете дать предупреждения боту!"
			)
			await ctx.send(embed=emb)
			return

		await self.client.support_commands.warn(
			ctx=ctx,
			member=member,
			author=ctx.author,
			reason=reason[:1024]
		)

	@commands.command(
		aliases=["remwarn", "rem-warn"],
		name="remove-warn",
		description="Снимает указанное предупреждения в участника",
		usage="remove-warn [Id предупреждения]",
		help="**Примеры использования:**\n1. {Prefix}remove-warn 1\n\n**Пример 1:** Снимает прежупреждения с id - `1`",
	)
	@commands.check(check_moderate_roles)
	async def rem_warn(self, ctx, warn_id: int):
		data = await self.client.database.del_warn(warn_id)
		guild_time = await self.client.utils.get_guild_time(ctx.guild)
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit

		if data is None:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Предупреждения с таким айди не существует!**"
			)
			await ctx.send(embed=emb)
			return

		member = ctx.guild.get_member(data.user_id)
		emb = discord.Embed(
			description=f"**Предупреждения успешно было снято с участника** `{member}`",
			colour=discord.Color.green(),
			timestamp=guild_time
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"У пользователя `{member}` было снято предупреждения",
				colour=discord.Color.green(),
				timestamp=guild_time
			)
			e.add_field(
				name=f"Модератором {str(ctx.author)}",
				value=f"Id предупреждения - {warn_id}",
				inline=False,
			)
			e.add_field(
				name="Id Участника",
				value=f"`{member.id}`",
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
		description="Показывает список предупреждений",
		usage="warns |@Участник|",
		help="**Примеры использования:**\n1. {Prefix}warns @Участник\n2. {Prefix}warns 660110922865704980\n\n**Пример 1:** Показывает предупреждения указаного участника\n**Пример 2:** Показывает предупреждения участника с указаным id",
	)
	async def warns(self, ctx, member: discord.Member = None):
		if member is None:
			member = ctx.author

		if member.bot:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете просмотреть предупреждения бота!"
			)
			await ctx.send(embed=emb)
			return

		data = await self.client.database.get_warns(user_id=member.id, guild_id=ctx.guild.id)
		if len(data) > 0:
			embeds = []
			warns = []
			for warn in data:
				warn_time = datetime.datetime.fromtimestamp(warn.time).strftime("%d %B %Y %X")
				author = ctx.guild.get_member(warn.author)
				warn_state = "Да" if warn.state else "Нет"
				text = f"""Активный: **{warn_state}**\nId: `{warn.id}`\nПричина: **{warn.reason[:256]}**\nАвтор: `{author}`\nВремя мьюта: `{warn_time}`"""
				warns.append(text)

			grouped_warns = [warns[x:x + 5] for x in range(0, len(warns), 5)]
			for group in grouped_warns:
				emb = discord.Embed(
					title=f"Предупреждения пользователя - `{member}`",
					description="\n\n".join(group),
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
				title=f"Предупреждения пользователя - `{member}`",
				description="Список предупреждений пуст",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)


def setup(client):
	client.add_cog(Moderate(client))
