import discord
import time

from datetime import datetime
from discord.ext import commands, tasks


class TasksPunishments(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.mute_loop.start()
		self.ban_loop.start()
		self.temprole_loop.start()
		self.vmute_loop.start()
		self.FOOTER = self.client.config.FOOTER_TEXT

	@tasks.loop(minutes=1)
	async def mute_loop(self):
		try:
			data = await self.client.database.get_punishment()
		except AttributeError:
			pass
		else:
			for mute in data:
				mute_time = mute[2]
				guild = self.client.get_guild(int(mute[1]))
				if mute[3] == "mute":
					if guild is not None:
						audit = (await self.client.database.sel_guild(guild=guild))["audit"]
						member = guild.get_member(int(mute[0]))
						if float(mute_time) <= float(time.time()):
							await self.client.database.del_punishment(
								member=member, guild_id=guild.id, type_punishment="mute"
							)
							mute_role = guild.get_role(int(mute[4]))
							if member is not None and mute_role is not None:
								await member.remove_roles(mute_role)

								emb = discord.Embed(
									description=f"**Вы были размьючены на сервере `{guild.name}`**",
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
		try:
			data = await self.client.database.get_punishment()
		except AttributeError:
			pass
		else:
			for ban in data:
				ban_time = ban[2]
				guild = self.client.get_guild(int(ban[1]))
				if ban[3] == "ban":
					if guild is not None:
						bans = await guild.bans()
						for ban_entry in bans:
							user = ban_entry.user
							if user.id == ban[0]:
								if float(ban_time) <= float(time.time()):
									await self.client.database.del_punishment(
										member=user,
										guild_id=guild.id,
										type_punishment="ban",
									)
									await guild.unban(user)

									emb = discord.Embed(
										description=f"**Вы были разбанены на сервере `{guild.name}`**",
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
		try:
			data = await self.client.database.get_punishment()
		except AttributeError:
			pass
		else:

			for temprole in data:
				temprole_time = temprole[2]
				guild = self.client.get_guild(int(temprole[1]))
				if temprole[3] == "temprole":
					if guild is not None:
						member = guild.get_member(int(temprole[0]))
						if float(temprole_time) <= float(time.time()):
							await self.client.database.del_punishment(
								member=member,
								guild_id=guild.id,
								type_punishment="temprole",
							)
							temprole_role = guild.get_role(int(temprole[4]))
							if member is not None and temprole_role is not None:
								await member.remove_roles(temprole_role)

	@tasks.loop(minutes=1)
	async def vmute_loop(self):
		try:
			data = await self.client.database.get_punishment()
		except AttributeError:
			pass
		else:

			for vmute in data:
				vmute_time = vmute[2]
				guild = self.client.get_guild(int(vmute[1]))
				if vmute[3] == "vmute":
					if guild is not None:
						audit = (await self.client.database.sel_guild(guild=guild))["audit"]
						member = guild.get_member(int(vmute[0]))
						if float(vmute_time) <= float(time.time()):
							await self.client.database.del_punishment(
								member=member,
								guild_id=guild.id,
								type_punishment="vmute",
							)
							vmute_role = guild.get_role(int(vmute[4]))
							if member is not None and vmute_role is not None:
								await member.remove_roles(vmute_role)

								overwrite = discord.PermissionOverwrite(connect=None)
								for channel in guild.voice_channels:
									await channel.set_permissions(
										vmute_role, overwrite=overwrite
									)

								emb = discord.Embed(
									description=f"**Вы были размьючены в голосовых каналах на сервере `{guild.name}`**",
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
