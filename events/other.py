from discord.ext import commands


class EventsOther(commands.Cog):
	def __init__(self, client):
		self.client = client

	@commands.Cog.listener()
	async def on_command(self, ctx):
		await self.client.database.add_amout_command(entity=ctx.command.name)

		await self.client.database.execute(
			"""UPDATE users SET num_commands = num_commands + 1 WHERE user_id = %s AND guild_id = %s""",
			(ctx.author.id, ctx.guild.id),
		)


def setup(client):
	client.add_cog(EventsOther(client))
