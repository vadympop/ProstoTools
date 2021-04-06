import discord
import uuid
import os
import typing

from core.bases.cog_base import BaseCog
from discord.ext import commands


class EventsAudit(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.TEMP_PATH = self.client.config.TEMP_PATH
		self.CHANNEL_TYPES = {
			discord.ChannelType.text: "текстовый канал",
			discord.ChannelType.voice: "голосовый канал",
			discord.ChannelType.category: "канал категория",
			discord.ChannelType.news: "канал новостей",
		}

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		data = await self.client.database.sel_guild(guild=before.guild)

		if not data.audit["member_update"]["state"]:
			return

		channel = self.client.get_channel(data.audit["member_update"]["channel_id"])
		if channel is None:
			return

		if not len(before.roles) == len(after.roles):
			if len(before.roles) > len(after.roles):
				for role in before.roles:
					if role not in after.roles:
						name = "Была убрана роль"
						value = f"@{role}(`{role.id}`)"
			elif len(before.roles) < len(after.roles):
				for role in after.roles:
					if role not in before.roles:
						name = "Была добавлена роль"
						value = f"@{role}(`{role.id}`)"

			e = discord.Embed(
				description=f"У пользователя `{after}` были изменены роли",
				colour=discord.Color.blurple(),
				timestamp=await self.client.utils.get_guild_time(after.guild),
			)
			e.add_field(
				name=name, value=value, inline=False
			)
			e.add_field(name="Id Участника", value=f"`{after.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Изменение ролей участника",
				icon_url=before.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await channel.send(embed=e)

			if data.donate:
				await self.client.database.add_audit_log(
					user=after,
					channel=channel,
					guild_id=after.guild.id,
					action_type="member_roles_update",
					updated_role=value,
					action=name
				)

		if not before.display_name == after.display_name:
			e = discord.Embed(
				description=f"Пользователь `{before}` изменил ник",
				colour=discord.Color.blue(),
				timestamp=await self.client.utils.get_guild_time(after.guild),
			)
			e.add_field(
				name="Действующее имя",
				value=f"`{after}`",
				inline=False,
			)
			e.add_field(
				name="Предыдущее имя",
				value=f"`{before}`",
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{after.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Изменение ника участника",
				icon_url=before.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await channel.send(embed=e)

			if data.donate:
				await self.client.database.add_audit_log(
					user=after,
					channel=channel,
					guild_id=after.guild.id,
					action_type="member_nick_update",
					after_nick=str(after),
					before_nick=str(before)
				)

	@commands.Cog.listener()
	async def on_member_ban(self, guild, user):
		data = await self.client.database.sel_guild(guild=guild)
		if not data.audit["member_ban"]["state"]:
			return

		channel = self.client.get_channel(data.audit["member_ban"]["channel_id"])
		if channel is None:
			return

		ban = await guild.fetch_ban(user)
		e = discord.Embed(
			description=f"Пользователь `{user}` был забанен",
			colour=discord.Color.red(),
			timestamp=await self.client.utils.get_guild_time(guild),
		)
		e.add_field(
			name="Причина бана",
			value=f"""`{'Причина не указана' if not ban.reason else ban.reason}`""",
			inline=False,
		)
		e.add_field(name="Id Участника", value=f"`{user.id}`", inline=False)
		e.set_author(name="Журнал аудита | Бан пользователя", icon_url=user.avatar_url)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

		if data.donate:
			await self.client.database.add_audit_log(
				user=user,
				channel=channel,
				guild_id=guild.id,
				action_type="member_ban",
				ban_reason=ban.reason
			)

	@commands.Cog.listener()
	async def on_member_unban(self, guild, user):
		if user.bot:
			return

		data = await self.client.database.sel_guild(guild=guild)
		if not data.audit["member_unban"]["state"]:
			return

		channel = self.client.get_channel(data.audit["member_unban"]["channel_id"])
		if channel is None:
			return

		e = discord.Embed(
			description=f"Пользователь `{user}` был разбанен",
			colour=discord.Color.green(),
			timestamp=await self.client.utils.get_guild_time(guild),
		)
		e.add_field(name="Id Участника", value=f"`{user.id}`", inline=False)
		e.set_author(
			name="Журнал аудита | Разбан пользователя", icon_url=user.avatar_url
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

		if data.donate:
			await self.client.database.add_audit_log(
				user=user,
				channel=channel,
				guild_id=guild.id,
				action_type="member_unban",
			)

	@commands.Cog.listener()
	async def on_raw_bulk_message_delete(self, payload):
		guild = self.client.get_guild(payload.guild_id)
		audit = (await self.client.database.sel_guild(guild=guild)).audit
		if not audit["message_delete"]["state"]:
			return

		channel = guild.get_channel(audit["message_delete"]["channel_id"])
		if channel is None:
			return

		payload_channel = guild.get_channel(payload.channel_id)
		deleted_messages = ""
		delete_messages_fp = self.TEMP_PATH + str(uuid.uuid4()) + ".txt"
		for message in payload.cached_messages:
			if message.author.bot:
				continue

			deleted_messages += f"""\n{message.created_at.strftime("%H:%M:%S %d-%m-%Y")} -- {str(message.author)}\n{message.content}\n\n"""

		self.client.txt_dump(delete_messages_fp, deleted_messages)
		e = discord.Embed(
			description=f"Удалено `{len(payload.cached_messages)}` сообщений",
			colour=discord.Color.orange(),
			timestamp=await self.client.utils.get_guild_time(guild),
		)
		e.add_field(
			name=f"Канал",
			value=f"`{payload_channel.name}`",
			inline=False,
		)
		e.set_author(
			name="Журнал аудита | Массовое удаления сообщений",
			icon_url=self.client.user.avatar_url,
		)
		e.set_footer(
			text=self.FOOTER, icon_url=self.client.user.avatar_url
		)
		await channel.send(
			embed=e, file=discord.File(fp=delete_messages_fp)
		)
		os.remove(
			"/home/ProstoTools" + delete_messages_fp[1:]
		)

	@commands.Cog.listener()
	async def on_message_delete(self, message):
		if message.author.bot:
			return

		data = await self.client.database.sel_guild(guild=message.guild)
		if not data.audit["message_delete"]["state"]:
			return

		channel = self.client.get_channel(data.audit["message_delete"]["channel_id"])
		if channel is None:
			return

		if len(message.content) > 1000:
			return

		e = discord.Embed(
			colour=discord.Color.orange(), timestamp=await self.client.utils.get_guild_time(message.guild)
		)
		e.add_field(
			name="Удалённое сообщение",
			value=f"```{message.content}```"
			if message.content
			else "Сообщения отсутствует ",
			inline=False,
		)
		e.add_field(
			name="Автор сообщения", value=f"{message.author}(`{message.author.id}`)", inline=False
		)
		e.add_field(name="Канал", value=f"{message.channel.mention}(`{message.channel.id}`)", inline=False)
		e.add_field(name="Id Сообщения", value=f"`{message.id}`", inline=False)
		e.set_author(
			name="Журнал аудита | Удаление сообщения",
			icon_url=message.author.avatar_url,
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

		if data.donate:
			await self.client.database.add_audit_log(
				user=message.author,
				channel=message.channel,
				guild_id=message.guild.id,
				action_type="message_delete",
				message_content=message.content,
				message_id=message.id
			)

	@commands.Cog.listener()
	async def on_message_edit(self, before, after):
		if before.content == after.content:
			return

		if before.author.bot:
			return

		data = await self.client.database.sel_guild(guild=before.guild)
		if not data.audit["message_edit"]["state"]:
			return

		channel = self.client.get_channel(data.audit["message_edit"]["channel_id"])
		if channel is None:
			return

		e = discord.Embed(
			description=f"**[Сообщение]({before.jump_url}) было изменено**",
			colour=discord.Color.gold(),
			timestamp=await self.client.utils.get_guild_time(after.guild),
		)
		e.add_field(
			name="Старое содержимое", value=f"```{before.content}```", inline=False
		)
		e.add_field(
			name="Новое соодержиое", value=f"```{after.content}```", inline=False
		)
		e.add_field(name="Автор", value=f"{after.author}(`{after.author.id}`)", inline=False)
		e.add_field(name="Канал", value=f"{after.channel.mention}(`{after.channel.id}`)", inline=False)
		e.add_field(name="Id Сообщения", value=f"`{before.id}`", inline=False)
		e.set_author(
			name="Журнал аудита | Изменение сообщения",
			icon_url=before.author.avatar_url,
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

		if data.donate:
			await self.client.database.add_audit_log(
				user=after.author,
				channel=after.channel,
				guild_id=after.guild.id,
				action_type="message_edit",
				after_content=after.content,
				before_content=before.content,
				message_id=after.id
			)

	@commands.Cog.listener()
	async def on_guild_channel_create(
			self, new_channel: typing.Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel]
	):
		data = await self.client.database.sel_guild(guild=new_channel.guild)
		if not data.audit["channel_create"]["state"]:
			return

		channel = self.client.get_channel(data.audit["channel_create"]["channel_id"])
		if channel is None:
			return

		e = discord.Embed(
			description=f"Создан **{self.CHANNEL_TYPES[new_channel.type]}**",
			colour=discord.Color.green(),
			timestamp=await self.client.utils.get_guild_time(new_channel.guild),
		)
		e.add_field(name="Канал", value=f"{new_channel.mention}(`{new_channel.id}`)", inline=False)
		e.set_author(
			name="Журнал аудита | Новый канал",
			icon_url=self.client.user.avatar_url,
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

		if data.donate:
			await self.client.database.add_audit_log(
				user=channel.guild.me,
				channel=new_channel,
				guild_id=channel.guild.id,
				action_type="channel_create",
			)

	@commands.Cog.listener()
	async def on_guild_channel_delete(
			self, new_channel: typing.Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel]
	):
		data = await self.client.database.sel_guild(guild=new_channel.guild)
		if not data.audit["channel_delete"]["state"]:
			return

		channel = self.client.get_channel(data.audit["channel_delete"]["channel_id"])
		if channel is None:
			return

		e = discord.Embed(
			description=f"Удален **{self.CHANNEL_TYPES[new_channel.type]}**",
			colour=discord.Color.green(),
			timestamp=await self.client.utils.get_guild_time(new_channel.guild),
		)
		e.add_field(name="Канал", value=f"#{new_channel.name}(`{new_channel.id}`)", inline=False)
		e.set_author(
			name="Журнал аудита | Удален канал",
			icon_url=self.client.user.avatar_url,
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

		if data.donate:
			await self.client.database.add_audit_log(
				user=channel.guild.me,
				channel=new_channel,
				guild_id=channel.guild.id,
				action_type="channel_delete",
			)

	@commands.Cog.listener()
	async def on_guild_role_create(self, role: discord.Role):
		data = await self.client.database.sel_guild(guild=role.guild)
		if not data.audit["role_create"]["state"]:
			return

		channel = self.client.get_channel(data.audit["role_create"]["channel_id"])
		if channel is None:
			return

		e = discord.Embed(
			description=f"Создана новая роль `@{role.name}`",
			colour=discord.Color.green(),
			timestamp=await self.client.utils.get_guild_time(role.guild),
		)
		e.add_field(name="Роль", value=f"{role.mention}(`{role.id}`)", inline=False)
		e.set_author(
			name="Журнал аудита | Новая роль",
			icon_url=self.client.user.avatar_url,
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

		if data.donate:
			await self.client.database.add_audit_log(
				user=channel.guild.me,
				channel=channel,
				guild_id=channel.guild.id,
				action_type="role_create",
			)

	@commands.Cog.listener()
	async def on_guild_role_delete(self, role: discord.Role):
		data = await self.client.database.sel_guild(guild=role.guild)
		if not data.audit["role_delete"]["state"]:
			return

		channel = self.client.get_channel(data.audit["role_delete"]["channel_id"])
		if channel is None:
			return

		e = discord.Embed(
			description=f"Удалена роль `@{role.name}`",
			colour=discord.Color.green(),
			timestamp=await self.client.utils.get_guild_time(role.guild),
		)
		e.add_field(name="Роль", value=f"@{role.name}(`{role.id}`)", inline=False)
		e.set_author(
			name="Журнал аудита | Удалена роль",
			icon_url=self.client.user.avatar_url,
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

		if data.donate:
			await self.client.database.add_audit_log(
				user=channel.guild.me,
				channel=channel,
				guild_id=channel.guild.id,
				action_type="role_delete",
			)

	@commands.Cog.listener()
	async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
		data = await self.client.database.sel_guild(guild=member.guild)

		if before.channel is None and after.channel is not None:
			if not data.audit["member_voice_connect"]["state"]:
				return

			channel = self.client.get_channel(data.audit["member_voice_connect"]["channel_id"])
			if channel is None:
				return

			e = discord.Embed(
				description=f"Участник подключился к голосовому каналу",
				colour=discord.Color.green(),
				timestamp=await self.client.utils.get_guild_time(member.guild),
			)
			e.add_field(name="Участник", value=f"{member}(`{member.id}`)", inline=False)
			e.add_field(name="Канал", value=f"{after.channel.mention}(`{after.channel.id}`)", inline=False)
			e.set_author(
				name="Журнал аудита | Подключения к голосовому каналу",
				icon_url=self.client.user.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await channel.send(embed=e)

			if data.donate:
				await self.client.database.add_audit_log(
					user=member,
					channel=after.channel,
					guild_id=member.guild.id,
					action_type="member_voice_connect",
				)
		elif before.channel is not None and after.channel is None:
			if not data.audit["member_voice_disconnect"]["state"]:
				return

			channel = self.client.get_channel(data.audit["member_voice_disconnect"]["channel_id"])
			if channel is None:
				return

			e = discord.Embed(
				description=f"Участник покинул голосовой канал",
				colour=discord.Color.green(),
				timestamp=await self.client.utils.get_guild_time(member.guild),
			)
			e.add_field(name="Участник", value=f"{member}(`{member.id}`)", inline=False)
			e.add_field(name="Канал", value=f"{before.channel.mention}(`{before.channel.id}`)", inline=False)
			e.set_author(
				name="Журнал аудита | Отключения от голосового канала",
				icon_url=self.client.user.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await channel.send(embed=e)

			if data.donate:
				await self.client.database.add_audit_log(
					user=member,
					channel=before.channel,
					guild_id=member.guild.id,
					action_type="member_voice_disconnect",
				)
		elif before.channel is not None and after.channel is not None:
			if not data.audit["member_voice_move"]["state"]:
				return

			channel = self.client.get_channel(data.audit["member_voice_move"]["channel_id"])
			if channel is None:
				return

			e = discord.Embed(
				description=f"Участник перешел в другой голосовой канал",
				colour=discord.Color.green(),
				timestamp=await self.client.utils.get_guild_time(member.guild),
			)
			e.add_field(name="Участник", value=f"{member}(`{member.id}`)", inline=False)
			e.add_field(name="С канала", value=f"{before.channel.mention}(`{before.channel.id}`)", inline=False)
			e.add_field(name="В канал", value=f"{after.channel.mention}(`{after.channel.id}`)", inline=False)
			e.set_author(
				name="Журнал аудита | Переход в другой голосовой канал",
				icon_url=self.client.user.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await channel.send(embed=e)

			if data.donate:
				await self.client.database.add_audit_log(
					user=member,
					channel=before.channel,
					guild_id=member.guild.id,
					action_type="member_voice_move",
					to_channel=after.channel
				)


def setup(client):
	client.add_cog(EventsAudit(client))
