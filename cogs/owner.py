import discord
import os
import asyncio
import ast
import math
import random

from tools import DB, template_engine as TemplateEngine

from discord.ext import commands
from colorama import *
from discord.utils import get
from jinja2 import Template

init()


def clear_commands(guild):
	data = DB().sel_guild(guild=guild)
	purge = data["purge"]
	return purge


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
	async def test(self, ctx, member: discord.Member = None, *, message: str = None):
		template = Template(message, autoescape=False)
		data = DB().sel_user(member)
		multi = DB().sel_guild(ctx.guild)["exp_multi"]
		data.update({"multi": multi})
		context = {
			"member": TemplateEngine.Member(member, data),
			"guild": TemplateEngine.Guild(member.guild),
			"channel": TemplateEngine.Channel(ctx.message.channel),
			"bot": TemplateEngine.User(self.client.user),
			"message": TemplateEngine.Message(ctx.message),
			"attributes": TemplateEngine.Attributes(ctx.args),
			"len": len,
			"math": math,
			"round": round,
			"random": random,
			"list": list,
			"int": int,
			"dict": dict,
			"str": str,
			"upper": lambda msg: msg.upper(),
			"lower": lambda msg: msg.lower(),
			"capitalize": lambda msg: msg.capitalize(),
			"format": lambda msg, **args: msg.format(args),
			"split": lambda msg, sdata: msg.split(sdata),
			"join": lambda msg, value: msg.join(value),
			"reverse": lambda msg: msg[::-1],
			"keys": lambda msg: msg.keys(),
			"items": lambda msg: msg.items(),
			"values": lambda msg: msg.values(),
			"replace": lambda msg, old, new: msg.replace(old, new),
			"contains": lambda msg, word: True if word in msg.split(" ") else False,
		}
		result = template.render(context)
		await ctx.send(result)

	@commands.command(aliases=["eval"])
	@commands.is_owner()
	async def e(self, ctx, *, cmd):
		fn_name = "_eval_expr"
		cmd = cmd.strip("` ")
		cmd = "\n".join(f"    {i}" for i in cmd.splitlines())
		body = f"async def {fn_name}():\n{cmd}"
		parsed = ast.parse(body)
		body = parsed.body[0].body
		insert_returns(body)
		env = {
			"client": ctx.bot,
			"discord": discord,
			"os": os,
			"commands": commands,
			"ctx": ctx,
			"get": get,
			"__import__": __import__,
		}
		exec(compile(parsed, filename="<ast>", mode="exec"), env)

		try:
			result = await eval(f"{fn_name}()", env)
		except Exception as e:
			await ctx.send(repr(e))
			return

		if result != None:
			await ctx.send(result)
		elif result == None:
			return

	@commands.command()
	@commands.is_owner()
	async def rest_cd(self, ctx, *, command: str):
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)
		command = self.client.get_command(command)
		command.reset_cooldown(ctx)


def setup(client):
	client.add_cog(Owner(client))
