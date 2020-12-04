from tools import DB
from discord.ext import commands


class EventsOther(commands.Cog):
	def __init__(self, client):
		self.client = client

	@commands.Cog.listener()
	async def on_command(self, ctx):
		DB().add_amout_command(entity=ctx.command.name)


def setup(client):
	client.add_cog(EventsOther(client))
