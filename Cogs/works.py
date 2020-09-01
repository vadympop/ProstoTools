import discord
import datetime
import os
import json
import random
import requests
import asyncio
import typing
import mysql.connector
from Tools.database import DB
from discord.ext import commands, tasks
from discord.utils import get
from discord.voice_client import VoiceClient
from discord.ext.commands import Bot
from random import randint
from configs import configs


def clear_commands( guild ):

	data = DB().sel_guild(guild = guild)
	purge = data['purge']
	return purge


global Footer
Footer = configs['FOOTER_TEXT']


class Works(commands.Cog, name = 'Works'):

	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(user = 'root', password = os.environ['DB_PASSWORD'], host = 'localhost', database = 'data')
		self.cursor = self.conn.cursor(buffered = True)


	@commands.group()
	@commands.cooldown(2, 7200, commands.BucketType.member)
	async def work( self, ctx ):
		client = self.client
		DB().add_amout_command()
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if ctx.invoked_subcommand is None:
			self.work.reset_cooldown(ctx)
			emb = discord.Embed( title = 'Список работ', description = '**Грузчик - *work loader**\nДля работы нужно иметь более 3-го уровня и перчатки, кулдавн 3 часа после двух попыток, зарабатывает от 80$ до 100$\n\n**Охотник за кладом - *work treasure-hunter**\nДля работы нужен металоискатель(любого уровня), кулдавн 5 часов, может ничего не найти(0$, металоискатель 2-го уровня повышает шанс найти клад на 30%), если найдёт от 1$ до 500$\n\n**Барман - *work barman**\nДля работы нужно иметь более 4-го уровня, кулдавн 3 часа, зарабатывает от 150 до 200\n\n**Уборщик - *work cleaner**\nДля повышения эфективности работы нужно иметь веник или швабру, кулдавн 2 часа после 3 попыток\n\n**Мойщик окон - *work window-washer**\nДля работы нужно иметь более 5-го уровня, кулдавн 5 часов, от 250$ до 300$, может упасть и потерять 300$', colour = discord.Color.green() )

			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send( embed = emb )


	@work.command()
	@commands.cooldown(2, 10800, commands.BucketType.member)
	async def loader( self, ctx ):
		client = self.client

		data = DB().sel_user(target = ctx.author)
		lvl_member = data['lvl']
		rand_num = randint( 80, 100 )
		cur_state_pr = data['prison']
		cur_items = data['items']

		if cur_state_pr == False:
			if lvl_member >= 3:
				if "gloves" in cur_items:
					sql = ("""UPDATE users SET money = money + %s WHERE user_id = %s AND guild_id = %s""")
					val = (rand_num, ctx.author.id, ctx.guild.id)

					self.cursor.execute(sql, val)
					self.conn.commit()

					emb = discord.Embed( description = f'**За работу вы получили: {rand_num}$. Продолжайте стараться!**', colour = discord.Color.green() )

					emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
					emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

					await ctx.send( embed = emb )
				else:
					emb = discord.Embed( description = '**У вас нет необходимых предметов!**', colour = discord.Color.green() )

					emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
					emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

					await ctx.send( embed = emb )
					return
			else:
				emb = discord.Embed( description = '**У вас не достаточний уровень для этой работы!**', colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )
				return

		elif cur_state_pr:
			emb = discord.Embed( description = '**Вы сейчас в тюрме. На эту работу нельзя выходить во время заключения!**', colour = discord.Color.green() )

			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send( embed = emb )
			return


	@work.command(aliases = ['treasure-hunter'])
	@commands.cooldown(1, 18000, commands.BucketType.member)
	async def treasurehunter( self, ctx ):
		client = self.client

		data = DB().sel_user(target = ctx.author)
		lvl_member = data['lvl']
		cur_state_pr = data['prison']
		cur_items = data['items']

		def func_trHunt( shans: int ):
			rand_num_1 = randint( 0, 100 )
			shans_2 = 100 - shans

			if rand_num_1 >= shans:
				rand_num_2 = randint( 1, 500 )

				sql = ("""UPDATE users SET money = money + %s WHERE user_id = %s AND guild_id = %s""")
				val = (rand_num_2, ctx.author.id, ctx.guild.id)

				self.cursor.execute(sql, val)
				self.conn.commit()

				msg_content = f'**За работу вы получили: {rand_num_2}$. Продолжайте стараться!**'
				return msg_content

			elif rand_num_1 <= shans_2:
				msg_content = '**Сегодня вы ничего не нашли**'
				return msg_content

		if cur_state_pr == False:
			if lvl_member >= 2:				
				if cur_items != None:
					
					if "metal_1" in cur_items and "metal_2" in cur_items:
						msg_content = func_trHunt( 20 )
						emb = discord.Embed( description = msg_content, colour = discord.Color.green() )

						emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
						emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

						await ctx.send( embed = emb )
					elif "metal_1" in cur_items:
						msg_content = func_trHunt( 50 )

						emb = discord.Embed( description = msg_content, colour = discord.Color.green() )

						emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
						emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

						await ctx.send( embed = emb )
					elif "metal_2" in cur_items:
						msg_content = func_trHunt( 20 )

						emb = discord.Embed( description = msg_content, colour = discord.Color.green() )

						emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
						emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

						await ctx.send( embed = emb )
					else:
						emb = discord.Embed( description = '**У вас нет не обходимых предметов, метало искателей! Купите метало искатель!**', colour = discord.Color.green() )

						emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
						emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

						await ctx.send( embed = emb )
						return
				elif cur_items == []:
					emb = discord.Embed( description = '**У вас нет не обходимых предметов, метало искателей! Купите метало искатель!**', colour = discord.Color.green() )

					emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
					emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

					await ctx.send( embed = emb )
					return
			else:
				emb = discord.Embed( description = '**У вас не достаточний уровень для этой работы!**', colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )
				return
		elif cur_state_pr:
			emb = discord.Embed( description = '**Вы сейчас в тюрме. На эту работу нельзя выходить во время заключения!**', colour = discord.Color.green() )

			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send( embed = emb )
			return


	@work.command()
	@commands.cooldown(2, 10800, commands.BucketType.member)
	async def barman( self, ctx ):
		client = self.client

		data = DB().sel_user(target = ctx.author)
		lvl_member = data['lvl']
		rand_num = 150 + randint( 0, 50 )
		cur_state_pr = data['prison']

		if cur_state_pr == False:
			if lvl_member >= 4:

				sql = ("""UPDATE users SET money = money + %s WHERE user_id = %s AND guild_id = %s""")
				val = (rand_num, ctx.author.id, ctx.guild.id)

				self.cursor.execute(sql, val)
				self.conn.commit()

				emb = discord.Embed( description = f'**За сегодняшнюю работу в баре: {rand_num}$. Не употребляйте много алкоголя :3**', colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )
			else:
				emb = discord.Embed( description = '**У вас не достаточний уровень для этой работы!**', colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )
				return
		elif cur_state_pr == True:
			emb = discord.Embed( description = '**Вы сейчас в тюрме. На эту работу нельзя выходить во время заключения!**', colour = discord.Color.green() )

			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send( embed = emb )
			return


	@work.command()
	@commands.cooldown(3, 7200, commands.BucketType.member)
	async def cleaner( self, ctx ):
		client = self.client

		data = DB().sel_user(target = ctx.author)
		cur_items = data['items']
		cur_state_pr = data['prison']

		def cleaner_func( rnum1: int, rnum2: int ):
			rnum = randint( rnum1, rnum2 )

			sql = ("""UPDATE users SET money = money + %s WHERE user_id = %s AND guild_id = %s""")
			val = (rnum, ctx.author.id, ctx.guild.id)

			self.cursor.execute(sql, val)
			self.conn.commit()

			msg_content = f'**За сегодняшнюю уборку вы получили: {rnum}$**'
			return msg_content

		if cur_items != None:
			if "broom" in cur_items:
				msg = cleaner_func( 50, 60 )
				emb = discord.Embed( description = msg, colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )
			elif "mop" in cur_items:
				msg = cleaner_func( 60, 80 )
				emb = discord.Embed( description = msg, colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )

			elif "mop" in cur_items and "broom" in cur_items:
				msg = cleaner_func( 60, 80 )
				emb = discord.Embed( description = msg, colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )
			else:
				msg = cleaner_func( 40, 50 )
				emb = discord.Embed( description = msg, colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )
		elif cur_items == []:
			msg = cleaner_func( 40, 50 )
			emb = discord.Embed( description = msg, colour = discord.Color.green() )

			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send( embed = emb )


		if cur_state_pr == True and data['money'] > 0:
			emb = discord.Embed( description = '**Вы успешно погасили борг и выйшли с тюрмы!**', colour = discord.Color.green() )

			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send( embed = emb )

			sql = ("""UPDATE users SET prison = %s WHERE user_id = %s AND guild_id = %s""")
			val = ("False", ctx.author.id, ctx.guild.id)

			self.cursor.execute(sql, val)
			self.conn.commit()


	@work.command(aliases = ['window-washer'])
	@commands.cooldown(1, 18000, commands.BucketType.member)
	async def windowasher( self, ctx ):
		client = self.client

		data = DB().sel_user(target = ctx.author)
		lvl_member = data['lvl']
		rand_num_1 = randint( 1, 2 )
		cur_state_pr = data['prison']

		if cur_state_pr == False:
			if lvl_member >= 5:
				if rand_num_1 == 1:
					rand_num_2 = randint( 250, 300 )
					cur_money = data['money'] + rand_num_2
					emb = discord.Embed( description = f'**За мойку окон на высоком здании в получили {rand_num_2}$**', colour = discord.Color.green() )

					emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
					emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

					await ctx.send( embed = emb )

				elif rand_num_1 == 2:
					cur_money = data['money'] - 300
					emb = discord.Embed( description = f'**Вы упали и потеряли 300$**', colour = discord.Color.green() )

					emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
					emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

					await ctx.send( embed = emb )

				sql = ("""UPDATE users SET money = %s WHERE user_id = %s AND guild_id = %s""")
				val = (cur_money, ctx.author.id, ctx.guild.id)

				self.cursor.execute(sql, val)
				self.conn.commit()

			else:
				emb = discord.Embed( description = '**У вас не достаточний уровень для этой работы!**', colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )
				return
		elif cur_state_pr == True:
			emb = discord.Embed( description = '**Вы сейчас в тюрме. На эту работу нельзя выходить во время заключения!**', colour = discord.Color.green() )

			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send( embed = emb )

			return


def setup( client ):
	client.add_cog(Works(client))