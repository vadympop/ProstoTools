import discord
import datetime
from tools.http import RandomAPI
from tools import DB, Utils, Commands, template_engine as temp_eng
from cogs.economy.buy_cmd import buy
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
	"cogs.economy.economy",
	"cogs.fun.other",
	"cogs.fun.edit_image",
	"cogs.fun.random_image",
	"cogs.moderate",
	"cogs.owner",
	"cogs.settings",
	"cogs.utils",
	"cogs.works",
	"cogs.help",
	"tasks.message_stat",
	"tasks.other",
	"tasks.punishments",
	"tasks.server_stat",
	"tasks.send_data",
	"tasks.bot_stat",
	"events.errors",
	"events.custom_voice_channel",
	"events.join",
	"events.leave",
	"events.leveling",
	"events.logs",
	"events.other",
	"events.reactions_commands",
	"events.auto_reactions",
	"events.custom_commands",
	"events.autoresponders"
)


class Client(commands.AutoShardedBot):
	def __init__(self, command_prefix, case_insensitive, intents):
		super().__init__(
			command_prefix=command_prefix,
			case_insensitive=case_insensitive,
			intents=intents,
		)
		self.remove_command("help")
		self.config = Config
		self.database = DB(client=self)
		self.utils = Utils(client=self)
		self.random_api = RandomAPI()
		self.support_commands = Commands(client=self)
		self.template_engine = temp_eng
		self.template_engine.client = self

	async def on_ready(self):
		logger.info(
			f"[PT-SYSTEM-LOGGING]:::{self.user.name} is connected to discord server"
		)
		await self.change_presence(
			status=discord.Status.online, activity=discord.Game(" p.help | p.invite ")
		)
		self.launched_at = datetime.datetime.now()
		await self.database.prepare()

	async def on_disconnect(self):
		logger.info(
			f"[PT-SYSTEM-LOGGING]:::{self.user.name} is disconnected from discord server"
		)

	def txt_dump(self, filename, filecontent):
		with open(filename, "w+", encoding="utf-8") as f:
			f.writelines(filecontent)

	def txt_load(self, filename):
		with open(filename, "r", encoding="utf-8") as f:
			return f.read()


async def get_prefix(client, message):
	if message.guild is None:
		return "p."
	return client.database.get_prefix(guild=message.guild)


base_intents = discord.Intents.none()
base_intents.guilds = True
base_intents.members = True
base_intents.bans = True
base_intents.emojis = True
base_intents.voice_states = True
base_intents.presences = True
base_intents.guild_messages = True
base_intents.guild_reactions = True
client = Client(
	command_prefix=get_prefix, case_insensitive=True, intents=base_intents
)


def start_bot():
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
	start_bot()
	client.add_command(buy)
	client.run(client.config.TOKEN)
