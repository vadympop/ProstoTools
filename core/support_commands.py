import discord
import datetime
import humanize
from core.utils.other import process_converters
from core.converters import Expiry
from discord.utils import get


class SupportCommands:
	def __init__(self, client):
		self.client = client
		self.MUTE_ROLE = self.client.config.MUTE_ROLE
		self.VMUTE_ROLE = self.client.config.VMUTE_ROLE
		self.SOFTBAN_ROLE = self.client.config.SOFTBAN_ROLE
		self.FOOTER = self.client.config.FOOTER_TEXT

	async def mute(self, ctx, member: discord.Member, author: discord.Member, expiry_at: datetime.datetime, reason: str):
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit
		guild_time = await self.client.utils.get_guild_time(ctx.guild)
		delta = None
		if expiry_at is not None:
			delta = humanize.naturaldelta(
				expiry_at+datetime.timedelta(seconds=1),
				when=guild_time
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
			description=f"**{member}**({member.mention}) Был замьючен\nДлительность: `{description_time}`\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=guild_time
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были замьчены на сервере\nСервер: `{ctx.guild.name}`\nДлительность: `{description_time}`\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=guild_time
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass

		if expiry_at is not None:
			await self.client.database.add_punishment(
				type_punishment="mute",
				time=expiry_at.timestamp(),
				member=member,
				role_id=int(role.id),
				reason=reason,
				author=author.id,
			)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"Пользователь `{str(member)}` был замьючен",
				colour=discord.Color.teal(),
				timestamp=guild_time
			)
			e.add_field(
				name=f"Модератором {str(author)}",
				value=f"Длительность: {delta}"
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
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit
		guild_time = await self.client.utils.get_guild_time(ctx.guild)
		guild_settings = await self.client.database.sel_guild(guild=ctx.guild)
		max_warns = int(guild_settings.warns_settings["max"])
		warn_punishment = guild_settings.warns_settings["punishment"]
		cur_warns = await self.client.database.get_warns(user_id=member.id, guild_id=ctx.guild.id)

		warn_id = await self.client.database.add_warn(
			user_id=member.id,
			guild_id=ctx.guild.id,
			reason=reason,
			author=author.id,
		)

		if len(cur_warns) >= 20:
			await self.client.database.del_warn(
				warn_id=[warn for warn in cur_warns if not warn.state][0].id
			)

		if len([warn for warn in cur_warns if warn["state"]]) >= max_warns:
			if warn_punishment is not None:
				expiry_at = None
				if warn_punishment["time"] is not None:
					expiry_at = await process_converters(
						ctx, Expiry.__args__, warn_punishment["time"]
					)

				if warn_punishment["type"] == "mute":
					await self.mute(
						ctx=ctx,
						member=member,
						expiry_at=expiry_at,
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
						expiry_at=expiry_at,
						reason=reason,
						author=author,
					)
				elif warn_punishment["type"] == "soft-ban":
					await self.soft_ban(
						ctx=ctx,
						member=member,
						author=author,
						expiry_at=expiry_at,
						reason=reason
					)

			emb = discord.Embed(
				description=f"**{member}**({member.mention}) Достиг максимальное количество предупреждений и получил наказания\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns)+1}`\nМодератор: `{author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=guild_time
			)
			emb.set_author(name=author.name, icon_url=author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			emb = discord.Embed(
				description=f"Вы достигли максимальное количество предупреждений и получили наказания\nСервер: `{ctx.guild.name}`\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns)+1}`\nМодератор: `{author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=guild_time
			)
			emb.set_author(name=author.name, icon_url=author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			try:
				await member.send(embed=emb)
			except:
				pass

			await self.client.database.del_warns(user_id=member.id, guild_id=ctx.guild.id)
		else:
			emb = discord.Embed(
				description=f"**{member}**({member.mention}) Получил предупреждения\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns)+1}`\nМодератор: `{author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=guild_time
			)
			emb.set_author(name=author.name, icon_url=author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			emb = discord.Embed(
				description=f"Вы получили предупреждения на сервере\nСервер: `{ctx.guild.name}`\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns)+1}`\nМодератор: `{author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=guild_time
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
				timestamp=guild_time
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

	async def ban(self, ctx, member: discord.Member, author: discord.Member, expiry_at: datetime.datetime, reason: str):
		guild_time = await self.client.utils.get_guild_time(ctx.guild)
		await member.ban(reason=reason)
		emb = discord.Embed(
			description=f"**{member}**(`{member.id}`) Был забанен\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=guild_time
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были забанены на сервере\nСервер: `{ctx.guild.name}`\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=guild_time
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass

		if expiry_at is not None:
			await self.client.database.add_punishment(
				type_punishment="ban",
				time=expiry_at.timestamp(),
				member=member
			)

	async def soft_ban(self, ctx, member: discord.Member, author: discord.Member, expiry_at: datetime.datetime, reason: str):
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit
		guild_time = await self.client.utils.get_guild_time(ctx.guild)
		delta = None
		if expiry_at is not None:
			delta = humanize.naturaldelta(
				expiry_at+datetime.timedelta(seconds=1),
				when=guild_time
			)

		emb = discord.Embed(
			description=f"**{member}**({member.mention}) Был апаратно забанен\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=guild_time
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были апаратно забанены на сервере\nСервер: `{ctx.guild.name}`\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=guild_time
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

		if expiry_at is not None:
			await self.client.database.add_punishment(
				type_punishment="temprole",
				time=expiry_at.timestamp(),
				member=member,
				role=role.id
			)

		if "moderate" in audit.keys():
			e = discord.Embed(
				description=f"Пользователь `{str(member)}` был апаратно забанен",
				colour=discord.Color.red(),
				timestamp=guild_time
			)
			e.add_field(
				name=f"Модератором {str(author)}",
				value=f"Длительность: {delta}"
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
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit
		guild_time = await self.client.utils.get_guild_time(ctx.guild)
		await member.kick(reason=reason)

		emb = discord.Embed(
			description=f"**{member}**({member.mention}) Был выгнан\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=guild_time
		)
		emb.set_author(name=author.name, icon_url=author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"Вы были выгнаны с сервера\nСервер: `{ctx.guild.name}`\nМодератор: `{author}`\nПричина: **{reason}**",
			colour=discord.Color.green(),
			timestamp=guild_time
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
				timestamp=guild_time
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
