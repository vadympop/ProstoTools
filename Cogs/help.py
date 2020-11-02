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
	
class Help(commands.Cog, name = 'Help'):

	def __init__(self, client):
		self.client = client
		self.FOOTER = configs['FOOTER_TEXT']
		self._names = []
		for cog in self.client.cogs:
			for command in self.client.get_cog(cog).get_commands():
				for alias in command.aliases:
					self._names.append(alias)
				self._names.append(command.name)
		self.commands = self._names


	@commands.command()
	async def works( self, ctx ):

		purge = self.client.clear_commands(ctx.guild)
		Prefix = self.get_prefix(self.client, ctx)
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
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )
		exceptions = ['Help', 'Loops', 'Events', 'Owner', 'Errors']
		groups = ['settings', 'works', 'clans']
		moder_roles = DB().sel_guild(guild = ctx.guild)['moder_roles']
		state = False
		group_name = ''
		locks = {
			'Different': 5,
			'Economy': 5,
			'Games': 7,
			'Moderate': 6,
			'Settings': 3,
			'Utils': 5,
			'Works': 7,
			'Clans': 3
		}
		PREFIX = self.client.get_guild_prefix(ctx)

		def add_command_loop(command, commands, count, group_name):
			try:
				for c in command.commands:
					if not c.hidden:
						if command.brief != 'True':
							commands += f' {PREFIX}{c.name} '
							count += 1
							group_name = command.name
						else:
							for role_id in moder_roles:
								role = get(ctx.guild.roles, id = role_id)
								if role in ctx.author.roles:
									state = True
									break
							
							if state or ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
								commands += f' {PREFIX}{c.name} '
								count += 1
								group_name = command.name
					else:
						if ctx.author.guild_permissions.administrator:
							commands += f' {PREFIX}{c.name} '
							count += 1
							group_name = command.name
								
					if count >= locks[soft_cog_name]:
						count = 0
						commands += '`\n`'
			except:
				commands += f' {PREFIX}{command.name} '

			return [commands, count, group_name]

		emb_1 = discord.Embed( title = '**Доступние команды:**', description = f'**Префикс на этом сервере - **`{PREFIX}`**, если команды после двое-точия значит их надо использовать как групу, пример: "В хелп - група: команда, надо писать - `[Префикс на сервере]група команда`", если надо ввести названия чего-либо с пробелом, укажите его в двойных кавычках**', colour = discord.Color.green() )
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

						emb_1.add_field(name = f'Категория команд: {soft_cog_name.capitalize()} - {PREFIX}help {soft_cog_name.lower()}', value = value, inline = False)

			emb_1.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb_1.set_footer( text = f'Вызвал: {ctx.author.name}', icon_url = ctx.author.avatar_url )
			await ctx.send(embed = emb_1)
			return

		if cog_name.capitalize() not in self.client.cogs:
			if cog_name.lower() not in self.commands:
				emb = discord.Embed(title = 'Ошибка!', description = 'Такой категории нет, введите названия правильно. Список доступных категорий: different, economy, moderate, games, settings, utils, works', colour = discord.Color.green())
				emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
				emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
				await ctx.send(embed = emb)
				return
			else:
				emb = discord.Embed(title=f'Команда: {PREFIX+cog_name.lower()}', description=self.client.get_command(cog_name.lower()).help, colour=discord.Color.green())
				emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				return

		emb_2 = discord.Embed(title = f'Категория команд - {cog_name.capitalize()}', description = '[Пример] - требуется, |Пример| - необязательно', colour = discord.Color.green())
		for c in self.client.get_cog(cog_name.capitalize()).get_commands():
			emb_2.add_field(name = f'{PREFIX}{c.usage}', value = f'{c.description[2:-2]}.', inline = False)
		emb_2.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
		emb_2.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
		await ctx.send(embed = emb_2)	


def setup( client ):
	client.add_cog(Help(client))
