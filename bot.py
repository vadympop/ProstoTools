import discord
import datetime
import asyncio

from tools import DB
from tools import template_engine as temp_eng

from loguru import logger
from colorama import *
from discord.ext import commands
from configs import Config


init()
logger.add(
	"data/logs/prostotoolsbot.log",
	format="{time} {level} {message}",
	level="ERROR",
	rotation="1 day",
	compression="zip",
)
extensions = (
	"cogs.clans",
	"cogs.different",
	"cogs.economy",
	"cogs.games",
	"cogs.help",
	"cogs.moderate",
	"cogs.owner",
	"cogs.settings",
	"cogs.utils",
	"cogs.works",
	"tasks.message_stat",
	"tasks.other",
	"tasks.punishments",
	"tasks.server_stat",
	"tasks.send_data",
	"events.errors",
	"events.custom_voice_channel",
	"events.join",
	"events.leave",
	"events.leveling",
	"events.logs",
	"events.other",
	"events.reactions_commands",
)


class Client(commands.AutoShardedBot):
	def __init__(self, command_prefix, case_insensitive, intents):
		super().__init__(
			command_prefix=command_prefix,
			case_insensitive=case_insensitive,
			intents=intents,
		)
		self.remove_command("help")

	async def on_ready(self):
		logger.info(
			f"[PT-SYSTEM-LOGGING]:::{self.user.name} is connected to discord server"
		)
		await self.change_presence(
			status=discord.Status.online, activity=discord.Game(" *help | *invite ")
		)
		self.launched_at = datetime.datetime.now()

	async def clear_commands(self, guild):
		return (await self.database.sel_guild(guild=guild))["purge"]

	def txt_dump(self, filename, filecontent):
		with open(filename, "w", encoding="utf-8") as f:
			f.writelines(filecontent)

	def txt_load(self, filename):
		with open(filename, "r", encoding="utf-8") as f:
			return f.read()

	async def get_guild_prefix(self, ctx):
		return self.database.get_prefix(guild=ctx.guild)


async def get_prefix(client, message):
	return client.database.get_prefix(guild=message.guild)


client = Client(
	command_prefix=get_prefix, case_insensitive=True, intents=discord.Intents.all()
)
client.config = Config
client.database = DB(client=client)
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
	if extension.lower() == "all":
		for extension in extensions:
			try:
				client.unload_extension(extension)
				client.load_extension(extension)
			except:
				logger.error(
					f"[PT-SYSTEM-ERROR]:::An error occurred in the cog {extension}"
				)
			else:
				logger.info(f"[PT-SYSTEM-COG]:::{extension} - Reloaded")
		await ctx.message.add_reaction("✅")
		return

	try:
		client.unload_extension(extension)
		client.load_extension(extension)
	except:
		logger.error(f"[PT-SYSTEM-ERROR]:::An error occurred in the cog {extension}")
		return
	logger.info(f"[PT-SYSTEM-COG]:::{extension} - Reloaded")
	await ctx.message.add_reaction("✅")


if __name__ == "__main__":
	for extension in extensions:
		try:
			client.load_extension(extension)
		except Exception as e:
			raise e
			logger.error(
				f"[PT-SYSTEM-ERROR]:::An error occurred in the cog {extension}"
			)
		else:
			logger.info(f"[PT-SYSTEM-COG]:::{extension} - Loaded")
	client.run(client.config.TOKEN)
