import discord
import datetime
import humanize
from discord.ext import commands
from dateutil.relativedelta import relativedelta
from tools.time_converter import TimeConverter
from discord.utils import get


class SupportCommands:
	def __init__(self, client):
		self.client = client
		self.MUTE_ROLE = self.client.config.MUTE_ROLE
		self.VMUTE_ROLE = self.client.config.VMUTE_ROLE
		self.SOFTBAN_ROLE = self.client.config.SOFTBAN_ROLE
		self.FOOTER = self.client.config.FOOTER_TEXT
		self.time_converter = TimeConverter()

	async def mute(self, ctx, member: discord.Member, author: discord.Member, expiry_in: relativedelta, reason: str):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]
		delta = None
		if expiry_in is not None:
			delta = humanize.naturaldelta(
				self.client.utils.relativedelta_to_timedelta(expiry_in)
			)

		role = get(ctx.guild.roles, name=self.MUTE_ROLE)
		if role is None:
			role = await ctx.guild.create_role(name=self.MUTE_ROLE)

		if role in member.roles:
			emb = await self.client.utils.create_error_embed(
				ctx, "Указаный пользователь уже замьючен!"
			)
			await ctx.send(embed=emb)
			return

		overwrite = discord.PermissionOverwrite(send_messages=False)
		await member.add_roles(role)
		for channel in ctx.guild.text_channels:
			await channel.set_permissions(role, overwrite=overwrite)

		description_time = delta if delta is not None else "Перманентно"
		emb = discord.Embed(
			description=f"**{member}**({member.mention}) Был замьючен\nВремя: `{description_time}`\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были замьчены на сервере\nСервер: `{ctx.guild.name}`\nВремя: `{description_time}`\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass

		if expiry_in is not None:
			await self.client.database.set_punishment(
				type_punishment="mute",
				time=self.client.utils.relativedelta_to_timestamp(expiry_in),
				member=member,
				role_id=int(role.id),
				reason=reason,
				author=author.id,
			)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"Пользователь `{str(member)}` был замьючен",
				colour=discord.Color.teal(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name=f"Модератором {str(author)}",
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
				name="Журнал аудита | Мьют пользователя", icon_url=author.avatar_url
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)

	async def warn(self, ctx, member: discord.Member, author: discord.Member, reason: str):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]
		guild_settings = await self.client.database.sel_guild(guild=ctx.guild)
		max_warns = int(guild_settings["warns_settings"]["max"])
		warn_punishment = guild_settings["warns_settings"]["punishment"]
		cur_warns = (await self.client.database.sel_user(target=member))["warns"]

		warn_id = await self.client.database.set_warn(
			target=member,
			reason=reason,
			author=author.id,
		)

		if len(cur_warns) >= 20:
			await self.client.database.del_warn(
				warn_id=[warn for warn in cur_warns if not warn["state"]][0]["id"]
			)

		if len([warn for warn in cur_warns if warn["state"]]) >= max_warns:
			if warn_punishment is not None:
				expiry_in = None
				if warn_punishment["time"] is not None:
					try:
						expiry_in = await self.time_converter.convert(
							ctx, warn_punishment["time"]
						)
					except commands.BadArgument:
						pass

				if warn_punishment["type"] == "mute":
					await self.mute(
						ctx=ctx,
						member=member,
						expiry_in=expiry_in,
						reason=reason,
						author=author,
					)
				elif warn_punishment["type"] == "kick":
					await self.client.support_commands.kick(
						ctx=ctx,
						member=member,
						author=author,
						reason=reason
					)
				elif warn_punishment["type"] == "ban":
					await self.ban(
						ctx=ctx,
						member=member,
						expiry_in=expiry_in,
						reason=reason,
						author=author,
					)
				elif warn_punishment["type"] == "soft-ban":
					await self.soft_ban(
						ctx=ctx,
						member=member,
						author=author,
						expiry_in=expiry_in,
						reason=reason
					)

			emb = discord.Embed(
				description=f"**{member}**({member.mention}) Достиг максимальное количество предупреждений и получил наказания\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns)+1}`\nМодератор: `{author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow()
			)
			emb.set_author(name=author.name, icon_url=author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			emb = discord.Embed(
				description=f"Вы достигли максимальное количество предупреждений и получили наказания\nСервер: `{ctx.guild.name}`\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns)+1}`\nМодератор: `{author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow()
			)
			emb.set_author(name=author.name, icon_url=author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			try:
				await member.send(embed=emb)
			except:
				pass

			for warn_id in [warn["id"] for warn in cur_warns]:
				await self.client.database.del_warn(warn_id)
		else:
			emb = discord.Embed(
				description=f"**{member}**({member.mention}) Получил предупреждения\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns)+1}`\nМодератор: `{author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow()
			)
			emb.set_author(name=author.name, icon_url=author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			emb = discord.Embed(
				description=f"Вы получили предупреждения на сервере\nСервер: `{ctx.guild.name}`\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns)+1}`\nМодератор: `{author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow()
			)
			emb.set_author(name=author.name, icon_url=author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			try:
				await member.send(embed=emb)
			except:
				pass

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"Пользователь `{str(member)}` получил предупреждения",
				colour=discord.Color.teal(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name=f"Модератором {str(author)}",
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
				icon_url=author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)

	async def ban(self, ctx, member: discord.Member, author: discord.Member, expiry_in: relativedelta, reason: str):
		await member.ban(reason=reason)
		emb = discord.Embed(
			description=f"**{member}**(`{member.id}`) Был забанен\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были забанены на сервере\nСервер: `{ctx.guild.name}`\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass

		if expiry_in is not None:
			await self.client.database.set_punishment(
				type_punishment="ban",
				time=self.client.utils.relativedelta_to_timestamp(expiry_in),
				member=member
			)

	async def soft_ban(self, ctx, member: discord.Member, author: discord.Member, expiry_in: relativedelta, reason: str):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]
		delta = None
		if expiry_in is not None:
			delta = humanize.naturaldelta(
				self.client.utils.relativedelta_to_timedelta(expiry_in)
			)

		emb = discord.Embed(
			description=f"**{member}**({member.mention}) Был апаратно забанен\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были апаратно забанены на сервере\nСервер: `{ctx.guild.name}`\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
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

		if expiry_in is not None:
			await self.client.database.set_punishment(
				type_punishment="temprole",
				time=self.client.utils.relativedelta_to_timestamp(expiry_in),
				member=member,
				role=role.id
			)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"Пользователь `{str(member)}` был апаратно забанен",
				colour=discord.Color.red(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name=f"Модератором {str(author)}",
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
				name="Журнал аудита | Апаратный бан пользователя",
				icon_url=author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)

	async def kick(self, ctx, member: discord.Member, author: discord.Member, reason: str):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]
		await member.kick(reason=reason)

		emb = discord.Embed(
			description=f"**{member}**({member.mention}) Был выгнан\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были выгнаны с сервера\nСервер: `{ctx.guild.name}`\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow()
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
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
				value=str(author),
				inline=False,
			)
			e.add_field(
				name="Причина",
				value=reason,
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Кик пользователя", icon_url=author.avatar_url
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["moderate"])
			if channel is not None:
				await channel.send(embed=e)
