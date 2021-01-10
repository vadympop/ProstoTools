from discord.ext import commands


class EventsOther(commands.Cog):
	def __init__(self, client):
		self.client = client

	@commands.Cog.listener()
	async def on_command(self, ctx):
		await self.client.database.add_amout_command(entity=ctx.command.name)
		if ctx.guild is None:
			return

		if ctx.author.bot:
			return

		num_commands = (await self.client.database.sel_user(target=ctx.author))["num_commands"]
		await self.client.database.update(
			"users",
			where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
			num_commands=num_commands+1
		)


def setup(client):
	client.add_cog(EventsOther(client))
