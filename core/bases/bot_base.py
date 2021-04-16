import discord
import aiohttp
import datetime
import logging

from cogs.economy.buy_cmd import buy
from core.http import RandomAPI, HTTPClient
from core.services.cache import Cache
from core.services.database import Database
from core.utils.other import get_prefix
from core import Utils, SupportCommands, template_engine as temp_eng
from core.config import Config
from discord.ext import commands

logger = logging.getLogger(__name__)


class ProstoTools(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            intents=discord.Intents(
                guilds=True,
                members=True,
                bans=True,
                emojis=True,
                voice_states=True,
                messages=True,
                guild_reactions=True
            ),
            allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False),
            max_messages=1500,
            case_insensitive=True
        )
        self.remove_command("help")
        self.config = Config
        self.http_client = HTTPClient()
        self.cache = Cache()
        self.database = Database(client=self)
        self.utils = Utils(client=self)
        self.random_api = RandomAPI(client=self)
        self.support_commands = SupportCommands(client=self)
        self.template_engine = temp_eng
        self.template_engine.client = self
        self.launched_at = datetime.datetime.utcnow()

    async def on_connect(self):
        logger.info(
            f"{self.user} is connected to discord server"
        )
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name=" {prefix}help | {prefix}invite ".format(prefix=self.config.DEF_PREFIX)
            )
        )
        await self.cache.run()
        self.http_client.prepare(aiohttp.ClientSession(loop=self.loop))

    async def on_ready(self):
        logger.info(
            f"{self.user} is ready to work"
        )

    async def on_disconnect(self):
        logger.info(
            f"{self.user} is disconnected from discord server"
        )

    async def close(self):
        await self.http_client.close()
        await super().close()

    async def on_message_edit(self, before, after):
        await self.process_commands(after)

    async def is_owner(self, user: discord.User):
        if user.id in (377485441114439693, 660110922865704980):
            return True

        return await super().is_owner(user)

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        if ctx.valid:
            await ctx.trigger_typing()
        await self.invoke(ctx)

    async def on_command(self, ctx):
        if ctx.valid:
            await self.database.add_stat_counter(entity=ctx.command.name)

    def txt_dump(self, filename, filecontent):
        with open(filename, "w+", encoding="utf-8") as f:
            f.writelines(filecontent)

    def txt_load(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()

    def run(self):
        for extension in self.config.EXTENSIONS:
            try:
                self.load_extension(extension)
            except Exception as e:
                logger.error(f"An error occurred when loading cog {extension}:\n{repr(e)}")
            else:
                logger.info(f"{extension} was loaded")

        self.load_extension("jishaku")
        self.add_command(buy)
        self.add_check(self.utils.global_command_check)
        super().run(self.config.TOKEN)