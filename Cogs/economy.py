import discord
import datetime
import os
import json
import random
import requests
import asyncio
import typing
import io
import mysql.connector
from Tools.database import DB
from Cybernator import Paginator
from discord.ext import commands, tasks
from discord.utils import get
from discord.voice_client import VoiceClient
from discord.ext.commands import Bot
from PIL import Image, ImageFont, ImageDraw, ImageFilter, ImageEnhance
from random import randint
from configs import configs

class Economy(commands.Cog, name = 'Economy'):

	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(user = 'root', password = os.environ['DB_PASSWORD'], host = 'localhost', database = 'data')
		self.cursor = self.conn.cursor(buffered = True)
		self.FOOTER = configs['FOOTER_TEXT']
		self.BACKGROUND = configs['DEF_PROFILE_BG']
		self.FONT = configs['FONT']
		self.SAVE = configs['SAVE_IMG']


	@commands.command(description = '**Показывает лидеров по разных валютах**', usage = 'top')
	async def top(self, ctx):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		sql = ("""SELECT user_id, exp, level, money, reputation FROM users WHERE guild_id = %s AND guild_id = %s ORDER BY exp DESC LIMIT 15""")
		val = (ctx.guild.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		data = self.cursor.fetchall()

		emb = discord.Embed( title = 'Лидеры сервера', colour = discord.Color.green() )
		emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )

		num = 1
		for user in data:
			member = get(ctx.guild.members, id=user[0])
			if member:
				if not member.bot:
					if num == 1:
						emb.add_field(name=f'**[{num}]** <:gold_star:732490991302606868> Участник - {member.name}, Опыта - {user[1]}', value=f'Уровень: **{user[2]}**\nРепутации: **{user[4]}**\nДенег: **{user[3]}**', inline=False)
					elif num == 2:
						emb.add_field(name=f'**[{num}]** <:silver_star:732490991378104390> Участник - {member.name}, Опыта - {user[1]}', value=f'Уровень: **{user[2]}**\nРепутации: **{user[4]}**\nДенег: **{user[3]}**', inline=False)
					elif num == 3:
						emb.add_field(name=f'**[{num}]** <:bronce_star:732490990924988418> Участник - {member.name}, Опыта - {user[1]}', value=f'Уровень: **{user[2]}**\nРепутации: **{user[4]}**\nДенег: **{user[3]}**', inline=False)
					else:
						emb.add_field(name=f'[{num}] Участник - {member.name}, Опыта - {user[1]}', value=f'Уровень: **{user[2]}**\nРепутации: **{user[4]}**\nДенег: **{user[3]}**', inline = False)
					num += 1

		await ctx.send(embed=emb)


	@commands.command(name = '+rep', aliases = ['+reputation', 'repp'], description = '**Добавления репутации(от 1 до 5) указаному пользователю(Cooldown 1 час)**', usage = '+rep [@Участник] [Число репутации]')
	@commands.cooldown(1, 3600, commands.BucketType.member)
	async def repp( self, ctx, member: discord.Member, num: int ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed( title = 'Ошибка!', description = '**Вы не можете изменять свою репутацию!**', colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.repp.reset_cooldown(ctx)
			return
		elif num < 1 or num > 5:
			emb = discord.Embed( title = 'Ошибка!', description = '**Вы указали число добавляемой репутацию в неправильном диапазоне!**', colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.repp.reset_cooldown(ctx)
			return	
		elif member.bot:
			emb = discord.Embed( title = 'Ошибка!', description = '**Вы не можете менять репутацию бота**', colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.repp.reset_cooldown(ctx)
			return	

		DB().sel_user(target = member)

		sql = ("""UPDATE users SET reputation = reputation + %s WHERE user_id = %s AND guild_id = %s""")
		val = (num, member.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		emb = discord.Embed( description = '**Вы успешно добавили репутация к указаному пользователю!**', colour = discord.Color.green() )
		emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
		await ctx.send( embed = emb )


	@commands.command(name = '-rep', aliases = ['-reputation', 'repm'], description = '**Отнимает репутацию(от 1 до 3) указаному пользователю(Cooldown 1 час)**', usage = '-rep [@Участник] [Число репутации]')
	@commands.cooldown(1, 3600, commands.BucketType.member)
	async def repm( self, ctx, member: discord.Member, num: int ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed( title = 'Ошибка!', description = '**Вы не можете изменять свою репутацию!**', colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.repm.reset_cooldown(ctx)
			return
		elif num < 1 or num > 3:
			emb = discord.Embed( title = 'Ошибка!', description = '**Вы указали число убаляемой репутацию в неправильном диапазоне!**', colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.repm.reset_cooldown(ctx)
			return
		elif member.bot:
			emb = discord.Embed( title = 'Ошибка!', description = '**Вы не можете менять репутацию бота**', colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.repm.reset_cooldown(ctx)
			return	

		DB().sel_user(target = member)

		sql = ("""UPDATE users SET reputation = reputation - %s WHERE user_id = %s AND guild_id = %s""")
		val = (num, member.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		emb = discord.Embed( description = '**Вы успешно убавили репутация к указаному пользователю!**', colour = discord.Color.green() )
		emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
		await ctx.send( embed = emb )


	@commands.command(description = '**Ежедневная награда**', usage = 'daily')
	@commands.cooldown(1, 86400, commands.BucketType.member)
	async def daily( self, ctx ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		nums = [100, 250, 1000, 500, 50]
		rand_num = random.choice(nums)

		DB().sel_user(target = ctx.author)
		sql = ("""UPDATE users SET money = money + %s WHERE user_id = %s AND guild_id = %s""")
		val = (rand_num, ctx.author.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		emb = discord.Embed( description = f'**Вы получили ежедневну награду! В размере - {rand_num}$**', colour = discord.Color.green() )
		emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
		await ctx.send( embed = emb )


	@commands.command(aliases=['textchannel'], name = 'text-channel', description = '**Создает приватный текстовый канал. По умолчанию у вас есть 20 каналов(Их можно купить в магазине), создавать их можно только в определлёной категории. Он автоматически удаляеться через 30мин!(Cooldown - 3 мин)**', usage = 'text-channel [Имя канала]')
	@commands.cooldown(1, 240, commands.BucketType.member)
	async def textchannel( self, ctx, *, name ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		data = DB().sel_user(target = ctx.author)
		sql = ("""UPDATE users SET text_channel = text_channel - 1 WHERE user_id = %s AND guild_id = %s""")
		val = (ctx.author.id, ctx.guild.id)

		guild_data = DB().sel_guild(guild = ctx.guild)
		category_id = guild_data['textchannels_category']
		time = guild_data['timedelete_textchannel']
		num_textchannels = data['text_channels']

		if category_id == 0:
			emb = discord.Embed( title = 'Ошибка!', description = '**Не указана категория создания приватных текстовых каналов. Обратитесь к администации сервера**', colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.textchannel.reset_cooldown(ctx)
			return
		elif category_id:
			if num_textchannels >= 0:
				overwrites = {
					ctx.guild.default_role: discord.PermissionOverwrite( read_messages = False, send_messages = False ),
					ctx.author: discord.PermissionOverwrite( read_messages = True, send_messages = True, manage_permissions = True, manage_channels = True  ),
				}
				category = discord.utils.get( ctx.guild.categories, id = category_id )
				text_channel = await ctx.guild.create_text_channel( name, category = category, overwrites = overwrites )

				emb = discord.Embed( title = f'{ctx.author.name} Создал текстовый канал #{text_channel}', colour = discord.Color.green() )
				emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
				emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
				await ctx.send( embed = emb )
			elif num_textchannels <= 0:
				emb = discord.Embed( title = f'**У вас не достаточно каналов!**', colour = discord.Color.green() )
				emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
				emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
				await ctx.send( embed = emb )
				await ctx.message.add_reaction('❌')
				self.textchannel.reset_cooldown(ctx)
				return

			self.cursor.execute(sql, val)
			self.conn.commit()
			
			await asyncio.sleep( 60 * time )
			await text_channel.delete()


	@commands.command(aliases=['shoplist'], name = 'shop-list', description = '**Показывает список покупаемых предметов**', usage = 'shop-list')
	async def shoplist( self, ctx ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		data = DB().sel_guild(guild = ctx.guild)
		shoplist = data['shop_list']
		content = ''

		if shoplist != []:
			for shop_role in shoplist:
				role = get( ctx.guild.roles, id = shop_role[0] )
				content += f'{role.mention} - {shop_role[1]}\n'

			emb = discord.Embed( title = 'Список товаров', description = f'**Роли:**\n{content}\n**Товары:**\nМеталоискатель 1-го уровня - 500$\nМеталоискатель 2-го уровня 1000$\nСим-карта - 100$\nТелефон - 1100$\nМетла - 500 коинов\nШвабра - 2000 коинов\nТекстовый канал - 100$\nПерчатки - 600$\n\n**Лут боксы:**\nЛут бокс Common - 800$\nЛут бокс Rare - 1800$\nЛут бокс Epic - 4600$\nЛут бокс Legendary - 9800$\nЛут бокс Imposible - 19600$', colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
		elif shoplist == []:
			emb = discord.Embed( title = 'Список товаров', description = f'**Товары:**\nМеталоискатель 1-го уровня - 500$\nМеталоискатель 2-го уровня 1000$\nСим-карта - 100$\nТелефон - 1100$\nМетла - 500 коинов\nШвабра - 2000 коинов\nТекстовый канал - 100$\nПерчатки - 600$\n\n**Лут боксы:**\nЛут бокс Common - 800$\nЛут бокс Rare - 1800$\nЛут бокс Epic - 4600$\nЛут бокс Legendary - 9800$\nЛут бокс Imposible - 19600$', colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )


	@commands.command(description = '**Купляет указанный товар**', usage = 'buy [Имя товара]')
	async def buy( self, ctx, item: typing.Optional[str], num: typing.Optional[int] = None ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		member = ctx.author

		data = DB().sel_user(target = ctx.author)
		cur_state_prison = data['prison']
		member_items = data['items']

		if cur_state_prison == False:
			try:
				role = get( ctx.guild.roles, name = item )
			except:
				pass

			if not item:
				emb = discord.Embed( title = 'Как купить товары?', description = f'Метало искатель 1-го уровня - metal_1 или металоискатель_1\nМетало искатель 2-го уровня - metal_2 или металоискатель_2\nТелефон - tel или телефон\nСим-карта - sim или сим-карта\nТекстовый канал - текстовый-канал или text-channel\nМетла - метла или broom\nШвабра - швабра или mop\nПерчатки - перчатки или gloves\nДля покупки роли нужно вести её названия\n\n**Все цены можно узнать с помощю команды {self.client.get_prefix(self.client, ctx)}shoplist**', colour = discord.Color.green() )
				emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
				emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
				await ctx.send( embed = emb )
				return

			costs = [500, 1000, 100, 1100, 100, 600, 800, 1800, 4600, 9800, 19600]
			info = DB().sel_guild(guild = ctx.guild)
			roles = info['shop_list']

			def buy_func( func_item, func_cost ):
				cur_money = data['money'] - func_cost
				cur_items = data['items']
				cur_transantions = data['transantions']
				prison = 'False'

				if isinstance( cur_items, list ) == True:
					cur_items.append(func_item)
				elif cur_items == []:
					cur_items.append(func_item)

				if cur_money <= -5000:
					prison = 'True'
					cur_items = []
					return True

				id_trans = ''
				stop = 0
				while stop <= 12:
					id_trans += str(randint(1, 9))
					stop += 1

				info_transantion = {
					'to': 'Магазин',
					'from': ctx.author.id,
					'cash': func_cost,
					'time': str(datetime.datetime.today()),
					'id': id_trans,
					'guild_id': ctx.guild.id
				}
				cur_transantions.append(info_transantion)

				sql = ("""UPDATE users SET items = %s, prison = %s, money = %s, transantions = %s WHERE user_id = %s AND guild_id = %s""")
				val = (json.dumps(cur_items), prison, cur_money, json.dumps(cur_transantions), ctx.author.id, ctx.guild.id)

				self.cursor.execute(sql, val)
				self.conn.commit()

			def buy_coins_func( func_item, func_cost ):
				coins_member = data['coins'] - func_cost
				cur_items = data['items']

				if isinstance( cur_items, list ) == True:
					cur_items.append(func_item)
				elif cur_items == []:
					cur_items.append(func_item)

				sql = ("""UPDATE users SET items = %s, coins = %s WHERE user_id = %s AND guild_id = %s""")
				val = (json.dumps(cur_items), coins_member, ctx.author.id, ctx.guild.id)

				self.cursor.execute(sql, val)
				self.conn.commit()

			def buy_text_channel( func_cost, num ):
				cost = func_cost * num
				cur_transantions = data['transantions']
				cur_money = data['money'] - cost
				num_textchannels = data['text_channels'] + num
				cur_items = data['items']
				prison = 'False'

				if cur_money <= -5000:
					prison = 'True'
					cur_items = []
					return True

				id_trans = ''
				stop = 0
				while stop <= 12:
					id_trans += str(randint(1, 9))
					stop += 1

				info_transantion = {
					'to': 'Магазин',
					'from': ctx.author.id,
					'cash': cost,
					'time': str(datetime.datetime.today()),
					'id': id_trans,
					'guild_id': ctx.guild.id
				}
				cur_transantions.append(info_transantion)

				sql = ("""UPDATE users SET items = %s, prison = %s, money = %s, text_channel = %s, transantions = %s WHERE user_id = %s AND guild_id = %s""")
				val = (json.dumps(cur_items), prison, cur_money, num_textchannels, json.dumps(cur_transantions), ctx.author.id, ctx.guild.id)

				self.cursor.execute(sql, val)
				self.conn.commit()

			def buy_item( item, cost, stacked = False ):
				emb_cool = None
				emb_prison = None
				emb_fail = None

				if item not in member_items:
					if stacked:
						cur_items = data['items']
						prison = data['prison']
						stack = False

						for i in cur_items:
							if isinstance(i, list) == True:
								if i[0] == item[0]:
									stack = True

						if not stack:
							state = buy_func( item, cost )

							if state:
								emb_prison = discord.Embed( description = f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**' , colour = discord.Color.green() )
								emb_prison.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
								emb_prison.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
		
							emb_cool = discord.Embed( description = f'**Вы успешно приобрели - {item[0]}**', colour = discord.Color.green() )
							emb_cool.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
							emb_cool.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
						elif stack:
							cur_money = data['money'] - cost

							for i in cur_items:
								if isinstance(i, list) == True:
									if i[0] == item[0]:
										i[1] += 1

							if cur_money <= -5000:
								prison = True
								cur_items = []
								emb_prison = discord.Embed( description = f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**' , colour = discord.Color.green() )
								emb_prison.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
								emb_prison.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )			
								
							emb_cool = discord.Embed( description = f'**Вы успешно приобрели - {item[0]}**', colour = discord.Color.green() )
							emb_cool.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
							emb_cool.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )

							sql = ("""UPDATE users SET items = %s, prison = %s, money = %s WHERE user_id = %s AND guild_id = %s""")
							val = (json.dumps(cur_items), str(prison), cur_money, ctx.author.id, ctx.guild.id)

							self.cursor.execute(sql, val)
							self.conn.commit()

					elif not stacked:
						state = buy_func( item, cost )
						if state:
							emb_prison = discord.Embed( description = f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**' , colour = discord.Color.green() )
							emb_prison.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
							emb_prison.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
				
						emb_cool = discord.Embed( description = f'**Вы успешно приобрели - {item}**', colour = discord.Color.green() )
						emb_cool.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
						emb_cool.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
				else:
					if not stacked:
						emb_fail = discord.Embed( description = '**Вы уже имеете этот товар!**', colour = discord.Color.green() )
						emb_fail.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
						emb_fail.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
					elif stacked:
						cur_items = data['items']
						prison = data['prison']
						stack = False

						for i in cur_items:
							if isinstance(i, list) == True:
								if i[0] == item[0]:
									stack = True

						if not stack:
							state = buy_func( item, cost )
							if state:
								emb_prison = discord.Embed( description = f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**' , colour = discord.Color.green() )
								emb_prison.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
								emb_prison.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )

							emb_cool = discord.Embed( description = f'**Вы успешно приобрели - {item[0]}**', colour = discord.Color.green() )
							emb_cool.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
							emb_cool.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
						elif stack:
							cur_money = data['money'] - cost

							for i in cur_items:
								if isinstance(i, list) == True:
									if i[0] == item[0]:
										i[1] += 1

							if cur_money <= -5000:
								cur_items = []
								prison = True
								emb_prison = discord.Embed( description = f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**' , colour = discord.Color.green() )
								emb_prison.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
								emb_prison.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
								
							emb_cool = discord.Embed( description = f'**Вы успешно приобрели - {item[0]}**', colour = discord.Color.green() )
							emb_cool.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
							emb_cool.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )

							sql = ("""UPDATE users SET items = %s, prison = %s, money = %s WHERE user_id = %s AND guild_id = %s""")
							val = (json.dumps(cur_items), str(prison), cur_money, ctx.author.id, ctx.guild.id)

							self.cursor.execute(sql, val)
							self.conn.commit()

				embeds = [emb_cool, emb_prison, emb_fail]
				return embeds

			if item == 'металоискатель1' or item == 'metal_1' or item == 'металоискатель_1':
				embeds = buy_item('metal_1', costs[0])
				if embeds[0]:
					await ctx.send( embed = embeds[0] )
				elif embeds[1]:
					await member.send( embed = embeds[1] )
				elif embeds[2]:
					await ctx.message.add_reaction('❌')
					await ctx.send( embed = embeds[2] )

			elif item == 'металоискатель2' or item == 'metal_2' or item == 'металоискатель_2':
				embeds = buy_item('metal_2', costs[1])
				if embeds[0]:
					await ctx.send( embed = embeds[0] )
				elif embeds[1]:
					await member.send( embed = embeds[1] )
				elif embeds[2]:
					await ctx.message.add_reaction('❌')
					await ctx.send( embed = embeds[2] )

			elif item == 'телефон' or item == 'тел' or item == 'telephone' or item == 'tel':
				embeds = buy_item('tel', costs[3])
				if embeds[0]:
					await ctx.send( embed = embeds[0] )
				elif embeds[1]:
					await member.send( embed = embeds[1] )
				elif embeds[2]:
					await ctx.message.add_reaction('❌')
					await ctx.send( embed = embeds[2] )

			elif item == 'sim' or item == 'sim_card' or item == 'sim-card' or item == 'симка' or item == 'сим_карта':
				embeds = buy_item('sim', costs[2])
				if embeds[0]:
					await ctx.send( embed = embeds[0] )
				elif embeds[1]:
					await member.send( embed = embeds[1] )
				elif embeds[2]:
					await ctx.message.add_reaction('❌')				
					await ctx.send( embed = embeds[2] )

			elif role != None:
				role_state = False

				for i in roles:
					if i[0] == role.id:
						role_state = True

				if role_state:
					if role.id not in member_items and role not in member.roles:

						for i in roles:
							if i[0] == role.id:
								role_cost = i[1]

						state = buy_func( role.id, role_cost )
						await member.add_roles(role)

						if state:
							emb = discord.Embed( description = f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**' , colour = discord.Color.green() )
							emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
							emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
							await member.send( embed = emb )
							return

						emb = discord.Embed( description = f'**Вы успешно приобрели новую роль - <@&{role.id}>**', colour = discord.Color.green() )
						emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
						emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
						await ctx.send( embed = emb )
					else:
						emb = discord.Embed( title = 'Ошибка!', description = '**Вы уже имеете эту роль!**', colour = discord.Color.green() )
						emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
						emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
						await ctx.send( embed = emb )
						await ctx.message.add_reaction('❌')
						return
				else:
					emb = discord.Embed( title = 'Ошибка!', description = f'**Укажите роль правильно, такой роли нету в списке продаваемых ролей!**', colour = discord.Color.green() )
					emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
					emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
					await ctx.send( embed = emb )
					await ctx.message.add_reaction('❌')
					return

			elif item == 'метла' or item == 'broom' or item == 'metla':
				if data['coins'] >= 500:
					if member_items != None and isinstance(member_items, int) == False:
						if 'broom' not in member_items:
							buy_coins_func( "broom", 500 )
							emb = discord.Embed( description = f'**Вы успешно приобрели - {item}**', colour = discord.Color.green() )
							emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
							emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
							await ctx.send( embed = emb )
						else:
							emb = discord.Embed( description = '**Вы уже имеете этот товар!**', colour = discord.Color.green() )
							emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
							emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
							await ctx.send( embed = emb )
							return
					else:
						buy_coins_func( "broom", 500 )
						emb = discord.Embed( description = f'**Вы успешно приобрели - {item}**', colour = discord.Color.green() )
						emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
						emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
						await ctx.send( embed = emb )
				else:
					emb = discord.Embed( title = 'Ошибка!', description = f'**У вас недостаточно коинов!**', colour = discord.Color.green() )
					emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
					emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
					await ctx.send( embed = emb )
					await ctx.message.add_reaction('❌')
					return
			elif item == 'швабра' or item == 'mop':
				if data['coins'] >= 500:
					if 'mop' not in member_items:
						buy_coins_func( "mop", 2000 )
						emb = discord.Embed( description = f'**Вы успешно приобрели - {item}**', colour = discord.Color.green() )
						emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
						emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
						await ctx.send( embed = emb )
					else:
						emb = discord.Embed( description = '**Вы уже имеете этот товар!**', colour = discord.Color.green() )
						emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
						emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
						await ctx.send( embed = emb )
						return
				else:
					await ctx.message.add_reaction('❌')
					emb = discord.Embed( title = 'Ошибка!', description = f'**У вас недостаточно коинов!**', colour = discord.Color.green() )
					emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
					emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
					await ctx.send( embed = emb )
					return

			elif item == 'перчатки' or item == 'gloves':
				embeds = buy_item('gloves', costs[5])
				if embeds[0]:
					await ctx.send( embed = embeds[0] )
				elif embeds[1]:
					await member.send( embed = embeds[1] )
				elif embeds[2]:
					await ctx.send( embed = embeds[2] )

			elif item == 'бокс-обычный' or item == 'box-c' or item == 'box-C' or item == 'box-common' or item == 'box-Common':
				embeds = buy_item(['box-C', 1], costs[6], True)
				if embeds[0]:
					await ctx.send( embed = embeds[0] )
				elif embeds[1]:
					await member.send( embed = embeds[1] )
				elif embeds[2]:
					await ctx.send( embed = embeds[2] )

			elif item == 'бокс-редкий' or item == 'box-r' or item == 'box-R' or item == 'box-rare' or item == 'box-Rare':
				embeds = buy_item(['box-R', 1], costs[7], True)
				if embeds[0]:
					await ctx.send( embed = embeds[0] )
				elif embeds[1]:
					await member.send( embed = embeds[1] )
				elif embeds[2]:
					await ctx.send( embed = embeds[2] )

			elif item == 'бокс-эпик' or item == 'box-e' or item == 'box-E' or item == 'box-epic' or item == 'box-Epic':
				embeds = buy_item(['box-E', 1], costs[8], True)
				if embeds[0]:
					await ctx.send( embed = embeds[0] )
				elif embeds[1]:
					await member.send( embed = embeds[1] )
				elif embeds[2]:
					await ctx.send( embed = embeds[2] )

			elif item == 'бокс-легенда' or item == 'box-l' or item == 'box-L' or item == 'box-legendary' or item == 'box-Legendary':
				embeds = buy_item(['box-L', 1], costs[9], True)
				if embeds[0]:
					await ctx.send( embed = embeds[0] )
				elif embeds[1]:
					await member.send( embed = embeds[1] )
				elif embeds[2]:
					await ctx.send( embed = embeds[2] )

			elif item == 'бокс-невероятный' or item == 'box-i' or item == 'box-I' or item == 'box-imposible' or item == 'box-Imposible':
				embeds = buy_item(['box-I', 1], costs[10], True)
				if embeds[0]:
					await ctx.send( embed = embeds[0] )
				elif embeds[1]:
					await member.send( embed = embeds[1] )
				elif embeds[2]:
					await ctx.send( embed = embeds[2] )		

			elif item == 'текст_канал' or item == 'текстовый-канал' or item == 'text-channel' or item == 'text_channel':
				if num:	
					state = buy_text_channel( costs[4], num )
					if state == True:
						emb = discord.Embed( description = f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**' , colour = discord.Color.green() )
						emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
						emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
						await member.send( embed = emb )
						return

					emb = discord.Embed( description = f'**Вы успешно приобрели текстовые каналы - {num}шт**', colour = discord.Color.green() )
					emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
					emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
					await ctx.send( embed = emb )
				elif not num:
					await ctx.message.add_reaction('❌')
					emb = discord.Embed( title = 'Ошибка!', description = f'**Вы не указали число покупаемых каналов!**', colour = discord.Color.green() )
					emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
					emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
					await ctx.send( embed = emb )
					return

		elif cur_state_prison:
			await ctx.message.add_reaction('❌')
			emb = discord.Embed( title = 'Ошибка!', description = "**У вас заблокирование транзакции, так как вы в тюрме!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			return


	@commands.command(aliases=['sendmoney'], name = 'send-money', description = '**Этой командой можно оправить свои деньги другому пользователю(Cooldown - 30 мин)**', usage = 'send-money [@Участник]')
	@commands.cooldown(1, 1800, commands.BucketType.member)
	async def sendmoney( self, ctx, member: discord.Member, num: int ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		data1 = DB().sel_user(target = ctx.author)

		if member.bot:
			emb = discord.Embed( title = 'Ошибка!', description = f"**Вы не можете передавать деньги боту!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return

		if member in ctx.guild.members:
			data2 = DB().sel_user(target = member)
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f"**На сервере не существует такого пользователя!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return

		cur_state_pr1 = data1['prison']
		cur_state_pr2 = data2['prison']
		cur_money1 = data1['money']
		cur_transantions1 = data1['transantions']
		cur_transantions2 = data2['transantions']

		if cur_state_pr1 == False and cur_state_pr2 == False and cur_money1 > num:
			id_1 = ''
			id_2 = ''
			stop = 0
			while stop <= 12:
				id_1 += str(randint(1, 9))
				id_2 += str(randint(1, 9))
				stop += 1

			info_transantion_1 = {
				'to': member.id,
				'from': ctx.author.id,
				'cash': num,
				'time': str(datetime.datetime.today()),
				'id': id_1,
				'guild_id': ctx.guild.id
			}
			info_transantion_2 = {
				'to': member.id,
				'from': ctx.author.id,
				'cash': num,
				'time': str(datetime.datetime.today()),
				'id': id_2,
				'guild_id': ctx.guild.id
			}

			cur_transantions1.append(info_transantion_1)
			cur_transantions2.append(info_transantion_2)

			sql_1 = ("""UPDATE users SET money = money - %s, transantions = %s WHERE user_id = %s AND guild_id = %s""")
			sql_2 = ("""UPDATE users SET money = money + %s, transantions = %s WHERE user_id = %s AND guild_id = %s""")
			val_1 = (num, json.dumps(cur_transantions1), ctx.author.id, ctx.guild.id)
			val_2 = (num, json.dumps(cur_transantions2), member.id, member.guild.id)

			self.cursor.execute(sql_1, val_1)
			self.conn.commit()

			self.cursor.execute(sql_2, val_2)
			self.conn.commit()

			emb = discord.Embed( description = f"**Вы успешно совершили транзакцию `{member.mention}` на суму `{num}$`**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )

			emb = discord.Embed( description = f"**Вам {ctx.author.mention} перевел деньги на суму `{num}$`, сервер `{ctx.guild.name}`**", colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await member.send( embed = emb )
		elif cur_state_pr1 == True:
			emb = discord.Embed( title = 'Ошибка!', description = "**У вас заблокирование транзакции, так как вы в тюрме!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.sendmoney.reset_cooldown(ctx)
			return
		elif cur_state_pr2 == True:
			emb = discord.Embed( title = 'Ошибка!', description = "**В указаного пользователя заблокирование транзакции, так как он в тюрме!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.sendmoney.reset_cooldown(ctx)
			return
		elif cur_money1 < num:
			emb = discord.Embed( title = 'Ошибка!', description = "**У вас недостаточно средств для транзакции!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.sendmoney.reset_cooldown(ctx)
			return


	@commands.command(aliases=['trans', 'transactions'], name = 'my-transactions', description = '**Показывает всё ваши транзакции на текущем сервере**', usage = 'my-transactions')
	async def trans(self, ctx):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		data = DB().sel_user(target = ctx.author)
		transantions = data['transantions']

		if transantions == []:
			emb = discord.Embed( title = f'Транзакции пользователя - `{ctx.author}`', description = 'Пользователь не совершал транзакций', colour = discord.Color.green() )
		else:
			emb = discord.Embed( title = f'Транзакции пользователя - `{ctx.author}`', colour = discord.Color.green() )

		for transantion in transantions:
			transantion_id = transantion['id']
			transantion_time = transantion['time']
			transantion_to = get(ctx.guild.members, id = transantion['to'])
			if not transantion_to:
				transantion_to = transantion['to']
			transantion_from = get(ctx.guild.members, id = transantion['from'])
			transantion_cash = transantion['cash']

			emb.add_field( value = f"Время - {transantion_time}, Id - {transantion_id}", name = f'Сумма - {transantion_cash}, кому - `{transantion_to}`, от кого - `{transantion_from}`', inline = False )

		emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )

		await ctx.send(embed = emb)


	@commands.command(description = '**Открывает указаный лут бокс**', usage = 'open [Лут бокс]')
	async def open(self, ctx, box: str = None):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		box = box[:-2].lower() + f'-{box[-1:].upper()}'
		boxes = ['box-C', 'box-R', 'box-E', 'box-L', 'box-I']
		dict_boxes = {
			'box-C': ['Обычный бокс', 4000],
			'box-R': ['Редкий бокс', 6000],
			'box-E': ['Эпический бокс', 9000],
			'box-L': ['Легендарный бокс', 12000],
			'box-I': ['Невероятный бокс', 16000]
		}

		if not box:
			emb = discord.Embed( title = 'Укажите пожалуйста бокс!', description = f"**Обычный бокс - box-C\nРедкий бокс - box-R\nЭпический бокс - box-E\nЛегендарный бокс - box-L\nНевероятный бокс - box-I**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			return
		elif box not in boxes:			
			emb = discord.Embed( title = 'Укажите пожалуйста бокс правильно!', description = f"**Обычный бокс - box-C\nРедкий бокс - box-R\nЭпический бокс - box-E\nЛегендарный бокс - box-L\nНевероятный бокс - box-I**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			return

		data = DB().sel_user(target = ctx.author)
		items = data['items']
		pets = data['pets']
		money = data['money'] 
		coins = data['coins']

		rand_num_1 = randint(1, 100)
		rand_items_1 = ['mop', 'broom', 'sim', 'metal_1']
		rand_items_2 = ['gloves', 'tel', 'metal_2']
		rand_money = 0
		msg_content = ''
		state = False
		pet = None
		all_pets = ['cat', 'dog', 'helmet', "loupe", 'parrot', 'hamster']
		dict_items = {
			'mop': 'Швабра',
			'broom': 'Метла',
			'sim': 'Сим-карта',
			'metal_1': 'Металоискатель 1-го уровня',
			'gloves': 'Перчатки',
			'tel': 'Телефон',
			'metal_2': 'Металоискатель 2-го уровня'
		}

		for item in items:
			if isinstance(item, list):
				if item[0] == box:
					state = True
					if item[1] <= 1:
						items.remove(item)
					elif item[1] > 1:
						item[1] -= 1

		if state:
			if box == boxes[0]:
				if rand_num_1 <= 5:
					pet = [all_pets[2], boxes[0]]
					msg_content = 'С обычного бокса вам выпал питомец - Каска(Увеличивает стоимость клада)'
					# Каска

				elif rand_num_1 > 5 and rand_num_1 <= 25:
					pet = [all_pets[1], boxes[0]]
					msg_content = 'С обычного бокса вам выпал питомец - Собачка(Обычный питомец)'				
					# Собачка

				elif rand_num_1 > 25 and rand_num_1 <= 50:
					pet = [all_pets[0], boxes[0]]
					msg_content = 'С обычного бокса вам выпал питомец - Кошка(Обычный питомец)'
					# Кошка

				elif rand_num_1 > 50:
					rand_num_2 = randint(1, 2)

					if rand_num_2 == 1:
						rand_money = randint(10, 600)
					elif rand_num_2 == 2:
						rand_money = randint(400, 1000)
					msg_content = f'Вам не очень повезло и с обычного бокса выпали деньги в размере - {rand_money}'

			elif box == boxes[1]:
				if rand_num_1 <= 1:
					pet = [all_pets[5], boxes[1]]
					msg_content = 'С редкого бокса вам выпал питомец - Хомяк(Увеличивает выпадения коинов)'
					# Хомяк

				elif rand_num_1 > 1 and rand_num_1 <= 7:
					pet = [all_pets[2], boxes[1]]
					msg_content = 'С редкого бокса вам выпал питомец - Каска(Увеличивает стоимость клада)'
					# Каска

				elif rand_num_1 > 7 and rand_num_1 <= 30:
					pet = [all_pets[1], boxes[1]]
					msg_content = 'С редкого бокса вам выпал питомец - Собачка(Обычный питомец)'
					# Собачка

				elif rand_num_1 > 30 and rand_num_1 <= 60:
					pet = [all_pets[0], boxes[1]]
					msg_content = 'С редкого бокса вам выпал питомец - Кошка(Обычный питомец)'
					# Кошка

				elif rand_num_1 > 60:
					rand_num_2 = randint(1, 2)

					if rand_num_2 == 1:
						rand_money = randint(100, 1000)
					elif rand_num_2 == 2:
						rand_money = randint(600, 2000)
					msg_content = f'Вам не очень повезло и с редкого бокса выпали деньги в размере - {rand_money}'

			elif box == boxes[2]:
				if rand_num_1 <= 4:
					pet = [all_pets[5], boxes[2]]
					msg_content = 'С эпического бокса вам выпал питомец - Хомяк(Увеличивает выпадения коинов)'
					# Хомяк

				elif rand_num_1 > 4 and rand_num_1 <= 10:
					pet = [all_pets[2], boxes[2]]
					msg_content = 'С эпического бокса вам выпал питомец - Каска(Увеличивает стоимость клада)'
					# Каска

				elif rand_num_1 > 10 and rand_num_1 <= 33:
					pet = [all_pets[1], boxes[2]]
					msg_content = 'С эпического бокса вам выпал питомец - Собачка(Обычный питомец)'
					# Собачка

				elif rand_num_1 > 33 and rand_num_1 <= 63:
					pet = [all_pets[0], boxes[2]]
					msg_content = 'С эпического бокса вам выпал питомец - Кошка(Обычный питомец)'
					# Кошка

				elif rand_num_1 > 63:
					rand_num_2 = randint(1, 4)

					if rand_num_2 == 1:
						rand_money = randint(1000, 3000)
						msg_content = f'Вам не очень повезло и с эпического бокса выпали деньги в размере - {rand_money}'
					
					elif rand_num_2 == 2:
						rand_money = randint(1800, 4900)
						msg_content = f'Вам не очень повезло и с эпического бокса выпали деньги в размере - {rand_money}'
					
					elif rand_num_2 == 3:
						choice = random.choice(rand_items_1)
						if choice in items:
							rand_money_2 = randint(1000, 2000)
							msg_content = f'Вам не очень повезло и с эпического бокса выпали деньги в размере - {rand_money_2}'
						else:
							items.append(choice)
							msg_content = f'С эпического бокса выпал предмет - {dict_items[choice]}'

					elif rand_num_2 == 4:
						choice = random.choice(rand_items_2)
						if choice in items:
							rand_money_2 = randint(1000, 2000)
							msg_content = f'Вам не очень повезло и с эпического бокса выпали деньги в размере - {rand_money_2}'
						else:
							items.append(choice)
							msg_content = f'С эпического бокса выпал предмет - {dict_items[choice]}'

			elif box == boxes[3]:
				if rand_num_1 <= 10:
					pet = [all_pets[5], boxes[3]]
					msg_content = 'С легендарного бокса вам выпал питомец - Хомяк(Увеличивает выпадения коинов)'
					# Хомяк

				elif rand_num_1 > 10 and rand_num_1 <= 30:
					pet = [all_pets[2], boxes[3]]
					msg_content = 'С легендарного бокса вам выпал питомец - Каска(Увеличивает стоимость клада)'
					# Каска

				elif rand_num_1 > 30 and rand_num_1 <= 33:
					pet = [all_pets[3], boxes[3]]
					msg_content = 'С легендарного бокса вам выпал питомец - Лупа(Увеличивает шанс найти клад)'
					# Лупа

				elif rand_num_1 > 33 and rand_num_1 <= 63:
					pet = [all_pets[0], boxes[3]]
					msg_content = 'С легендарного бокса вам выпал питомец - Кошка(Обычный питомец)'
					# Кошка

				elif rand_num_1 > 63:
					rand_num_2 = randint(1, 4)

					if rand_num_2 == 1:
						rand_money = randint(5000, 11000)
						msg_content = f'Вам не очень повезло и с легендарного бокса выпали деньги в размере - {rand_money}'

					elif rand_num_2 == 2:
						rand_money = randint(7000, 15000)
						msg_content = f'Вам не очень повезло и с легендарного бокса выпали деньги в размере - {rand_money}'

					elif rand_num_2 == 3:
						choice = random.choice(rand_items_1)
						if choice in items:
							rand_money_2 = randint(6000, 8000)
							msg_content = f'Вам не очень повезло и с легендарного бокса выпали деньги в размере - {rand_money_2}'
						else:
							items.append(choice)
							msg_content = f'С легендарного бокса выпал предмет - {dict_items[choice]}'

					elif rand_num_2 == 4:
						choice = random.choice(rand_items_2)
						if choice in items:
							rand_money_2 = randint(6000, 8000)
							msg_content = f'Вам не очень повезло и с легендарного бокса выпали деньги в размере - {rand_money_2}'
						else:
							items.append(choice)
							msg_content = f'С легендарного бокса выпал предмет - {dict_items[choice]}'
		
			elif box == boxes[4]:
				if rand_num_1 <= 25:
					pet = [all_pets[5], boxes[4]]
					msg_content = 'С невероятного бокса вам выпал питомец - Хомяк(Увеличивает выпадения коинов)'
					# Хомяк

				elif rand_num_1 > 25 and rand_num_1 <= 50:
					pet = [all_pets[2], boxes[4]]
					msg_content = 'С невероятного бокса вам выпал питомец - Каска(Увеличивает стоимость клада)'
					# Каска

				elif rand_num_1 > 50 and rand_num_1 <= 65:
					pet = [all_pets[3], boxes[4]]
					msg_content = 'С невероятного бокса вам выпал питомец - Лупа(Увеличивает шанс найти клад)'
					# Лупа

				elif rand_num_1 > 65 and rand_num_1 <= 70:
					pet = [all_pets[4], boxes[4]]
					msg_content = 'С невероятного бокса вам выпал питомец - Попугай(Уменьшает шанс быть пойманым)'
					# Попугай

				elif rand_num_1 > 70:
					rand_num_2 = randint(1, 5)

					if rand_num_2 == 1:
						rand_num_3 = randint(1, 3)

						if rand_num_3 >= 1 and rand_num_3 <= 2:
							rand_money = randint(5000, 12000)
							msg_content = f'Вам не очень повезло и с невероятного бокса выпали деньги в размере - {rand_money}'

						elif rand_num_3 > 2:
							rand_money = randint(50000, 120000)
							msg_content = f'С невероятного бокса вы сорвали джек-пот в размере - {rand_money}!'

					elif rand_num_2 == 2:
						rand_money = randint(19000, 25000)
						msg_content = f'Вам не очень повезло и с невероятного бокса выпали деньги в размере - {rand_money}'
					
					elif rand_num_2 == 3:
						choice = random.choice(rand_items_1)
						if choice in items:
							rand_money_2 = randint(18000, 20000)
							msg_content = f'Вам не очень повезло и с невероятного бокса выпали деньги в размере - {rand_money_2}'
						else:
							items.append(choice)
							msg_content = f'С невероятного бокса выпал предмет - {dict_items[choice]}'

					elif rand_num_2 == 4:
						choice = random.choice(rand_items_2)
						if choice in items:
							rand_money_2 = randint(18000, 20000)
							msg_content = f'Вам не очень повезло и с невероятного бокса выпали деньги в размере - {rand_money_2}'
						else:
							items.append(choice)
							msg_content = f'С невероятного бокса выпал предмет - {dict_items[choice]}'

			money += rand_money
			if pet:
				if pet[0] in pets:
					coins += dict_boxes[pet[1]][1]
					msg_content = f'К сожалению выйграный питомец уже есть в вашем инвертаре, по этому вам выпали коины в размере - {dict_boxes[pet[1]][1]}'
				else:
					pets.append(pet[0])

			emb = discord.Embed(title = f'Бокс - {dict_boxes[box][0]}', description = f'**{msg_content}**', colour = discord.Color.green())
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )

			sql = ("""UPDATE users SET items = %s, pets = %s, money = %s WHERE user_id = %s AND guild_id = %s""")
			val = (json.dumps(items), json.dumps(pets), money, ctx.author.id, ctx.guild.id)

			self.cursor.execute(sql, val)
			self.conn.commit()
		elif not state:
			emb = discord.Embed(title = f'Ошибка!', description = f'**В вашем инвертаре нет такого лут-бокса!**', colour = discord.Color.green())
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')


	@commands.command(aliases=['removerole'], hidden = True, name = 'remove-role', description = '**Удаляет указаную роль из профиля пользователя(Объязательно используйте эту команду для снятия роли, а не простое удаление роли через сам дискорд!, Cooldown - 3 часа)', usage = 'remove-role [@Участник] [@Роль]')
	@commands.cooldown(1, 14400, commands.BucketType.member)
	@commands.has_permissions( administrator = True )
	async def remove_role(self, ctx, member: discord.Member, role: discord.Role):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member.bot:			
			emb = discord.Embed( title = 'Ошибка!', description = f"**Вы не можете снимать роль боту!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return

		if member in ctx.guild.members:
			data = DB().sel_user(target = member)
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f"**На сервере не существует такого пользователя!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.remove_role.reset_cooldown(ctx)
			return

		items = data['items']
		if role.id in items:
			items.remove(role.id)

			try:
				await member.remove_roles(role)
			except:
				pass

			sql = ("""UPDATE users SET items = %s WHERE user_id = %s AND guild_id = %s""")
			val = (json.dumps(items), member.id, ctx.guild.id)

			self.cursor.execute(sql, val)
			self.conn.commit()

			emb = discord.Embed( title = 'Успех!', description = f"**Снятия роли прошло успешно, роль - {role.mention} была удаленна из эго профиля!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )


	@commands.command(aliases=['addcash'], hidden = True, name = 'add-cash', description = '**Добавляет указаний тип валюты в профиль**', usage = 'add-cash [@Участник] [Название валюты] [Количество]')
	@commands.has_permissions( administrator = True )
	@commands.cooldown(1, 14400, commands.BucketType.member)
	async def add_cash( self, ctx, member: discord.Member, typem: str, num: int ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member.bot:			
			emb = discord.Embed( title = 'Ошибка!', description = f"**Вы не можете добавлять деньги боту!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return

		if member in ctx.guild.members:
			data = DB().sel_user(target = member)
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f"**На сервере не существует такого пользователя!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.add_cash.reset_cooldown(ctx)
			return

		coins_member = data['coins']
		cur_money = data['money']

		if typem == 'money':
			cur_money += num
		elif typem == 'coins':
			coins_member += num 
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f"**Укажите правильную единицу!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.add_cash.reset_cooldown(ctx)
			return

		emb = discord.Embed( description = f"**Вы успешно добавили значений в профиль {member.name}**", colour = discord.Color.green() )
		emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
		await ctx.send( embed = emb )

		sql = ("""UPDATE users SET money = %s, coins = %s WHERE user_id = %s AND guild_id = %s""")
		val = (cur_money, coins_member, member.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()


	@commands.command(aliases=['removecash'], hidden = True, name = 'remove-cash', description = '**Удаляет указаний тип валюты из профиля**', usage = 'remove-cash [@Участник] [Название валюты] [Количество]')
	@commands.has_permissions( administrator = True )
	@commands.cooldown(1, 14400, commands.BucketType.member)
	async def remove_cash( self, ctx, member: discord.Member, typem: str, num: int ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member.bot:			
			emb = discord.Embed( title = 'Ошибка!', description = f"**Вы не можете снимать деньги боту!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return

		if member in ctx.guild.members:
			data = DB().sel_user(target = member)
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f"**На сервере не существует такого пользователя!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.remove_cash.reset_cooldown(ctx)
			return

		coins_member = data['coins']
		cur_money = data['money']

		if typem == 'money':
			cur_money -= num
		elif typem == 'coins':
			coins_member -= num 
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f"**Укажите правильную единицу!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.remove_cash.reset_cooldown(ctx)
			return

		emb = discord.Embed( description = f"**Вы успешно добавили значений в профиль {member.name}**", colour = discord.Color.green() )
		emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
		await ctx.send( embed = emb )

		sql = ("""UPDATE users SET money = %s, coins = %s WHERE user_id = %s AND guild_id = %s""")
		val = (cur_money, coins_member, member.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()


	@commands.command(description = '**Этой командой можно ограбить пользователя(Cooldown 24 часа)**', usage = 'rob [@Участник]')
	@commands.cooldown(1, 86400, commands.BucketType.member)
	async def rob( self, ctx, member: discord.Member ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		data1 = DB().sel_user(target = ctx.author)
		cur_state_pr = data1['prison']

		if member.bot:			
			emb = discord.Embed( title = 'Ошибка!', description = f"**Вы не можете красть деньги у бота!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return

		if cur_state_pr == False:
			if member in ctx.guild.members:
				data2 = DB().sel_user(target = member)
			else:
				emb = discord.Embed( title = 'Ошибка!', description = f"**На сервере не существует такого пользователя!**", colour = discord.Color.green() )
				emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
				emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
				await ctx.send( embed = emb )
				await ctx.message.add_reaction('❌')
				self.rob.reset_cooldown(ctx)
				return

			rand_num = randint( 1, 100 ) 
			crimed_member_money = data2['money']

			def rob_func( num, member ):
				data = DB().sel_user(target = member)
				cur_money = data['money'] + num
				prison = data['prison']
				items = data['items']
				state = False

				if member == ctx.author:
					if cur_money <= -5000:
						items = []
						prison = True
						state = True

				sql = ("""UPDATE users SET money = %s, items = %s, prison = %s WHERE user_id = %s AND guild_id = %s""")
				val = (cur_money, json.dumps(items), str(prison), member.id, member.guild.id)

				self.cursor.execute(sql, val)
				self.conn.commit()

				return [state, data['money']]

			if rand_num <= 40:
				state = rob_func( -10000, ctx.author )
				if state[0] == True:
					emb = discord.Embed( description = f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Ваш текущий баланс: {state[1]}**' , colour = discord.Color.green() )
					emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
					emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
					await ctx.author.send(embed = emb)
					return
				else:
					emb = discord.Embed( description = f"**Вас задержала полиция. Вы откупились потеряв 10000$**", colour = discord.Color.green() )
					emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
					emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
					await ctx.send( embed = emb )
			elif rand_num > 40 and rand_num <= 80:
				emb = discord.Embed( description = f"**Вы не смогли ограбить указаного пользователя**", colour = discord.Color.green() )
				emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
				emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
				await ctx.send( embed = emb )
			elif rand_num > 80:
				rand_num_1 = randint(1,2)
				cr_money = crimed_member_money // 4 * rand_num_1

				rob_func( cr_money, ctx.author )
				rob_func( int(cr_money * -1), member )

				emb = discord.Embed( description = f"**Вы смогли ограбить пользователя на суму {cr_money}**", colour = discord.Color.green() )
				emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
				emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
				await ctx.send( embed = emb )
		elif cur_state_pr == True:
			emb = discord.Embed( description = f"**Вы не забыли? Вы сейчас в тюрме!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.rob.reset_cooldown(ctx)
			return


	@commands.command(description = '**Незаконная добыча денег(Cooldown - 12 часов)**', usage = 'crime')
	@commands.cooldown(1, 43200, commands.BucketType.member)
	async def crime( self, ctx ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		data = DB().sel_user(target = ctx.author)
		cur_state_pr = data['prison']

		if cur_state_pr == False:
			rand_num = randint( 1, 100 ) 
			def crime_func( num, member ):
				data = DB().sel_user(target = member)
				cur_money = data['money'] + num
				prison = data['prison']
				items = data['items']

				if cur_money <= -5000:
					prison = True
					items = []
					return [True, data['money']]

				sql = ("""UPDATE users SET money = %s, prison = %s, items = %s WHERE user_id = %s AND guild_id = %s""")
				val = (cur_money, str(prison), json.dumps(items), member.id, member.guild.id)

				self.cursor.execute(sql, val)
				self.conn.commit()

			if rand_num <= 40:
				state = crime_func( -5000, ctx.author )
				if state[0] == True:
					emb = discord.Embed( description = f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Ваш текущий баланс: {state[1]}**' , colour = discord.Color.green() )
					emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
					emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
					await ctx.author.send(embed = emb)
					return
				else:
					emb = discord.Embed( description = f"**Вас задержала полиция. Вы откупились потеряв 10000$**", colour = discord.Color.green() )
					emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
					emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
					await ctx.send( embed = emb )
			elif rand_num > 40 and rand_num <= 80:
				emb = discord.Embed( description = f"**Вы не смогли совершить идею заработка денег**", colour = discord.Color.green() )
				emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
				emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
				await ctx.send( embed = emb )
			elif rand_num > 80:
				rand_money = randint(20, 1000)	
				crime_func( rand_money, ctx.author )
				emb = discord.Embed( description = f"**Вы смогли заработать на незаконной работе - {rand_money}$**", colour = discord.Color.green() )
				emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
				emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
				await ctx.send( embed = emb )
		elif cur_state_pr == True:
			emb = discord.Embed( description = f"**Вы не забыли? Вы сейчас в тюрме!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.crime.reset_cooldown(ctx)
			return


	@commands.command(description = '**Показывает ваш инвертарь**', usage = 'invertory')
	async def invertory( self, ctx ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		data = DB().sel_user(target = ctx.author)
		Prefix = DB().sel_guild(guild = ctx.guild)['prefix']
		number = data['text_channels']

		def func_inv():
			items = data['items']
			pets = data['pets']
			roles_content = ' '
			items_content = ' '
			box_content = ' '
			pets_content = ' '
			check_state = True
			names_of_items = {
				'sim': 'Сим-карта',
				'tel': 'Телефон',
				'metal_1': 'Металоискатель 1-го уровня',
				'metal_2': 'Металоискатель 2-го уровня',
				'mop': 'Швабра',
				'broom': 'Метла',
				'gloves': 'Перчатки'
			}
			boxes = {
				'box-I': 'Невероятный бокс',
				'box-L': 'Легендарный бокс',
				'box-E': 'Эпический бокс',
				'box-R': 'Редкий бокс',
				'box-C': 'Обычный бокс'
			}
			dict_pets = {
				'cat': 'Кошка',
				'dog': 'Собачка',
				'helmet': 'Каска',
				'loupe': 'Лупа',
				'parrot': 'Попугай',
				'hamster': 'Хомяк'
			}

			if items == []:
				items_content = f'Ваш инвертарь пуст. Купите что-нибудь с помощью команды - {Prefix}buy\n'
				check_state = False
			elif items != []:
				for i in items:
					if isinstance( i, list ) == True:
						box_content = box_content + f'{boxes[i[0]]} - {i[1]}шт \n'
					else:
						if isinstance( i, str ) == True:
							items_content = items_content + f'{names_of_items[i]}\n '
						elif isinstance( i, int ) == True:
							role = get( ctx.guild.roles, id = i )
							roles_content = roles_content + f'{role.mention}\n '

				for pet in pets:
					pets_content += f'{dict_pets[pet]}\n '

			if check_state:
				if items_content != ' ':
					items_content = f'**Ваши предметы:**\n{items_content}\n'

			if roles_content != ' ':
				roles_content = f'**Ваши роли:**\n{roles_content}\n'

			if box_content != ' ':
				box_content = f'**Ваши лут-боксы:**\n{box_content}\n'

			if pets_content != ' ':
				pets_content = f'**Ваши питомцы:**\n{pets_content}\n'

			return [items_content, roles_content, box_content, pets_content]

		emb = discord.Embed( title = 'Ваш инвертарь', description = f'{func_inv()[0]}{func_inv()[1]}{func_inv()[2]}{func_inv()[3]}**Текстовые каналы:** {number}', colour = discord.Color.green() )
		emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
		await ctx.send( embed = emb )


	@commands.command(aliases=['profile-color', 'profilecolor'], name = 'set-profile-color', description = '**Ставит новый цвет для вашего профиля**', usage = 'set-profile-color [Цвет]')
	async def profile_color(self, ctx, color: str = None):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		colors = ['green', 'lime', 'orange', 'purple', 'pink', 'red', 'зелёный', "лаймовый", "оранжевый", "фиолетовый", "розовый", "красный"]
		colour = {
			'green': "green",
			'lime': "lime",
			'orange': "orange",
			'purple': "purple",
			'pink': "pink",
			'red': "red",
			'зелёный': 'green', 
			"лаймовый": 'lime', 
			"оранжевый": 'orange', 
			"фиолетовый": 'purple', 
			"розовый": 'pink', 
			"красный": 'red'
		}

		if not color:
			emb = discord.Embed( description = f"**Выберите цвет профиля среди этих: зелёный, лаймовый, оранжевый, фиолетовый, розовый, красный. Стандартный цвет - лаймовый.**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			return
		elif color.lower() not in colors:
			emb = discord.Embed( title = 'Ошибка!', description = f"**Такого цвета нет! Выберите среди этих: зелёный, лаймовый, оранжевый, фиолетовый, розовый, красный. Стандартный цвет - лаймовый.**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			return

		DB().sel_user(target = ctx.author)
		sql = ("""UPDATE users SET profile = %s WHERE user_id = %s AND guild_id = %s""")
		val = (colour[color.lower()], ctx.author.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		emb = discord.Embed( description = f"**Вы успешно поменяли цвет своего профиля на {color}**", colour = discord.Color.green() )
		emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
		await ctx.send( embed = emb )


	@commands.command(description = '**Показывает профиль указаного пользователя, без упоминания ваш профиль**', usage = 'profile |@Участник|')
	async def profile( self, ctx, member: typing.Optional[discord.Member] = None ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if not member:
			member = ctx.author

		if member.bot:			
			emb = discord.Embed( title = 'Ошибка!', description = f"**Вы не можете просмотреть профиль бота!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return

		if member in ctx.guild.members:
			user_data = DB().sel_user(target = member)
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f"**На сервере не существует такого пользователя!**", colour = discord.Color.green() )
			emb.set_author( name = self.client.user.name, icon_url = self.client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = self.client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return

		def crop(im, s):
			w, h = im.size
			k = w / s[0] - h / s[1]
			if k > 0: im = im.crop(((w - h) / 2, 0, (w + h) / 2, h))
			elif k < 0: im = im.crop((0, (h - w) / 2, w, (h + w) / 2))

			return im.resize(s, Image.ANTIALIAS)

		colours = {
			'green': ['#b8f9ff', '#b8f9ff'],
			'lime': ['#787878', '#787878'],
			'orange': ["#595959", "#595959"],
			'purple': ['#a6de6f', "#595959"],
			'pink': ['#cadedb','#cadedb'],
			'red': ['#f3f598', "#595959"],
			None: ['#787878', '#787878']
		}

		user_data = DB().sel_user(target = member)
		user = str(member.name)
		user_tag = str(member.discriminator)
		user_id = int(member.id)
		user_exp = int(user_data['exp'])
		user_level = int(user_data['lvl'])
		user_warns = len(user_data['warns'])
		user_coins = int(user_data['coins'])
		user_money = int(user_data['money'])
		user_reputation = int(user_data['reputation'])
		user_state_prison = user_data['prison']
		user_profile = user_data['profile']

		if user_state_prison:
			user_state_prison = 'Сейчас в тюрме'
		elif not user_state_prison:
			user_state_prison = 'На свободе'

		size = (600, 290)

		if not user_profile:  
			img = Image.open(self.BACKGROUND)
		elif user_profile:
			img = Image.open(self.BACKGROUND[:-8]+f"{user_profile}.png")

		img = crop(img, size)
		responce = Image.open(io.BytesIO(await member.avatar_url.read())).convert('RGBA').resize((100, 100), Image.ANTIALIAS)

		img.paste(responce, (15, 0, 115, 100))
		idraw = ImageDraw.Draw(img)

		bigtext = ImageFont.truetype( self.FONT, size = 34 )
		midletext = ImageFont.truetype( self.FONT, size = 23)

		idraw.text((140, 20), u'Профиль {}'.format(user), font = bigtext )
		idraw.text((140, 60), f'Репутация: {user_reputation}', font = bigtext, fill = 'black' )

		idraw.text((140, 105), f'Тег: {user_tag}', font = midletext, fill = colours[user_profile][0]) 
		idraw.text((140, 130), f'Id: {user_id}', font = midletext, fill = colours[user_profile][0])
		idraw.text((140, 155), f'Предупрежденний: {user_warns}', font = midletext, fill = colours[user_profile][0])
		idraw.text((140, 180), f'Тюрма: {user_state_prison}', font = midletext, fill = colours[user_profile][0])

		idraw.text((405, 105), f'Exp: {user_exp}', font = midletext, fill = colours[user_profile][1])
		idraw.text((405, 130), f'Уровень: {user_level}', font = midletext, fill = colours[user_profile][1])
		idraw.text((405, 155), f'Монет: {user_coins}', font = midletext, fill = colours[user_profile][1] )
		idraw.text((405, 180), f'Денег: {user_money}$', font = midletext, fill = colours[user_profile][1])

		idraw.text((15, 245), self.FOOTER, font = midletext)

		img.save(self.SAVE)
		await ctx.send( file = discord.File( fp = self.SAVE ) )


def setup( client ):
	client.add_cog(Economy(client))
