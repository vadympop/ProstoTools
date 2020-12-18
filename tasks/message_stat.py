import discord
import json

from tools import DB

from discord.ext import commands, tasks


class TasksMessageStat(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.message_stat_loop.start()
		self.FOOTER = self.client.config.FOOTER_TEXT

	@tasks.loop(minutes=5)
	async def message_stat_loop(self):
		for guild in self.client.guilds:
			data_guild = await self.client.database.sel_guild(guild=guild)
			if "message" in data_guild["server_stats"].keys():
				message = await guild.get_channel(
					data_guild["server_stats"]["message"][1]
				).fetch_message(data_guild["server_stats"]["message"][0])
				if message is not None:
					val = (guild.id, guild.id)
					sql_1 = """SELECT user_id, exp, money, reputation, messages FROM users WHERE guild_id = %s AND guild_id = %s ORDER BY exp DESC LIMIT 20"""
					sql_2 = """SELECT exp FROM users WHERE guild_id = %s AND guild_id = %s"""

					data = await self.client.database.execute(sql_1, val)
					all_exp = sum([i[0] for i in await self.client.database.execute(sql_2, val)])
					dnd = len(
						[
							str(member.id)
							for member in guild.members
							if member.status.name == "dnd"
						]
					)
					sleep = len(
						[
							str(member.id)
							for member in guild.members
							if member.status.name == "idle"
						]
					)
					online = len(
						[
							str(member.id)
							for member in guild.members
							if member.status.name == "online"
						]
					)
					offline = len(
						[
							str(member.id)
							for member in guild.members
							if member.status.name == "offline"
						]
					)
					description = "Статистика обновляеться каждые 5 минут\n\n**20 Самых активных участников сервера**"
					num = 1
					for profile in data:
						member = guild.get_member(profile[0])
						if member is not None:
							if not member.bot:
								if len(member.name) > 15:
									member = (
										member.name[:15]
										+ "..."
										+ "#"
										+ member.discriminator
									)
								description += f"""\n`{num}. {str(member)} {profile[1]}exp {profile[2]}$ {profile[3]}rep {json.loads(profile[4])[1]}msg`"""
								num += 1

					description += f"""\n\n**Общая инфомация**\n:baby:Пользователей: **{guild.member_count}**\n:family_man_girl_boy:Участников: **{len([m.id for m in guild.members if not m.bot])}**\n<:bot:731819847905837066>Ботов: **{len([m.id for m in guild.members if m.bot])}**\n<:voice_channel:730399079418429561>Голосовых подключений: **{sum([len(v.members) for v in guild.voice_channels])}**\n<:text_channel:730396561326211103>Каналов: **{len([c.id for c in guild.channels])}**\n<:role:730396229220958258>Ролей: **{len([r.id for r in guild.roles])}**\n:star:Всего опыта: **{all_exp}**\n\n**Статусы участников**\n<:online:730393440046809108>`{online}`  <:offline:730392846573633626>`{offline}`\n<:sleep:730390502972850256>`{sleep}`  <:mobile:777854822300385291>`{len([m.id for m in guild.members if m.is_on_mobile()])}`\n<:dnd:730391353929760870>`{dnd}`  <:boost:777854437724127272>`{len(set(guild.premium_subscribers))}`"""

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


def setup(client):
	client.add_cog(TasksMessageStat(client))
