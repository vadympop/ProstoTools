import discord
from configs import configs
from Tools.database import DB
from discord.ext import commands

class Clans(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.FOOTER = configs['FOOTER_TEXT']


def setup(client):
    client.add_cog(Clans(client))