import discord
import uuid
import os

from core.bases.cog_base import BaseCog
from discord.ext import commands


class EventsAudit(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.TEMP_PATH = self.client.config.TEMP_PATH

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		data = await self.client.database.sel_guild(guild=before.guild)

		if "member_update" not in data.audit.keys():
			return

		channel = self.client.get_channel(data.audit["member_update"])
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
					action_type="member_update",
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
					action_type="member_update",
					after_nick=str(after),
					before_nick=str(before)
				)

	@commands.Cog.listener()
	async def on_member_ban(self, guild, user):
		data = await self.client.database.sel_guild(guild=guild)
		if "member_ban" not in data.audit.keys():
			return

		channel = self.client.get_channel(data.audit["member_ban"])
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
		if "member_unban" not in data.audit.keys():
			return

		channel = self.client.get_channel(data.audit["member_unban"])
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
		if "message_delete" not in audit.keys():
			return

		channel = guild.get_channel(audit["message_delete"])
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
		channel = guild.get_channel(audit["moderate"])
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
		if "message_delete" not in data.audit.keys():
			return

		channel = self.client.get_channel(data.audit["message_delete"])
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
		if "message_edit" not in data.audit.keys():
			return

		channel = self.client.get_channel(data.audit["message_edit"])
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


def setup(client):
	client.add_cog(EventsAudit(client))
