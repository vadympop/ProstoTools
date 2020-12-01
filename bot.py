import discord
import traceback
import datetime

from cogs.tools import DB
from cogs.tools import template_engine as temp_eng

from loguru import logger
from colorama import *
from discord.ext import commands
from configs import configs


init()
logger.add("data/logs/prostotoolsbot.log", format="{time} {level} {message}", level="ERROR", rotation="1 day", compression="zip")
extensions = [
	"cogs.clans",
	"cogs.different",
	"cogs.economy",
	"cogs.errors",
	"cogs.events",
	"cogs.games",
	"cogs.help",
	"cogs.loops",
	"cogs.moderate",
	"cogs.owner",
	"cogs.settings",
	"cogs.utils",
	"cogs.works",
]

class Client(commands.AutoShardedBot):
	def __init__(self, command_prefix, case_insensitive, intents):
		super().__init__(
			command_prefix=command_prefix,
			case_insensitive=case_insensitive,
			intents=intents,
		)
		self.remove_command("help")

	async def on_ready(self):
		logger.info(f"[PT-SYSTEM-LOGGING]:::{self.user.name} is connected to discord server")
		await self.change_presence(
			status=discord.Status.online, activity=discord.Game(" *help | *invite ")
		)

	def clear_commands(self, guild):
		data = DB().sel_guild(guild=guild)
		purge = data["purge"]
		return purge

	def txt_dump(self, filename, filecontent):
		with open(filename, "w", encoding="utf-8") as f:
			f.writelines(filecontent)

	def txt_load(self, filename):
		with open(filename, "r", encoding="utf-8") as f:
			return f.read()

	def get_guild_prefix(self, ctx):
		data = DB().sel_guild(guild=ctx.guild)
		return str(data["prefix"])


def get_prefix(client, message):
	data = DB().sel_guild(guild=message.guild)
	return str(data["prefix"])


client = Client(
	command_prefix=get_prefix, case_insensitive=True, intents=discord.Intents.all()
)
temp_eng.client = client

@client.command()
@commands.is_owner()
async def load(ctx, extension):
	client.load_extension(extension)
	logger.info(f"[PT-SYSTEM-COG]:::{extension} - Loaded")

@client.command()
@commands.is_owner()
async def unload(ctx, extension):
	client.unload_extension(extension)
	logger.info(f"[PT-SYSTEM-COG]:::{extension} - Unloaded")

@client.command()
@commands.is_owner()
async def reload(ctx, extension):
	if extension.lower() == 'all':
		for extension in extensions:
			try:
				client.unload_extension(extension)
				client.load_extension(extension)
			except:
				logger.error(f"[PT-SYSTEM-ERROR]:::An error occurred in the cog {extension}")
			else:
				logger.info(f"[PT-SYSTEM-COG]:::{extension} - Reloaded")
		await ctx.message.add_reaction('✅')
		return
	
	try:	
		client.unload_extension(extension)
		client.load_extension(extension)
	except:
		logger.error(f"[PT-SYSTEM-ERROR]:::An error occurred in the cog {extension}")
		return
	logger.info(f"[PT-SYSTEM-COG]:::{extension} - Reloaded")
	await ctx.message.add_reaction('✅')

def main():
	for extension in extensions:
		try:
			client.load_extension(extension)
		except:
			logger.error(f"[PT-SYSTEM-ERROR]:::An error occurred in the cog {extension}")
		else:
			logger.info(f"[PT-SYSTEM-COG]:::{extension} - Reloaded")

if __name__ == "__main__":
	main()
	client.run(configs["TOKEN"])