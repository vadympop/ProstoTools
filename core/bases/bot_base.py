import discord
import aiohttp
import datetime
import logging

from cogs.economy.buy_cmd import buy
from core.context import Context
from core.http import RandomAPI, HTTPClient
from core.services.cache import Cache
from core.services.database import Database
from core.services.api import API
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
        self.config = None
        self.http_client = None
        self.cache = None
        self.low_level_api = None
        self.database = None
        self.utils = None
        self.random_api = None
        self.support_commands = None
        self.template_engine = None
        self.launched_at = datetime.datetime.utcnow()

    async def on_connect(self):
        logger.info(f"{self.user} is connected to discord server")
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="prosto-tools.ml | p.help"
            )
        )
        await self.cache.run()
        await self.low_level_api.run()
        self.http_client.prepare(aiohttp.ClientSession(loop=self.loop))

    async def on_ready(self):
        logger.info(f"{self.user} is ready to work")

    async def on_disconnect(self):
        logger.info(f"{self.user} is disconnected from discord server")

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=cls or Context)

    async def close(self):
        await self.http_client.close()
        await self.low_level_api.close()
        await super().close()

    async def on_message(self, message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        if message.content.strip() in (
            f"<@{self.user.id}>",
            f"<@!{self.user.id}>"
        ):
            await message.channel.send(
                f':information_source: Мой префикс на этом сервере - `{await self.database.get_prefix(message.guild)}`'
            )

        await self.process_commands(message)

    async def on_message_edit(self, before, after):
        if before.content != after.content:
            await self.process_commands(after)

    async def is_owner(self, user: discord.User):
        if user.id in (377485441114439693, 660110922865704980):
            return True

        return await super().is_owner(user)

    async def on_command(self, ctx):
        if ctx.valid:
            await self.database.add_stat_counter(entity=ctx.command.name)

    def setup_extensions(self):
        for extension in self.config.EXTENSIONS:
            try:
                self.load_extension(extension)
            except Exception as e:
                logger.error(f"An error occurred when loading cog {extension}:\n{repr(e)}")
            else:
                logger.info(f"{extension} was loaded")

        self.load_extension("jishaku")

    def setup_modules(self):
        self.config = Config
        self.http_client = HTTPClient()
        self.cache = Cache()
        self.low_level_api = API(self, port=1111, host='0.0.0.0')
        self.database = Database(client=self)
        self.utils = Utils(client=self)
        self.random_api = RandomAPI(client=self)
        self.support_commands = SupportCommands(client=self)
        self.template_engine = temp_eng
        self.template_engine.client = self

    def run(self):
        self.setup_modules()
        self.setup_extensions()
        self.add_command(buy)
        self.add_check(self.utils.global_command_check)
        super().run(self.config.TOKEN)