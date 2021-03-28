import discord
import time

from core.bases.cog_base import BaseCog
from datetime import datetime
from discord.ext import tasks


class TasksPunishments(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.mute_loop.start()
		self.ban_loop.start()
		self.temprole_loop.start()
		self.vmute_loop.start()

	@tasks.loop(minutes=1)
	async def mute_loop(self):
		await self.client.wait_until_ready()
		for mute in await self.client.database.get_punishments():
			guild = self.client.get_guild(int(mute[1]))
			if mute[3] == "mute":
				if guild is not None:
					member = guild.get_member(mute.member_id)
					if float(mute.time) <= float(time.time()):
						await self.client.database.del_punishment(
							member=member, guild_id=guild.id, type_punishment="mute"
						)
						mute_role = guild.get_role(mute.role_id)
						if member is not None and mute_role is not None:
							await member.remove_roles(mute_role)

							emb = discord.Embed(
								description=f"**Вы были размьючены на сервере** `{guild.name}`",
								colour=discord.Color.green(),
							)
							emb.set_author(
								name=self.client.user.name,
								icon_url=self.client.user.avatar_url,
							)
							emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
							try:
								await member.send(embed=emb)
							except:
								pass

							audit = (await self.client.database.sel_guild(guild=guild)).audit
							if "moderate" in audit.keys():
								e = discord.Embed(
									description=f"Пользователь `{str(member)}` был размьючен",
									colour=discord.Color.green(),
									timestamp=datetime.utcnow(),
								)
								e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
								e.set_author(
									name="Журнал аудита | Размьют пользователя",
									icon_url=self.client.user.avatar_url,
								)
								e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
								channel = guild.get_channel(audit["moderate"])
								if channel is not None:
									await channel.send(embed=e)

	@tasks.loop(minutes=1)
	async def ban_loop(self):
		await self.client.wait_until_ready()
		for ban in await self.client.database.get_punishments():
			guild = self.client.get_guild(ban.guild_id)
			if ban.type == "ban":
				if guild is not None:
					bans = await guild.bans()
					for ban_entry in bans:
						user = ban_entry.user
						if user.id == ban.member_id:
							if float(ban.time) <= float(time.time()):
								await self.client.database.del_punishment(
									member=user,
									guild_id=guild.id,
									type_punishment="ban",
								)
								await guild.unban(user)

								emb = discord.Embed(
									description=f"**Вы были разбанены на сервере** `{guild.name}`",
									colour=discord.Color.green(),
								)
								emb.set_author(
									name=self.client.user.name,
									icon_url=self.client.user.avatar_url,
								)
								emb.set_footer(
									text=self.FOOTER,
									icon_url=self.client.user.avatar_url,
								)
								try:
									await user.send(embed=emb)
								except:
									pass

	@tasks.loop(minutes=1)
	async def temprole_loop(self):
		await self.client.wait_until_ready()
		for temprole in await self.client.database.get_punishments():
			guild = self.client.get_guild(temprole.guild_id)
			if temprole.type == "temprole":
				if guild is not None:
					member = guild.get_member(temprole.member_id)
					if float(temprole.time) <= float(time.time()):
						await self.client.database.del_punishment(
							member=member,
							guild_id=guild.id,
							type_punishment="temprole",
						)
						temprole_role = guild.get_role(temprole.role_id)
						if member is not None and temprole_role is not None:
							await member.remove_roles(temprole_role)

	@tasks.loop(minutes=1)
	async def vmute_loop(self):
		await self.client.wait_until_ready()
		for vmute in await self.client.database.get_punishments():
			guild = self.client.get_guild(vmute.guild_id)
			if vmute.type == "vmute":
				if guild is not None:
					member = guild.get_member(vmute.member_id)
					if float(vmute.time) <= float(time.time()):
						await self.client.database.del_punishment(
							member=member,
							guild_id=guild.id,
							type_punishment="vmute",
						)
						vmute_role = guild.get_role(vmute.role_id)
						if member is not None and vmute_role is not None:
							await member.remove_roles(vmute_role)

							overwrite = discord.PermissionOverwrite(connect=None)
							for channel in guild.voice_channels:
								await channel.set_permissions(
									vmute_role, overwrite=overwrite
								)

							emb = discord.Embed(
								description=f"**Вы были размьючены в голосовых каналах на сервере** `{guild.name}`",
								colour=discord.Color.green(),
							)
							emb.set_author(
								name=self.client.user.name,
								icon_url=self.client.user.avatar_url,
							)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							try:
								await member.send(embed=emb)
							except:
								pass

							audit = (await self.client.database.sel_guild(guild=guild)).audit
							if "moderate" in audit.keys():
								e = discord.Embed(
									description=f"Пользователь `{str(member)}` был размьючен в голосовых каналах",
									colour=discord.Color.green(),
									timestamp=datetime.utcnow(),
								)
								e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
								e.set_author(
									name="Журнал аудита | Голосовой размьют пользователя",
									icon_url=self.client.user.avatar_url,
								)
								e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
								channel = guild.get_channel(audit["moderate"])
								if channel is not None:
									await channel.send(embed=e)


def setup(client):
	client.add_cog(TasksPunishments(client))
