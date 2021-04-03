import discord
import asyncio

from core.services.database.models import User
from core.bases.cog_base import BaseCog
from discord.ext import tasks


class TasksMessageStat(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.message_stat_loop.start()

	@tasks.loop(minutes=5)
	async def message_stat_loop(self):
		for guild in self.client.guilds:
			if guild is None:
				continue

			server_stats = (await self.client.database.sel_guild(guild=guild)).server_stats
			if "message" in server_stats.keys():
				channel = guild.get_channel(server_stats["message"][1])
				if channel is None:
					server_stats.pop("message")
					await self.client.database.update(
						"guilds",
						where={"guild_id": guild.id},
						server_stats=server_stats
					)
					continue

				try:
					message = await channel.fetch_message(server_stats["message"][0])
				except discord.errors.NotFound:
					server_stats.pop("message")
					await self.client.database.update(
						"guilds",
						where={"guild_id": guild.id},
						server_stats=server_stats
					)
				except discord.errors.DiscordServerError:
					pass
				else:
					if message is not None:
						all_exp = sum([u.exp for u in User.objects.filter(guild_id=guild.id)])
						data = User.objects.filter(guild_id=guild.id).order_by("-exp")[:20]
						dnd = len([
							str(member.id)
							for member in guild.members
							if member.status.name == "dnd"
						])
						sleep = len([
							str(member.id)
							for member in guild.members
							if member.status.name == "idle"
						])
						online = len([
							str(member.id)
							for member in guild.members
							if member.status.name == "online"
						])
						offline = len([
							str(member.id)
							for member in guild.members
							if member.status.name == "offline"
						])
						description = "Статистика обновляеться каждые 5 минут\n\n**20 Самых активных участников сервера**"
						num = 1
						for profile in data:
							member = guild.get_member(profile.user_id)
							if member is not None:
								if not member.bot:
									if len(member.name) > 10:
										member = member.name[:10] + "..." + "#" + member.discriminator
									description += f"""\n`{num}. {str(member)} {profile.exp}exp {profile.money}$ {profile.reputation}rep`"""
									num += 1

						description += f"""
\n**Общая инфомация**
:baby:Пользователей: **{guild.member_count}**
:family_man_girl_boy:Участников: **{len([m.id for m in guild.members if not m.bot])}**
<:bot:731819847905837066>Ботов: **{len([m.id for m in guild.members if m.bot])}**
<:voice_channel:730399079418429561>Голосовых подключений: **{sum([len(v.members) for v in guild.voice_channels])}**
<:text_channel:730396561326211103>Каналов: **{len([c.id for c in guild.channels])}**
<:role:730396229220958258>Ролей: **{len([r.id for r in guild.roles])}**
:star:Всего опыта: **{all_exp}**
\n**Статусы участников**
<:online:730393440046809108>`{online}`  <:offline:730392846573633626>`{offline}`
<:sleep:730390502972850256>`{sleep}`  <:mobile:777854822300385291>`{len([m.id for m in guild.members if m.is_on_mobile()])}`
<:dnd:730391353929760870>`{dnd}` <:boost:777854437724127272>`{len(set(guild.premium_subscribers))}`
"""

						emb = discord.Embed(
							title="Статистика сервера",
							description=description,
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=self.client.user.name, icon_url=self.client.user.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await message.edit(embed=emb)
						await asyncio.sleep(5)

	def cog_unload(self):
		self.message_stat_loop.cancel()


def setup(client):
	client.add_cog(TasksMessageStat(client))
