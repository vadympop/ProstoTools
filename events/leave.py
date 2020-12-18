import discord
from discord.ext import commands


class EventsLeave(commands.Cog):
	def __init__(self, client):
		self.client = client

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		await self.client.database.add_amout_command(entity="guilds", add_counter=len(self.client.guilds))

		val = (guild.id, guild.id)
		sql_1 = """DELETE FROM guilds WHERE guild_id = %s AND guild_id = %s"""
		sql_2 = """DELETE FROM mutes WHERE guild_id = %s AND guild_id = %s"""
		sql_3 = """DELETE FROM punishments WHERE guild_id = %s AND guild_id = %s"""
		sql_4 = """DELETE FROM reminders WHERE guild_id = %s AND guild_id = %s"""
		sql_5 = """DELETE FROM warns WHERE guild_id = %s AND guild_id = %s"""

		await self.client.database.execute(sql_1, val)
		await self.client.database.execute(sql_2, val)
		await self.client.database.execute(sql_3, val)
		await self.client.database.execute(sql_4, val)
		await self.client.database.execute(sql_5, val)

		for member in guild.members:
			sql_2 = """DELETE FROM users WHERE user_id = %s AND guild_id = %s"""
			val_2 = (member.id, guild.id)

			await self.client.database.execute(sql_2, val_2)

		guild_owner_bot = self.client.get_guild(717776571406090310)
		channel = guild_owner_bot.text_channels[3]

		emb_info = discord.Embed(
			title=f"Бот изгнан из сервера, всего серверов - {len(self.client.guilds)}",
			description=f"Названия сервера - `{guild.name}`\nАйди сервера - `{guild.id}`\nВладелец - `{guild.owner}`\nКол-во участников - `{guild.member_count}`",
		)
		emb_info.set_thumbnail(url=guild.icon_url)

		await channel.send(embed=emb_info)

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		val = (member.id, member.id)
		sql_1 = """DELETE FROM mutes WHERE user_id = %s AND user_id = %s"""
		sql_2 = """DELETE FROM punishments WHERE member_id = %s AND member_id = %s"""
		sql_3 = """DELETE FROM reminders WHERE user_id = %s AND user_id = %s"""
		sql_4 = """DELETE FROM warns WHERE user_id = %s AND user_id = %s"""

		await self.client.database.execute(sql_1, val)
		await self.client.database.execute(sql_2, val)
		await self.client.database.execute(sql_3, val)
		await self.client.database.execute(sql_4, val)


def setup(client):
	client.add_cog(EventsLeave(client))
