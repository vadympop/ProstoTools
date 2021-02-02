import traceback
import json
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
		await ctx.message.add_reaction("✅")

	@commands.command()
	@commands.is_owner()
	async def _eda(self, ctx, action: str, column: str, *, key: str):
		async with ctx.typing():
			try:
				if action == "update" or action == "u":
					guilds = await self.client.database.execute(
						f"SELECT guild_id, {column} FROM guilds"
					)
					for guild in guilds:
						json_data = json.loads(guild[1])
						if json_data is not None:
							json_data.update(json.loads(key))
						else:
							json_data = json.loads(key)
						await self.client.database.execute(
							f"""UPDATE guilds SET {column} = %s WHERE guild_id = {guild[0]}""",
							(json.dumps(json_data),)
						)
					await ctx.send(f"✅ `{column} has been edited(update)`")
				elif action == "pop" or action == "p":
					guilds = await self.client.database.execute(
						f"SELECT guild_id, {column} FROM guilds"
					)
					for guild in guilds:
						json_data = json.loads(guild[1])
						json_data.pop(json.loads(key)["key"])
						await self.client.database.execute(
							f"""UPDATE guilds SET {column} = %s WHERE guild_id = {guild[0]}""",
							(json.dumps(json_data),)
						)
					await ctx.send(f"✅ `{column} has been edited(pop)`")
				else:
					await ctx.send("❌ `Please select update or pop action`")
			except Exception:
				await ctx.send(f"```{traceback.format_exc()}```")


def setup(client):
	client.add_cog(Owner(client))
