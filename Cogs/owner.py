import discord
import datetime
import os
import json
import asyncio
import ast
import math
import random
import Tools.template_engine as TemplateEngine
from discord.ext import commands
from colorama import *
from discord.utils import get
from discord.voice_client import VoiceClient
from discord.ext.commands import Bot
from configs import configs
from Tools.database import DB
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


global Footer
Footer = configs["FOOTER_TEXT"]


class Owner(commands.Cog, name="Owner"):
	def __init__(self, client):
		self.client = client

	@commands.command()
	async def test(self, ctx, member: discord.Member = None, *, message: str = None):
		template = Template(message, autoescape=True)
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
		await ctx.send(ctx.kwargs)
		await ctx.send(
			result.replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", '"')
		)

	@commands.command()
	@commands.is_owner()
	async def restart(self, ctx):
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		emb = discord.Embed(title="Перезагрузка бота", colour=discord.Color.green())
		emb.set_image(url="https://i.gifer.com/Jx6X.gif")
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=Footer, icon_url=self.client.user.avatar_url)
		msg = await ctx.send(embed=emb)

		e = discord.Embed(title="Бот перезагружен", colour=discord.Color.green())
		e.set_image(url="http://www.clipartbest.com/cliparts/9iz/6Rp/9iz6RpkGT.gif")
		e.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		e.set_footer(text=Footer, icon_url=self.client.user.avatar_url)
		await asyncio.sleep(2)

		await msg.edit(embed=e)
		await self.client.logout()
		await os.system("python bot.py")

	@commands.command()
	@commands.is_owner()
	async def cls(self, ctx):
		emb = discord.Embed(
			title="Ожидайте... Происходит очистка консоли...",
			colour=discord.Color.green(),
		)
		emb.set_image(url="https://i.gifer.com/Jx6X.gif")
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=Footer, icon_url=self.client.user.avatar_url)
		msg = await ctx.send(embed=emb)

		e = discord.Embed(
			title="Консоль успешно очищена!", colour=discord.Color.green()
		)
		e.set_image(url="http://www.clipartbest.com/cliparts/9iz/6Rp/9iz6RpkGT.gif")
		e.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		e.set_footer(text=Footer, icon_url=self.client.user.avatar_url)

		await asyncio.sleep(3)
		await msg.edit(embed=e)
		os.system("cls")

	@commands.command(aliases=["print"])
	@commands.is_owner()
	async def p(self, ctx, *, arg):
		print(arg)

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

	@commands.command()
	@commands.is_owner()
	async def reload(self, ctx, extension):
		if extension.lower() == 'all':
			for filename in os.listdir("./Cogs"):
				if filename.endswith(".py"):
					try:
						self.client.unload_extension(f"Cogs.{filename[:-3]}")
						self.client.load_extension(f"Cogs.{filename[:-3]}")
					except:
						print(
							Fore.RED
							+ f"[PT-SYSTEM-ERROR]:::An error occurred in the cog {filename[:-3].upper()}"
						)
						await ctx.message.add_reaction('❌')
					else:
						print(Fore.GREEN + f"[PT-SYSTEM-COG]:::{filename.upper()} - Reloaded")
			await ctx.message.add_reaction('✅')
			return
			
		try:	
			self.client.unload_extension(f"Cogs.{extension}")
			self.client.load_extension(f"Cogs.{extension}")
		except:
			print(
				Fore.RED
				+ f"[PT-SYSTEM-ERROR]:::An error occurred in the cog {extension.upper()}"
			)
			return 
		print(Fore.GREEN + f"[PT-SYSTEM-COG]:::{extension.upper()} - Reloaded")
		await ctx.message.add_reaction('✅')


def setup(client):
	client.add_cog(Owner(client))
