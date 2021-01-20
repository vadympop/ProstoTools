import discord
import datetime

from discord.ext import commands


class EventsAudit(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		if self.client.is_ready():
			try:
				audit = (await self.client.database.sel_guild(guild=before.guild))["audit"]
			except AttributeError:
				return
			if "member_update" not in audit.keys():
				return
			channel = self.client.get_channel(audit["member_update"])
			if channel is None:
				return

			if not len(before.roles) == len(after.roles):
				roles = []
				if len(before.roles) > len(after.roles):
					for i in before.roles:
						if not i in after.roles:
							roles.append(f"➖ Была убрана роль {i.name}(<@&{i.id}>)\n")
				elif len(before.roles) < len(after.roles):
					for i in after.roles:
						if not i in before.roles:
							roles.append(f"➕ Была добавлена роль {i.name}(<@&{i.id}>)\n")

				e = discord.Embed(
					description=f"У пользователя `{str(after)}` были изменены роли",
					colour=discord.Color.green(),
					timestamp=datetime.datetime.utcnow(),
				)
				e.add_field(
					name="Было сделано", value=f"**{''.join(roles)}**", inline=False
				)
				e.add_field(name="Id Участника", value=f"`{after.id}`", inline=False)
				e.set_author(
					name="Журнал аудита | Изменение ролей участника",
					icon_url=before.avatar_url,
				)
				e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await channel.send(embed=e)

			if not before.display_name == after.display_name:
				e = discord.Embed(
					description=f"Пользователь `{str(before)}` изменил ник",
					colour=discord.Color.green(),
					timestamp=datetime.datetime.utcnow(),
				)
				e.add_field(
					name="Действующее имя",
					value=f"`{after.display_name+'#'+after.discriminator}`",
					inline=False,
				)
				e.add_field(
					name="Предыдущее имя",
					value=f"`{before.display_name+'#'+before.discriminator}`",
					inline=False,
				)
				e.add_field(name="Id Участника", value=f"`{after.id}`", inline=False)
				e.set_author(
					name="Журнал аудита | Изменение ника участника",
					icon_url=before.avatar_url,
				)
				e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_member_ban(self, guild, user):
		audit = (await self.client.database.sel_guild(guild=guild))["audit"]
		if "member_ban" not in audit.keys():
			return
		channel = self.client.get_channel(audit["member_ban"])
		if channel is None:
			return

		ban = await guild.fetch_ban(user)
		e = discord.Embed(
			description=f"Пользователь `{str(user)}` был забанен",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow(),
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

	@commands.Cog.listener()
	async def on_member_unban(self, guild, user):
		if user.bot:
			return

		audit = (await self.client.database.sel_guild(guild=guild))["audit"]
		if "member_unban" not in audit.keys():
			return
		channel = self.client.get_channel(audit["member_unban"])
		if channel is None:
			return

		e = discord.Embed(
			description=f"Пользователь `{str(user)}` был разбанен",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow(),
		)
		e.add_field(name="Id Участника", value=f"`{user.id}`", inline=False)
		e.set_author(
			name="Журнал аудита | Разбан пользователя", icon_url=user.avatar_url
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_message_delete(self, message):
		if message.author.bot:
			return

		audit = (await self.client.database.sel_guild(guild=message.guild))["audit"]
		if "message_delete" not in audit.keys():
			return
		channel = self.client.get_channel(audit["message_delete"])
		if channel is None:
			return

		if len(message.content) > 1000:
			return
		e = discord.Embed(
			colour=discord.Color.green(), timestamp=datetime.datetime.utcnow()
		)
		e.add_field(
			name="Удалённое сообщение",
			value=f"```{message.content}```"
			if message.content
			else "Сообщения отсутствует ",
			inline=False,
		)
		e.add_field(
			name="Автор сообщения", value=f"`{str(message.author)}`", inline=False
		)
		e.add_field(name="Канал", value=f"`{message.channel.name}`", inline=False)
		e.add_field(name="Id Сообщения", value=f"`{message.id}`", inline=False)
		e.set_author(
			name="Журнал аудита | Удаление сообщения",
			icon_url=message.author.avatar_url,
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)

	@commands.Cog.listener()
	async def on_message_edit(self, before, after):
		if before.content == after.content:
			return

		if before.author.bot:
			return

		audit = (await self.client.database.sel_guild(guild=before.guild))["audit"]
		if "message_edit" not in audit.keys():
			return
		channel = self.client.get_channel(audit["message_edit"])
		if channel is None:
			return

		e = discord.Embed(
			description=f"**[Сообщение]({before.jump_url}) было изменено**",
			colour=discord.Color.green(),
			timestamp=datetime.datetime.utcnow(),
		)
		e.add_field(
			name="Старое содержимое", value=f"```{before.content}```", inline=False
		)
		e.add_field(
			name="Новое соодержиое", value=f"```{after.content}```", inline=False
		)
		e.add_field(name="Автор", value=f"`{str(before.author)}`", inline=False)
		e.add_field(name="Канал", value=f"`{before.channel.name}`", inline=False)
		e.add_field(name="Id Сообщения", value=f"`{before.id}`", inline=False)
		e.set_author(
			name="Журнал аудита | Изменение сообщения",
			icon_url=before.author.avatar_url,
		)
		e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await channel.send(embed=e)


def setup(client):
	client.add_cog(EventsAudit(client))
