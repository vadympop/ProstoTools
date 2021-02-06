import discord
from discord.ext import commands


class EventsLeave(commands.Cog):
	def __init__(self, client):
		self.client = client

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		await self.client.database.add_amout_command(entity="guilds", add_counter=len(self.client.guilds))
		await self.client.database.execute(f"""DELETE FROM guilds WHERE guild_id = {guild.id}""")
		await self.client.database.execute(f"""DELETE FROM mutes WHERE guild_id = {guild.id}""")
		await self.client.database.execute(f"""DELETE FROM punishments WHERE guild_id = {guild.id}""")
		await self.client.database.execute(f"""DELETE FROM reminders WHERE guild_id = {guild.id}""")
		await self.client.database.execute(f"""DELETE FROM warns WHERE guild_id = {guild.id}""")
		await self.client.cache.delete(
			str(guild.id)
		)
		for member in guild.members:
			await self.client.database.execute(
				"""DELETE FROM users WHERE user_id = %s AND guild_id = %s""",
				(member.id, guild.id)
			)

		emb_info = discord.Embed(
			title=f"Бот изгнан из сервера, всего серверов - {len(self.client.guilds)}",
			colour=discord.Color.green(),
			description=f"Названия сервера - `{guild.name}`\nАйди сервера - `{guild.id}`\nВладелец - `{guild.owner}`\nКол-во участников - `{guild.member_count}`",
		)
		emb_info.set_thumbnail(url=guild.icon_url)
		await self.client.get_guild(717776571406090310).get_channel(737685906873647165).send(embed=emb_info)

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		await self.client.database.execute(f"""DELETE FROM reminders WHERE user_id = {member.id}""")


def setup(client):
	client.add_cog(EventsLeave(client))
