import discord
import os
import json
import random
import asyncio
import math
import datetime
import colorama
import mysql.connector
from Tools.commands import Commands
from colorama import *
from discord.ext import commands, tasks
from discord.utils import get
from discord.voice_client import VoiceClient
from discord.ext.commands import Bot
from random import randint
from configs import configs
from Tools.database import DB
init()


class Events(commands.Cog, name = 'Events'):

	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(user = 'root', password = os.environ['DB_PASSWORD'], host = 'localhost', database = 'data')
		self.cursor = self.conn.cursor(buffered = True)
		self.FOOTER = configs['FOOTER_TEXT']
		self.MUTE_ROLE = configs['MUTE_ROLE']
		self.HELP_SERVER = configs['HELP_SERVER']
		

	@commands.Cog.listener()
	async def on_ready( self ):
		print( Fore.MAGENTA + f'[PT-SYSTEM-LOGGING]:::{self.client.user.name} is connected to discord server' + Fore.RESET )
		await self.client.change_presence( status = discord.Status.online, activity = discord.Game( ' *help | *invite ' ))


	@commands.Cog.listener()
	async def on_guild_join( self, guild ):
		emb = discord.Embed( title = 'Спасибо за приглашения нашего бота! Мы тебе всегда ради', description = f'**Стандартний префикс - *, команда помощи - *help, \nкоманда настроёк - *settings. Наш сервер поддержки: \n {self.HELP_SERVER}**', colour = discord.Color.green() )
		emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
		emb.set_footer( text = 'ProstoChelovek and Mr.Kola Copyright', icon_url = self.client.user.avatar_url )
		await guild.text_channels[0].send( embed = emb )

		DB().sel_guild(guild = guild)
		DB().add_amout_command(entity='guilds', add_counter=len(self.client.guilds))

		for member in guild.members:
			if not member.bot:
				DB().sel_user(target = member)

		guild_owner_bot = get(self.client.guilds, id = 717776571406090310)
		channel = guild_owner_bot.text_channels[3]
		invite = await guild.text_channels[0].create_invite(reason = 'For more information')

		emb_info = discord.Embed(title = f'Бот добавлен на новый сервер, всего серверов - {len(self.client.guilds)}', description = f'Названия сервера - `{guild.name}`\nАйди сервера - `{guild.id}`\nИнвайт - {invite}\nВладелец - `{guild.owner}`\nКол-во участников - `{guild.member_count}`')
		emb_info.set_thumbnail(url = guild.icon_url)
		await channel.send(embed = emb_info)


	@commands.Cog.listener()
	async def on_guild_remove( self, guild ):
		DB().add_amout_command(entity='guilds', add_counter=len(self.client.guilds))

		sql_1 = ("""DELETE FROM guilds WHERE guild_id = %s AND guild_id = %s""")
		val_1 = (guild.id, guild.id)

		self.cursor.execute(sql_1, val_1)
		self.conn.commit()

		for member in guild.members:
			sql_2 = ("""DELETE FROM users WHERE user_id = %s AND guild_id = %s""")
			val_2 = (member.id, guild.id)

			self.cursor.execute(sql_2, val_2)
			self.conn.commit()

		guild_owner_bot = get(self.client.guilds, id = 717776571406090310)
		channel = guild_owner_bot.text_channels[3]

		emb_info = discord.Embed(title = f'Бот изгнан из сервера, всего серверов - {len(self.client.guilds)}', description = f'Названия сервера - `{guild.name}`\nАйди сервера - `{guild.id}`\nВладелец - `{guild.owner}`\nКол-во участников - `{guild.member_count}`')
		emb_info.set_thumbnail(url = guild.icon_url)

		await channel.send(embed = emb_info)


	@commands.Cog.listener()
	async def on_raw_reaction_add( self, payload ):
		reaction = payload.emoji
		author = payload.member
		channel = self.client.get_channel(payload.channel_id)
		message = await channel.fetch_message(payload.message_id)
		member = message.author
		guild = message.guild
		data = DB().sel_guild(guild = guild)

		if data['auto_mod']['react_coomands']:
			if not author.bot:
				if author.guild_permissions.administrator:
					if reaction.name == '❌':
						try:
							await member.ban(reason = 'Нарушения правил')
						except:
							return

						emb = discord.Embed( description = f'**{author.mention} Забанил {member.mention}**' , colour = discord.Color.green() )
						
						emb.set_author( name = author.name, icon_url = author.avatar_url )
						emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )

						await message.channel.send( embed = emb )

						emb = discord.Embed( description = f'**Вы были забанены на сервере {message.guild.name}**', colour = discord.Color.green() )

						emb.set_author( name = author.name, icon_url = author.avatar_url )
						emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )

						await member.send( embed = emb )

					elif reaction.name == '🤐':
						emb = await Commands(self.client).main_mute(ctx = message, member = member, reason = 'Команды по реакциям: Нарушения правил', check_role = True)
						
						await message.channel.send(embed = emb)
					elif reaction.name == '💀':

						await member.kick( reason = 'Нарушения правил' )

						emb = discord.Embed( description = f'**{author.mention} Кикнул {member.mention}**' , colour = discord.Color.green() )
						
						emb.set_author( name = author.name, icon_url = author.avatar_url )
						emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
							
						await message.channel.send( embed = emb )


						emb = discord.Embed( description = f'**Администратор {author.mention} кикнул вас из сервера** ***{guild.name}***' , colour = discord.Color.green() )
						
						emb.set_author( name = author.name, icon_url = author.avatar_url )
						emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
						
						await member.send( embed = emb )


	@commands.Cog.listener()
	async def on_member_join( self, member ):
		DB().add_amout_command(entity='members', add_counter=len(self.client.users))

		if not member.bot:
			DB().sel_user(target = member)

		try:
			data = DB().sel_guild(guild = member.guild)['server_stats']
			async def edit_channel(channel_id: int, counter):
				channel = self.client.get_channel( channel_id )

				if counter >= 100:
					stats_channel_name = channel.name[6:]
				elif counter >= 10:
					stats_channel_name = channel.name[5:]
				elif counter < 10:
					stats_channel_name = channel.name[4:]

				await channel.edit( name = f'[{counter}] {stats_channel_name}' )

			for key in data.keys():
				if key == 'members':
					stats_channel_id = int(data['members'])
					count = len(' '.join(str(member.id) for member in member.guild.members if not member.bot and member.id != self.client.user.id).split(' '))
					await edit_channel(stats_channel_id, count)

				if key == 'bots':
					stats_channel_id = int(data['bots'])
					count = len(' '.join(str(bot.id) for bot in member.guild.members if bot.bot).split(' '))
					await edit_channel(stats_channel_id, count)
				
				if key == 'all':
					stats_channel_id = int(data['all'])
					count = member.guild.member_count
					await edit_channel(stats_channel_id, count)

		except:
			pass


	@commands.Cog.listener()
	async def on_member_remove( self, member ):
		DB().add_amout_command(entity='members', add_counter=len(self.client.users))

		try:
			data = DB().sel_guild(guild = member.guild)['server_stats']
			async def edit_channel(channel_id: int, counter):
				channel = self.client.get_channel( channel_id )

				if counter >= 100:
					stats_channel_name = channel.name[6:]
				elif counter >= 10:
					stats_channel_name = channel.name[5:]
				elif counter < 10:
					stats_channel_name = channel.name[4:]

				await channel.edit( name = f'[{counter}] {stats_channel_name}' )

			for key in data.keys():
				if key == 'members':
					stats_channel_id = int(data['members'])
					count = len(' '.join(str(member.id) for member in member.guild.members if not member.bot and member.id != self.client.user.id).split(' '))
					await edit_channel(stats_channel_id, count)

				if key == 'bots':
					stats_channel_id = int(data['bots'])
					count = len(' '.join(str(bot.id) for bot in member.guild.members if bot.bot).split(' '))
					await edit_channel(stats_channel_id, count)
				
				if key == 'all':
					stats_channel_id = int(data['all'])
					count = member.guild.member_count
					await edit_channel(stats_channel_id, count)

		except:
			pass


	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		try:
			data = DB().sel_guild(guild = channel.guild)['server_stats']
			if 'channels' in data.keys():
				channel_id = int(data['channels'])
				channel = self.client.get_channel( channel_id )
				counter = len(' '.join(str(channel.id) for channel in channel.guild.channels).split(' '))

				if counter >= 100:
					stats_channel_name = channel.name[6:]
				elif counter >= 10:
					stats_channel_name = channel.name[5:]
				elif counter < 10:
					stats_channel_name = channel.name[4:]

				await channel.edit( name = f'[{counter}] {stats_channel_name}' )
		except:
			pass


	@commands.Cog.listener()
	async def on_guild_channel_create(self, channel):
		try:
			data = DB().sel_guild(guild = channel.guild)['server_stats']
			if 'channels' in data.keys():
				channel_id = int(data['channels'])
				channel = self.client.get_channel( channel_id )
				counter = len(' '.join(str(channel.id) for channel in channel.guild.channels).split(' '))

				if counter >= 100:
					stats_channel_name = channel.name[6:]
				elif counter >= 10:
					stats_channel_name = channel.name[5:]
				elif counter < 10:
					stats_channel_name = channel.name[4:]

				await channel.edit( name = f'[{counter}] {stats_channel_name}' )
		except Exception as e:
			raise e


	@commands.Cog.listener()
	async def on_guild_role_create(self, role):
		try:
			data = DB().sel_guild(guild = role.guild)['server_stats']
			if 'roles' in data.keys():
				channel_id = int(data['roles'])
				channel = self.client.get_channel( channel_id )
				counter = len(' '.join(str(role.id) for role in role.guild.roles).split(' '))

				if counter >= 100:
					stats_channel_name = channel.name[6:]
				elif counter >= 10:
					stats_channel_name = channel.name[5:]
				elif counter < 10:
					stats_channel_name = channel.name[4:]

				await channel.edit( name = f'[{counter}] {stats_channel_name}' )
		except:
			pass


	@commands.Cog.listener()
	async def on_guild_role_delete(self, role):
		try:
			data = DB().sel_guild(guild = role.guild)['server_stats']
			if 'roles' in data.keys():
				channel_id = int(data['roles'])
				channel = self.client.get_channel( channel_id )
				counter = len(' '.join(str(role.id) for role in role.guild.roles).split(' '))

				if counter >= 100:
					stats_channel_name = channel.name[6:]
				elif counter >= 10:
					stats_channel_name = channel.name[5:]
				elif counter < 10:
					stats_channel_name = channel.name[4:]

				await channel.edit( name = f'[{counter}] {stats_channel_name}' )
		except:
			pass


	@commands.Cog.listener()
	async def on_message(self, message):

		if message.author.bot:
			return
		elif not message.guild:
			return
		else:
			role = get( message.guild.roles, name = self.MUTE_ROLE )
			if role in message.author.roles:
				await message.delete()
			
			guild_data = DB().sel_guild(guild = message.guild)
			data = DB().sel_user(target = message.author)

			if message.channel.id in guild_data['react_channels']:
				await message.add_reaction('👍')
				await message.add_reaction('👎')

			all_message = guild_data['all_message']
			guild_moder_settings = guild_data['auto_mod']
			multi = guild_data['exp_multi']
			ignored_channels = guild_data['ignored_channels']
			all_message += 1

			scr = ("""UPDATE guilds SET all_message = %s WHERE guild_id = %s AND guild_id = %s""")
			val_1 = (all_message, message.guild.id, message.guild.id)

			self.cursor.execute(scr, val_1)
			self.conn.commit()

			if ignored_channels != []:
				if message.channel.id in ignored_channels:
					return

			rand_number_1 = randint( 1, 5 )
			exp_first = rand_number_1
			coins_first = exp_first // 2 + 1

			exp_member = data['exp']
			coins_member = data['coins']
			exp = exp_first + exp_member
			coins = coins_first + coins_member
			reputation = data['reputation']
			messages = data['messages']
			lvl_member = data['lvl']
			last_msg = messages[2][0]

			reput_msg = 150
			messages[0] += 1
			messages[1] += 1
			messages[2][0] = message.content

			messages[2][1] = str(datetime.datetime.now())[:-7]
			exp_end = math.floor(9 * (lvl_member ** 2) + 50 * lvl_member + 125 * multi)
			if exp_end < exp:
				lvl_member += 1
				emb_lvl = discord.Embed(title = 'Сообщения о повышении уровня', description = f'Участник {message.author.mention} повысил свой уровень! Текущий уровень - `{lvl_member}`', timestamp = datetime.datetime.utcnow(), colour = discord.Color.green())

				emb_lvl.set_author(name = message.author.name, icon_url = message.author.avatar_url)
				emb_lvl.set_footer(text = self.FOOTER, icon_url = self.client.user.avatar_url)

				await message.channel.send(embed = emb_lvl)

			if messages[0] >= reput_msg:
				reputation = reputation + 1
				messages[0] = 0

			if reputation >= 100:
				reputation = 100

			sql = ("""UPDATE users SET exp = %s, coins = %s, reputation = %s, messages = %s, level = %s WHERE user_id = %s AND guild_id = %s""")
			val = (exp, coins, reputation, json.dumps(messages), lvl_member, message.author.id, message.guild.id)

			self.cursor.execute(sql, val)
			self.conn.commit()

			def check(m):
				return m.content == last_msg and m.channel == message.channel

			try:
				await self.client.wait_for( 'message', check = check, timeout = 2.0 )
			except asyncio.TimeoutError:
				pass
			else:
				if guild_moder_settings['anti_flud']:
					emb = await Commands(self.client).main_mute(ctx = message, member = message.author, mute_time = 4, mute_typetime = 'h', reason = 'Авто-модерация: Флуд')
					if emb:
						await message.channel.send(embed = emb)


	@commands.Cog.listener()
	async def on_voice_state_update( self, member, before, after ):

		if after.channel:
			pass
		elif before.channel:
			pass

		data = DB().sel_guild(guild = member.guild)['voice_channel']
		if data != {}:
			main_channel = data['channel_id']
			main_channel_obj = self.client.get_channel(int(main_channel))
			category = main_channel_obj.category

		try:
			if after.channel.id == main_channel:
				if not before.channel and after.channel:

					overwrites = {
						member.guild.default_role: discord.PermissionOverwrite( connect = False, manage_permissions = False ),
						member: discord.PermissionOverwrite( connect = True, manage_permissions = True, manage_channels = True ),
						self.client.user: discord.PermissionOverwrite( connect = True, manage_permissions = True, manage_channels = True )
					}

					member_channel = await member.guild.create_voice_channel( name = f'{member.name} Channel', overwrites = overwrites, category = category, guild = member.guild )
					await member.move_to( member_channel )

					def check(a, b, c):
						return len(member_channel.members) == 0

					await self.client.wait_for('voice_state_update', check=check)
					await member_channel.delete()
			else:
				return
		except:
			pass


def setup( client ):
	client.add_cog(Events(client))