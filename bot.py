import discord
import datetime
from tools.http import RandomAPI
from tools.cache import CacheManager
from tools.database import DB
from tools import Utils, Commands, template_engine as temp_eng
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
	"cogs.utils",
	"cogs.works",
	"cogs.show_configs",
	"cogs.settings",
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
	"events.audit",
	"events.other",
	"events.reactions_commands",
	"events.auto_reactions",
	"events.custom_commands",
	"events.autoresponders",
	"events.anti_flud",
	"events.anti_invite",
	"events.on_edit_command",
	"events.captcha",
	"events.anti_caps"
)


class ProstoTools(commands.AutoShardedBot):
	def __init__(self, intents, prefix):
		super().__init__(
			command_prefix=prefix,
			intents=intents,
			allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False),
			max_messages=500,
			case_insensitive=True
		)
		self.remove_command("help")
		self.config = Config
		self.cache = CacheManager()
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
		self.launched_at = datetime.datetime.utcnow()
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
	prefix = await client.database.get_prefix(guild=message.guild)
	return commands.when_mentioned_or(*(str(prefix), ))(client, message)


base_intents = discord.Intents(
	guilds=True,
	members=True,
	bans=True,
	emojis=True,
	voice_states=True,
	presences=True,
	messages=True,
	guild_reactions=True
)
client = ProstoTools(intents=base_intents, prefix=get_prefix)


def start_bot():
	for extension in extensions:
		try:
			client.load_extension(extension)
		except Exception as e:
			logger.error(
				f"[PT-SYSTEM-ERROR]:::An error occurred in the cog {extension}:\n{repr(e)}"
			)
		else:
			logger.info(f"[PT-SYSTEM-COG]:::{extension} - Loaded")
	client.load_extension("jishaku")
	client.add_command(buy)
	client.add_check(client.utils.global_command_check)


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
	client.run(client.config.TOKEN)
