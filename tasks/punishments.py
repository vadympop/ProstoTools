import discord
import time

from datetime import datetime
from discord.ext import commands, tasks
from discord.utils import get


class TasksPunishments(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.mute_loop.start()
		self.ban_loop.start()
		self.temprole_loop.start()
		self.vmute_loop.start()
		self.FOOTER = self.client.config.FOOTER_TEXT

	@tasks.loop(seconds=5)
	async def mute_loop(self):
		if self.client.is_ready():
			for mute in await self.client.database.get_punishment():
				mute_time = mute[2]
				guild = self.client.get_guild(int(mute[1]))
				if mute[3] == "mute":
					if guild is not None:
						logs_channel_id = (await self.client.database.sel_guild(guild=guild))["log_channel"]
						member = guild.get_member(int(mute[0]))
						if member is not None:
							if float(mute_time) <= float(time.time()):
								await self.client.database.del_punishment(
									member=member, guild_id=guild.id, type_punishment="mute"
								)
								mute_role = guild.get_role(int(mute[4]))
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

								if logs_channel_id != 0:
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
									await guild.get_channel(logs_channel_id).send(embed=e)

	@tasks.loop(seconds=5)
	async def ban_loop(self):
		if self.client.is_ready():
			for ban in await self.client.database.get_punishment():
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

	@tasks.loop(seconds=5)
	async def temprole_loop(self):
		if self.client.is_ready():
			for temprole in await self.client.database.get_punishment():
				temprole_time = temprole[2]
				guild = self.client.get_guild(int(temprole[1]))
				if temprole[3] == "temprole":
					if guild is not None:
						member = guild.get_member(int(temprole[0]))
						if member is not None:
							if float(temprole_time) <= float(time.time()):
								await self.client.database.del_punishment(
									member=member,
									guild_id=guild.id,
									type_punishment="temprole",
								)
								temprole_role = get(guild.roles, id=int(temprole[4]))
								await member.remove_roles(temprole_role)

	@tasks.loop(seconds=5)
	async def vmute_loop(self):
		if self.client.is_ready():
			for vmute in await self.client.database.get_punishment():
				vmute_time = vmute[2]
				guild = self.client.get_guild(int(vmute[1]))
				if vmute[3] == "vmute":
					if guild is not None:
						logs_channel_id = (await self.client.database.sel_guild(guild=guild))["log_channel"]
						member = guild.get_member(int(vmute[0]))
						if member is not None:
							if float(vmute_time) <= float(time.time()):
								await self.client.database.del_punishment(
									member=member,
									guild_id=guild.id,
									type_punishment="vmute",
								)
								vmute_role = guild.get_role(int(vmute[4]))
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

								if logs_channel_id != 0:
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
									await guild.get_channel(logs_channel_id).send(embed=e)


def setup(client):
	client.add_cog(TasksPunishments(client))
