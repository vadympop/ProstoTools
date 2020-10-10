import discord
import datetime
import os
import json
import random
import requests
import io
import asyncio
import typing
import sqlite3
import ast
from discord.ext import commands, tasks
from discord.utils import get
from discord.voice_client import VoiceClient
from discord.ext.commands import Bot
from PIL import Image, ImageFont, ImageDraw, ImageFilter, ImageEnhance
from random import randint
from itertools import cycle
from configs import configs
from Tools.database import DB

def clear_commands( guild ):
	data = DB().sel_guild(guild = guild)
	purge = data['purge']
	return purge


def get_prefix( client, message ):
	data = DB().sel_guild(guild = message.guild)
	return str(data['prefix'])

	
class Help(commands.Cog, name = 'Help'):

	def __init__(self, client):
		self.client = client
		self.FOOTER = configs['FOOTER_TEXT']


	@commands.command()
	async def ehelp( self, ctx ):

		purge = clear_commands(ctx.guild)
		Prefix = get_prefix(self.client, ctx)
		await ctx.channel.purge( limit = purge )

		if ctx.author.guild_permissions.administrator: 

			emb = discord.Embed( title = '**Доступние команды:**', description = f'**Префикс на этом сервере - {Prefix}, если команды после двое-точия значит их надо использовать как групу, пример: "В хелп - група: команда, надо писать - група команда", если надо ввести названия чего-либо с пробелом, укажите эго в двойных кавычках**', colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )

			emb.add_field( name = f'Модераторськие команды - {Prefix}moderate', value = '` kick  ban  un-ban  mute  un-mute  warn  clear-warns  vmute ` \n ` un-vmute  slow-mode  clear  temp-role  warns  soft-ban  un-soft-ban `', inline = False )
			emb.add_field( name = f'Shop команды - {Prefix}economy', value = '` profile  shop-list  invertory  buy  crime  send-money  add-cash `\n` remove-cash  text-channel  remove-role  open  rob  -reputation `\n` +reputation  top  set-profile-color  daily  my-transactions `', inline = False )
			emb.add_field( name = f'Работы - {Prefix}works', value = '` work: loader  treasure-hunter  barman  cleaner  window-washer `', inline = False )
			emb.add_field( name = f'Кланы - {Prefix}clans(В разработке)', value = '` clan: create  accept  denied  invite  transownship  edit  delete `\n` leave  kick  list  visit  members  info `', inline = False )
			emb.add_field( name = f'Утилиты - {Prefix}utils', value = '` settings  ban-list  anti-rade  voice-channel  server-stats  mass-role  list-moderators `', inline = False )
			emb.add_field( name = f'Развлечения - {Prefix}games', value = '` create-qrcode  dcode-qrcode  flags  8ball  wiki  fox  cat  dog  koala `\n` bird  meme `', inline = False )
			emb.add_field( name = f'Другое - {Prefix}different', value = '` feedback  user-info  user-send  send-guild-idea `\n` user-avatar  message-forward  random-number  server-info `\n` say  invite  info `', inline = False )

			emb.set_footer( text = f'Вызвал: {ctx.author.name}', icon_url = ctx.author.avatar_url )

			await ctx.send( embed = emb )

		else:

			emb = discord.Embed( title = '**Доступние команды:**', description = f'**Префикс на этом сервере - {Prefix}, если команды после двое-точия значит их надо использовать как групу, пример: "В хелп - група: команда, надо писать - група команда", если надо ввести названия чего-либо с пробелом, укажите эго в двойных кавычках**', colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )

			emb.add_field( name = f'Модераторськие команды - {Prefix}moderate', value = '` warns `', inline = False )
			emb.add_field( name = f'Shop команды - {Prefix}economy', value = '` profile  shop-list  invertory  buy  crime  send-money  text-channel  open `\n` rob  -reputation  +reputation  top  set-profile-color  daily `', inline = False )
			emb.add_field( name = f'Работы - {Prefix}works', value = '` work: loader  treasure-hunter  barman  cleaner  window-washer `', inline = False )
			emb.add_field( name = f'Кланы - {Prefix}clans(В разработке)', value = '` clan: create  accept  denied  invite  transownship  edit  delete  leave `\n` kick  list  visit  members  info `', inline = False )
			emb.add_field( name = f'Развлечения - {Prefix}games', value = '` create-qrcode  dcode-qrcode  flags  8ball  wiki  fox  cat  dog  koala `\n` bird  meme `', inline = False )
			emb.add_field( name = f'Другое - {Prefix}different', value = '` feedback  user-info  user-send  send-guild-idea  user-avatar `\n` message-forward  random-number  server-info `\n` say  invite  info `', inline = False )

			emb.set_footer( text = f'Вызвал: {ctx.author.name}', icon_url = ctx.author.avatar_url )

			await ctx.send( embed = emb )		


	@commands.command()
	async def works( self, ctx ):

		purge = clear_commands(ctx.guild)
		Prefix = get_prefix(self.client, ctx)
		await ctx.channel.purge( limit = purge )

		emb = discord.Embed( title = 'Категория команд - works', description = '[Пример] - требуется, |Пример| - необязательно', colour = discord.Color.green() )
		emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
		
		emb.add_field( name = f'{Prefix}loader', value = '**Работа грузчиком. Получает от 80$ до 100$, можна работать с 3 уровня, кулдавн 3 часа после 2 попыток**', inline = False )
		emb.add_field( name = f'{Prefix}treasure-hunter', value = '**Работа кладо искателем. Получает от 0$(Ты ничего не нашёл) до 500$, можна работать с 2 уровня, нужно купить апарат за 500$ или второго уровня за 1000$(На 20% больше найти клад), кулдавн 5 часов**', inline = False )
		emb.add_field( name = f'{Prefix}barman', value = '**Работа барменом. Получает 150$ + чаевые до 50$, можна работать с 4 уровня, кулдавн 3 часа после 2 попыток**', inline = False )
		emb.add_field( name = f'{Prefix}cleaner', value = '**Работа уборщиком. Получает от 40$ до 50$, уровень пользователя не важен, кулдавн 2 часа после 3 попыток**', inline = False )
		emb.add_field( name = f'{Prefix}window-washer', value = '**Работа мойщиком окон. Получает от 250$ до 300$, можна работать с 5 уровня, может упасть и потерять 300$, кулдавн 5 часов**', inline = False )

		emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )

		await ctx.send( embed = emb )


	@commands.command()
	async def help(self, ctx, cog_name = None):
		purge = clear_commands(ctx.guild)
		DB().add_amout_command(entity=ctx.command.name)
		await ctx.channel.purge( limit = purge )
		exceptions = ['Help', 'Loops', 'Events', 'Owner', 'Errors']
		groups = ['settings', 'works']
		moder_roles = DB().sel_guild(guild = ctx.guild)['moder_roles']
		state = False
		group_name = ''
		locks = {
			'Different': 6,
			'Economy': 6,
			'Games': 7,
			'Moderate': 6,
			'Settings': 3,
			'Utils': 5,
			'Works': 7
		}
		Prefix = get_prefix(self.client, ctx)

		def add_command_loop(command, commands, count, group_name):
			try:
				for c in command.commands:
					if not c.hidden:
						if command.brief != 'True':
							commands += f' {Prefix}{c.name} '
							count += 1
							group_name = command.name
						else:
							for role_id in moder_roles:
								role = get(ctx.guild.roles, id = role_id)
								if role in ctx.author.roles:
									state = True
									break
							
							if state or ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
								commands += f' {Prefix}{c.name} '
								count += 1
								group_name = command.name
					else:
						if ctx.author.guild_permissions.administrator:
							commands += f' {Prefix}{c.name} '
							count += 1
							group_name = command.name
								
					if count >= locks[soft_cog_name]:
						count = 0
						commands += '`\n`'
			except:
				commands += f' {Prefix}{command.name} '

			return [commands, count, group_name]

		emb_1 = discord.Embed( title = '**Доступние команды:**', description = f'**Префикс на этом сервере - **`{Prefix}`**, если команды после двое-точия значит их надо использовать как групу, пример: "В хелп - група: команда, надо писать - група команда", если надо ввести названия чего-либо с пробелом, укажите эго в двойных кавычках**', colour = discord.Color.green() )
		if not cog_name:
			for soft_cog_name in self.client.cogs:
				if soft_cog_name in exceptions:
					continue
				else:
					cog = self.client.get_cog(soft_cog_name)
					commands = ''
					count = 0
					for command in cog.get_commands():
						if not command.hidden:
							if command.brief != 'True':
								commands, count, group_name = add_command_loop(command, commands, count, group_name)

								count += 1
								if count >= locks[soft_cog_name]:
									count = 0
									commands += '`\n`'
							else:
								for role_id in moder_roles:
									role = get(ctx.guild.roles, id = role_id)
									if role in ctx.author.roles:
										state = True
										break
								
								if state or ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
									commands, count, group_name = add_command_loop(command, commands, count, group_name)

									count += 1
									if count >= locks[soft_cog_name]:
										count = 0
										commands += '`\n`'
						else:
							if ctx.author.guild_permissions.administrator:
								commands, count, group_name = add_command_loop(command, commands, count, group_name)

								count += 1
								if count >= locks[soft_cog_name]:
									count = 0
									commands += '`\n`'
					if commands != '':

						if soft_cog_name.lower() in groups:
							value = f'` {group_name.lower()}: {commands}`'
						else:
							value = f'`{commands}`'

						emb_1.add_field(name = f'Категория команд: {soft_cog_name.capitalize()} - {Prefix}help {soft_cog_name.lower()}', value = value, inline = False)

			emb_1.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb_1.set_footer( text = f'Вызвал: {ctx.author.name}', icon_url = ctx.author.avatar_url )

			await ctx.send(embed = emb_1)
			return

		if cog_name.capitalize() not in self.client.cogs:
			emb = discord.Embed(title = 'Ошибка!', description = 'Такой категории нет, введите названия правильно. Список доступных категорий: different, economy, moderate, games, settings, utils, works', colour = discord.Color.green())
			
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )

			await ctx.send(embed = emb)
			return

		emb_2 = discord.Embed(title = f'Категория команд - {cog_name.capitalize()}', description = '[Пример] - требуется, |Пример| - необязательно', colour = discord.Color.green())
		cog = self.client.get_cog(cog_name.capitalize())
		for c in cog.get_commands():
			emb_2.add_field(name = f'{Prefix}{c.usage}', value = f'{c.description[2:-2]}.', inline = False)

		emb_2.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
		emb_2.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )

		await ctx.send(embed = emb_2)	


def setup( client ):
	client.add_cog(Help(client))
