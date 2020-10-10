import discord
import os
import asyncio
import json
import colorama
import traceback
import datetime
from colorama import *
from discord.ext import commands
from discord.utils import get
from configs import configs
from Tools.database import DB
init()

class Client(commands.AutoShardedBot):
	def __init__(self, command_prefix, case_insensitive, intents):
		super().__init__(command_prefix=command_prefix, case_insensitive=case_insensitive, intents=intents)
	

	def clear_commands(self, guild):
		data = DB().sel_guild(guild=guild)
		purge = data['purge']
		return purge
	

	def txt_dump(self, filename, filecontent):
		with open( filename, 'w', encoding='utf-8' ) as f:
			f.writelines( filecontent )


	def txt_load(self, filename):
		with open( filename, 'r', encoding='utf-8' ) as f:
			return f.read()

	def get_guild_prefix(self, ctx):
		data = DB().sel_guild(guild=ctx.guild)
		return str(data['prefix'])
	

def get_prefix(client, message):
	data = DB().sel_guild(guild = message.guild)
	return str(data['prefix'])

intents = discord.Intents.all()
client = Client(command_prefix=get_prefix, case_insensitive=True, intents=intents)
client.remove_command('help')
load_error = ''
now_date = str(datetime.datetime.today())[:-16]
log_file = f'./Data/Logs/log-{now_date}.txt'
space = ''

try:
	log = client.txt_load(log_file)
except:
	client.txt_dump(log_file, space)
	log = client.txt_load(log_file)

@client.command()
@commands.is_owner()
async def load(ctx, extension):
	client.load_extension(f'Cogs.{extension}')
	print(Fore.GREEN+f'[PT-SYSTEM-COG]:::{extension.upper()} - Loaded')


@client.command()
@commands.is_owner()
async def unload(ctx, extension):
	client.unload_extension(f'Cogs.{extension}')
	print(Fore.GREEN+f'[PT-SYSTEM-COG]:::{extension.upper()} - Unloaded')


for filename in os.listdir('./Cogs'):
	if filename.endswith('.py'):
		try:
			client.load_extension(f'Cogs.{filename[:-3]}')
		except Exception as e:
			print( Fore.RED+f'[PT-SYSTEM-ERROR]:::An error occurred in the cog {filename[:-3].upper()}' )
			load_error = load_error+f'\n\n=============================================================\nВремя: {str(datetime.datetime.today())}\n\nОшибка:\n{str(traceback.format_exc())}\n============================================================='
			load_error = log+load_error
			client.txt_dump(log_file, load_error)
		else:
			print( Fore.GREEN+f'[PT-SYSTEM-COG]:::{filename[:-3].upper()} - Loaded')

print(Fore.RESET)
client.run(configs['TOKEN'])