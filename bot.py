import logging
from colorama import *
from discord.ext import commands

from log import setup
from core.bases.bot_base import ProstoTools


init()
setup()

logger = logging.getLogger(__name__)
prostotools = ProstoTools()


@prostotools.command()
@commands.is_owner()
async def load(ctx, extension):
	ctx.bot.load_extension(extension)
	logger.info(f"{extension} was loaded")


@prostotools.command()
@commands.is_owner()
async def unload(ctx, extension):
	ctx.bot.unload_extension(extension)
	logger.info(f"{extension} was unloaded")


@prostotools.command()
@commands.is_owner()
async def reload(ctx, extension):
	if extension.lower() == "all":
		for extension in ctx.bot.config.EXTENSIONS:
			try:
				prostotools.unload_extension(extension)
				prostotools.load_extension(extension)
			except:
				logger.error(f"An error occurred when loading cog {extension}")
			else:
				logger.info(f"{extension} was reloaded")
		await ctx.message.add_reaction("✅")
		return

	try:
		ctx.bot.unload_extension(extension)
		ctx.bot.load_extension(extension)
	except:
		logger.error(f"An error occurred when loading cog {extension}")
		return

	logger.info(f"{extension} was reloaded")
	await ctx.message.add_reaction("✅")


if __name__ == "__main__":
	prostotools.run()
