from .bot_base import ProstoTools
from discord.ext import commands


class BaseCog(commands.Cog):
    def __init__(self, client: ProstoTools):
        self.client: ProstoTools = client
        self.FOOTER = self.client.config.FOOTER_TEXT