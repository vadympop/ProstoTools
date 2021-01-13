import discord
import os
import ast
import math
import random

from tools import template_engine as TemplateEngine

from discord.ext import commands
from colorama import *
from discord.utils import get

init()


def insert_returns(body):
	if isinstance(body[-1], ast.Expr):
		body[-1] = ast.Return(body[-1].value)
		ast.fix_missing_locations(body[-1])

	if isinstance(body[-1], ast.If):
		insert_returns(body[-1].body)
		insert_returns(body[-1].orelse)

	if isinstance(body[-1], ast.With):
		insert_returns(body[-1].body)


class Owner(commands.Cog, name="Owner"):
	def __init__(self, client):
		self.client = client

	@commands.command()
	@commands.is_owner()
	async def _tsh(self, ctx, *, message: str = None):
		data = await self.client.database.sel_user(ctx.author)
		multi = (await self.client.database.sel_guild(ctx.guild))["exp_multi"]
		data.update({"multi": multi})
		result = await self.client.template_engine.render(ctx.message, ctx.author, data, message)
		await ctx.send(result)

	@commands.command(aliases=["eval"])
	@commands.is_owner()
	async def _e(self, ctx, *, cmd):
		fn_name = "_eval_expr"
		cmd = cmd.strip("` ")
		cmd = "\n".join(f"    {i}" for i in cmd.splitlines())
		body = f"async def {fn_name}():\n{cmd}"
		parsed = ast.parse(body)
		body = parsed.body[0].body
		insert_returns(body)
		env = {
			"client": self.client,
			"discord": discord,
			"os": os,
			"commands": commands,
			"ctx": ctx,
			"get": get,
			"__import__": __import__,
			"database": self.client.database,
		}
		exec(compile(parsed, filename="<ast>", mode="exec"), env)

		try:
			result = await eval(f"{fn_name}()", env)
		except Exception as e:
			await ctx.send(repr(e))
			return

		if result is not None:
			await ctx.send(result)
		elif result is None:
			return

	@commands.command()
	@commands.is_owner()
	async def _rest_cd(self, ctx, *, command: str):
		command = self.client.get_command(command)
		command.reset_cooldown(ctx)


def setup(client):
	client.add_cog(Owner(client))
