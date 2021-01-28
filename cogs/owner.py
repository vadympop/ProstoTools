import traceback
from discord.ext import commands


class Owner(commands.Cog, name="Owner"):
	def __init__(self, client):
		self.client = client

	@commands.command()
	@commands.is_owner()
	async def _sh(self, ctx, *, message: str = None):
		data = await self.client.database.sel_user(ctx.author)
		multi = (await self.client.database.sel_guild(ctx.guild))["exp_multi"]
		data.update({"multi": multi})
		try:
			result = await self.client.template_engine.render(ctx.message, ctx.author, data, message)
		except Exception:
			await ctx.send(f"```{traceback.format_exc()}```")
		else:
			try:
				await ctx.send(result)
			except Exception:
				await ctx.send(f"```{traceback.format_exc()}```")

	@commands.command()
	@commands.is_owner()
	async def _rc(self, ctx, *, command: str):
		command = self.client.get_command(command)
		command.reset_cooldown(ctx)

	@commands.command()
	@commands.is_owner()
	async def _ed(self, ctx):
		pass


def setup(client):
	client.add_cog(Owner(client))
