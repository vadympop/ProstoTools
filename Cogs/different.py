import discord
import json
import random
import os
import typing
import asyncio
import mysql.connector
import requests 
import psutil as ps
from datetime import datetime
from Cybernator import Paginator
from discord.ext import commands
from discord.utils import get
from discord.voice_client import VoiceClient
from discord.ext.commands import Bot
from random import randint
from googletrans import Translator
from configs import configs
from Tools.database import DB

class Different(commands.Cog, name = 'Different'):

	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(user = 'root', password = os.environ['DB_PASSWORD'], host = 'localhost', database = 'data')
		self.cursor = self.conn.cursor(buffered = True)
		self.FOOTER = configs['FOOTER_TEXT']


	@commands.command(aliases=['usersend'], name = 'user-send', description = '**Отправляет сообщения указаному участнику(Cooldown - 1 мин после двох попыток)**', usage = 'user-send [@Участник] [Сообщения]')
	@commands.cooldown(2, 60, commands.BucketType.member)
	async def send( self, ctx, member: discord.Member, *, message ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)

		purge = self.client.self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		data = DB().sel_user(target = ctx.author)
		coins_member = data['coins']
		cur_items = data['items']

		sql = ("""UPDATE users SET coins = coins - 50 WHERE user_id = %s AND guild_id = %s""")
		val = (ctx.author.id, ctx.guild.id)

		if cur_items != []:
			if "sim" in cur_items and "tel" in cur_items and coins_member > 50:
				self.cursor.execute(sql, val)
				self.conn.commit()

				emb = discord.Embed( title = f'Новое сообщения от {ctx.author.name}', description = f'**{message}**', colour = discord.Color.green() )
				emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
				emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
				await member.send( embed = emb )
			else:
				emb = discord.Embed( title = 'Ошибка!', description = f'**У вас нет необходимых предметов или не достаточно коинов!**', colour = discord.Color.green() )
				emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
				emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
				await ctx.send( embed = emb )
				await ctx.message.add_reaction('❌')
				self.send.reset_cooldown(ctx)
				return
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f'**У вас нет необходимых предметов!**', colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.send.reset_cooldown(ctx)
			return


	@commands.command(aliases=['devs'], name = 'feedback', description = '**Отправляет описания бага в боте разработчикам или идею к боту(Cooldown - 2ч)**', usage = 'feedback [bug/idea] [Описания бага или идея к боту]')
	@commands.cooldown(1, 7200, commands.BucketType.member)
	async def devs( self, ctx, typef, *, msg ):
		DB().add_amout_command(entity=ctx.command.name)
		client = self.client

		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		prch = get( client.users, id = 660110922865704980 )
		mrkl = get( client.users, id = 404224656598499348 )

		if typef == 'bug' or typef == 'баг':
			emb = discord.Embed( title = f'Описания бага от пользователя - {ctx.author.name}, с сервера - {ctx.guild.name}', description = f'**Описания бага:\n{msg}**', colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
			await prch.send( embed = emb )
			await mrkl.send( embed = emb )
		elif typef == 'idea' or typef == 'идея':
			emb = discord.Embed( title = f'Новая идея от пользователя - {ctx.author.name}, с сервера - {ctx.guild.name}', description = f'**Идея:\n{msg}**', colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
			await prch.send( embed = emb )
			await mrkl.send( embed = emb )
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f'**Вы не правильно указали флаг!**', colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			self.devs.reset_cooldown(ctx)
			return


	@commands.command(aliases=['userinfo', 'user'], name = 'user-info', description = '**Показывает информацию указаного учасника**', usage = 'user-info [@Участник]')
	async def userinfo( self, ctx, member: discord.Member = None ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if not member:
			member = ctx.author

		if member.bot:			
			emb = discord.Embed( title = 'Ошибка!', description = f"**Вы не можете просмотреть информацию о боте!**", colour = discord.Color.green() )
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return

		t = Translator()
		data = DB().sel_user(target = member)
		all_message = data['messages'][1]
		joined_at_en = datetime.strftime(member.joined_at, '%d %B %Y %X')
		joined_at = t.translate(joined_at_en, dest='ru', src='en').text
		created_at_en = datetime.strftime(member.created_at, '%d %B %Y %X')
		created_at = t.translate(created_at_en, dest='ru', src='en').text

		get_bio = lambda: '' if data['bio'] == '' else f"""\n\n**Краткая информация о пользователе:**\n{data['bio']}\n\n"""
		activity = member.activity

		def get_activity():
			if not activity:
				return ''

			if activity.emoji and activity.emoji.is_unicode_emoji():
				activity_info = f'\n**Пользовательский статус:** {activity.emoji} {activity.name}'
			else:
				if activity.emoji in self.client.emojis:
					activity_info = f'\n**Пользовательский статус:** {activity.emoji} {activity.name}'
				else:
					activity_info = f'\n**Пользовательский статус:** {activity.name}'

			return activity_info

		statuses = {
			'dnd': '<:dnd:730391353929760870> - Не беспокоить',
			'online': '<:online:730393440046809108> - В сети',
			'offline': '<:offline:730392846573633626> - Не в сети',
			'idle': '<:sleep:730390502972850256> - Отошёл',
		}

		emb = discord.Embed( title = f'Информация о пользователе - {member}', colour = discord.Color.green() )
		emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
		emb.set_thumbnail( url = member.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
		emb.add_field( name = 'Основная информация', value = f'{get_bio()}**Имя пользователя:** {member}\n**Статус:** {statuses[member.status.name]}{get_activity()}\n**Id пользователя:** {member.id}\n**Акаунт созданн:** {created_at}\n**Присоиденился:** {joined_at}\n**Сообщений:** {all_message}', inline = False )
		await ctx.send( embed = emb )  


	@commands.command(aliases=['useravatar', 'avatar'], name = 'user-avatar', description = '**Показывает аватар указаного учасника**', usage = 'user-avatar [@Участник]')
	async def avatar( self, ctx, member: typing.Optional[ discord.Member ] = None ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if not member:
			emb = discord.Embed( title = f'Аватар {ctx.author.name}', colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_image( url = ctx.author.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )
		else:
			emb = discord.Embed( title = f'Аватар {member.name}', colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_image( url = member.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )


	@commands.command(name="info-bot", aliases=["botinfo", "infobot", "bot-info"], usage="info-bot", description="Подробная информация о боте")
	async def bot(self, ctx):
		DB().add_amout_command(entity=ctx.command.name)
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		def bytes2human(number, typer=None):
			if typer == "system":
				symbols = ('KБ', 'МБ', 'ГБ', 'TБ', 'ПБ', 'ЭБ', 'ЗБ', 'ИБ')
			else:
				symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')

			prefix = {}
			for i, s in enumerate(symbols):
				prefix[s] = 1 << (i + 1) * 10

			for s in reversed(symbols):
				if number >= prefix[s]:
					value = float(number) / prefix[s]
					return '%.1f%s' % (value, s)

			return f"{number}B"
		
		embed1 = discord.Embed(title=f"{self.client.user.name}#{self.client.user.discriminator}", description=f"Информация о боте **{self.client.user.name}**.\nМного-функциональный бот со своей экономикой, кланами и системой модерации!", color=discord.Color.green())
		embed1.add_field(name='Создатель бота:', value="Mr. Kola#0684, 𝚅𝚢𝚝𝚑𝚘𝚗.𝚕𝚞𝚒#2020", inline=False)
		embed1.add_field(name=f'Проект был созданн с помощью:', value="discord.py, sanic", inline=False)
		embed1.add_field(name=f'Участников:', value=len(self.client.users), inline=False)
		embed1.add_field(name=f'Серверов:', value=len(self.client.guilds), inline=False)
		embed1.add_field(name=f'Шардов:', value=self.client.shard_count, inline=False)
		embed1.add_field(name=f'Приглашение Бота:', value="[Тык](https://discord.com/api/oauth2/authorize?client_id=700767394154414142&permissions=8&scope=bot)", inline=False)
		embed1.add_field(name=f'Сервер помощьи:', value="[Тык](https://discord.gg/CXB32Mq)", inline=False)
		embed1.set_thumbnail(url=self.client.user.avatar_url)
		embed1.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)

		mem = ps.virtual_memory()
		ping = self.client.latency

		ping_emoji = "🟩🔳🔳🔳🔳"
		ping_list = [
			{"ping": 0.00000000000000000, "emoji": "🟩🔳🔳🔳🔳"},
			{"ping": 0.10000000000000000, "emoji": "🟧🟩🔳🔳🔳"},
			{"ping": 0.15000000000000000, "emoji": "🟥🟧🟩🔳🔳"},
			{"ping": 0.20000000000000000, "emoji": "🟥🟥🟧🟩🔳"},
			{"ping": 0.25000000000000000, "emoji": "🟥🟥🟥🟧🟩"},
			{"ping": 0.30000000000000000, "emoji": "🟥🟥🟥🟥🟧"},
			{"ping": 0.35000000000000000, "emoji": "🟥🟥🟥🟥🟥"}
		]
		for ping_one in ping_list:
			if ping <= ping_one["ping"]:
				ping_emoji = ping_one["emoji"]
				break

		embed2 = discord.Embed(title='Статистика Бота', color=discord.Color.green())
		embed2.add_field(name='Использование CPU', value=f'В настоящее время используется: {ps.cpu_percent()}%', inline=True)
		embed2.add_field(name='Использование RAM', value=f'Доступно: {bytes2human(mem.available, "system")}\nИспользуется: {bytes2human(mem.used, "system")} ({mem.percent}%)\nВсего: {bytes2human(mem.total, "system")}', inline=True)
		embed2.add_field(name='Пинг Бота', value=f'Пинг: {ping * 1000:.0f}ms\n`{ping_emoji}`', inline=True)

		for disk in ps.disk_partitions():
			usage = ps.disk_usage(disk.mountpoint)
			embed2.add_field(name="‎‎‎‎", value=f'```{disk.device}```', inline=False)
			embed2.add_field(name='Всего на диске', value=bytes2human(usage.total, "system"), inline=True)
			embed2.add_field(name='Свободное место на диске', value=bytes2human(usage.free, "system"), inline=True)
			embed2.add_field(name='Используемое дисковое пространство', value=bytes2human(usage.used, "system"), inline=True)

		embeds = [embed1, embed2]
		message = await ctx.send(embed=embed1)
		page = Paginator(self.client, message, only=ctx.author, use_more=False, embeds=embeds, language="ru", timeout=120, use_exit=True, delete_message=False)
		await page.start()


	@commands.command(aliases=['server', 'serverinfo', 'guild', 'guildinfo', 'guild-info'], name = 'server-info', description = '**Показывает информацию о сервере**', usage = 'server-info')
	async def serverinfo( self, ctx ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		data = DB().sel_guild(guild = ctx.guild)
		guild = ctx.message.guild
		guild_name = guild.name
		guild_id = guild.id
		guild_reg = guild.region.name
		guild_owner_name = guild.owner
		guild_channels = len(guild.channels)
		guild_text_channels = len(guild.text_channels)
		guild_voice_channels = len(guild.voice_channels)
		guild_categories = len(guild.categories)
		guild_member_count = int(guild.member_count)
		guild_roles = len(guild.roles)
		guild_created_at_year = guild.created_at.year
		guild_created_at_month = guild.created_at.month
		guild_created_at_day = guild.created_at.day
		guild_created_at_hour = guild.created_at.hour
		dnd = 0
		sleep = 0
		online = 0
		offline = 0
		bots = 0
		time = data['timedelete_textchannel']
		max_warns = data['max_warns']
		all_message = data['all_message']

		if data['idea_channel']:
			ideachannel = f"<#{int(data['idea_channel'])}>"
		else:
			ideachannel = 'Не указан'

		if data['purge'] == 1:
			purge = 'Удаления команд включено'
		elif data['purge'] == 0:
			purge = 'Удаления команд выключено'

		if data['textchannels_category']:
			text_category = get( ctx.guild.categories, id = int(data['textchannels_category']) ).name
		else:
			text_category = 'Не указана'

		verifications = {
			"none": ":white_circle: — Нет верификации",
			"low": ":green_circle: — Маленькая верификация",
			"medium": ":yellow_circle: — Средняя верификация",
			"high": ":orange_circle: — Большая верификация",
			"extreme": ":red_circle: - Наивысшая верификация"
		}
		regions = {
			"us_west": ":flag_us: — Запад США",
			"us_east": ":flag_us: — Восток США",
			"us_central": ":flag_us: — Центральный офис США",
			"us_south": ":flag_us: — Юг США",
			"sydney": ":flag_au: — Сидней",
			"eu_west": ":flag_eu: — Западная Европа",
			"eu_east": ":flag_eu: — Восточная Европа",
			"eu_central": ":flag_eu: — Центральная Европа",
			"singapore": ":flag_sg: — Сингапур",
			"russia": ":flag_ru: — Россия",
			"southafrica": ":flag_za:  — Южная Африка",
			"japan": ":flag_jp: — Япония",
			"brazil": ":flag_br: — Бразилия",
			"india": ":flag_in: — Индия",
			"hongkong": ":flag_hk: — Гонконг",
		}
		monthes = {
			1: 'Января',
			2: 'Февраля',
			3: 'Марта',
			4: 'Апреля',
			5: 'Мая',
			6: 'Июня',
			7: 'Июля',
			8: 'Августа',
			9: 'Сентября',
			10: 'Октября',
			11: 'Ноября',
			12: 'Декабря'
		}

		dnd = len([str(member.id) for member in ctx.guild.members if member.status.name == 'dnd'])
		sleep = len([str(member.id) for member in ctx.guild.members if member.status.name == 'idle'])
		online = len([str(member.id) for member in ctx.guild.members if member.status.name == 'online'])
		offline = len([str(member.id) for member in ctx.guild.members if member.status.name == 'offline'])
		bots = len([str(member.id) for member in ctx.guild.members if member.bot])

		emb = discord.Embed( title = 'Информация о вашем сервере', colour = discord.Color.green() )

		emb.add_field( 
			name = f'Основная информация', 
			value = f'**Название сервера:** {guild_name}\n**Id сервера:** {guild_id}\n**Регион сервера:** {regions[guild_reg]}\n**Уровень верификации:** {verifications[guild.verification_level.name]}\n**Всего сообщений:** {all_message}\n**Владелец сервера:** {guild_owner_name}\n**Созданн:** {guild_created_at_day} {monthes[guild_created_at_month]} {guild_created_at_year} года в {guild_created_at_hour} часов', 
			inline = False 
		)
		emb.add_field( 
			name = 'Статистика', 
			value = f'**<:channels:730400768049414144> Всего каналов:** {guild_channels}\n**<:text_channel:730396561326211103> Текстовых каналов:** {guild_text_channels}\n**<:voice_channel:730399079418429561> Голосовых каналов:** {guild_voice_channels}\n**<:category:730399838897963038> Категорий:** {guild_categories}\n**<:role:730396229220958258> Количество ролей:** {guild_roles}', 
			inline = False 
		)
		emb.add_field( 
			name = 'Участники', 
			value = f'**:baby: Общее количество участников:** {guild_member_count}\n**<:bot:731819847905837066> Боты:** {bots}\n**<:sleep:730390502972850256> Отошли:** {sleep}\n**<:dnd:730391353929760870> Не беспокоить:** {dnd}\n**<:offline:730392846573633626> Не в сети:** {offline}\n**<:online:730393440046809108> В сети:** {online}', 
			inline = False 
		)
		emb.add_field( 
			name = 'Настройки сервера', 
			value = f'**Канал идей:** {ideachannel}\n**Удаления команд:** {purge}\n**Категория приватных текстовых каналов:** {text_category}\n**Максимальное количество предупрежденний:** {max_warns}\n**Время удаления приватного текстового канала:** {time}мин',
			inline = False
		 )

		emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )

		await ctx.send( embed = emb )


	@commands.command(aliases=['idea', 'guildidea'], name = 'guild-idea', description = '**Отправляет вашу идею (Cooldown - 30мин)**', usage = 'guild-idea [Ваша идея]')
	@commands.cooldown(1, 7200, commands.BucketType.member)
	async def idea( self, ctx, *, arg ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		data = DB().sel_guild(guild = ctx.guild)
		idea_channel_id = data['idea_channel']

		if not idea_channel_id:
			emb = discord.Embed( title = 'Ошибка!', description = '**Не указан канал идей. Обратитесь к администации сервера**', colour = discord.Color.green() )
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )
			self.idea.reset_cooldown(ctx)
			await ctx.message.add_reaction('❌')
			return
		elif idea_channel_id:
			idea_channel = client.get_channel(int(idea_channel_id))
			emb = discord.Embed( title = 'Новая идея!', description = f'**От {ctx.author.mention} прийшла идея: {arg}**', colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_thumbnail( url = ctx.author.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
			await idea_channel.send( embed = emb)


	@commands.command(description = '**Отправляет ссылку на приглашения бота на сервер**', usage = 'invite')
	async def invite( self, ctx ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		emb = discord.Embed( title = 'Пригласи бота на свой сервер =).**Жмякай!**', url = 'https://discord.com/api/oauth2/authorize?client_id=700767394154414142&permissions=8&scope=bot', colour = discord.Color.green() )
		emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
		emb.set_thumbnail( url = client.user.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
		await ctx.send( embed = emb )


	@commands.command(aliases=['msg-f', 'msg-forward', 'msgf'], name = 'message-forward', description = '**Перенаправляет ваше сообщения в указаный канал(Cooldown - 2 мин)**', usage = 'message-forward [Id Канала] [Сообщения]')
	@commands.cooldown(1, 120, commands.BucketType.member)
	async def msgforw( self, ctx, channel: int, *, msg ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		msgforw_channel = client.get_channel(channel)
		if ctx.author.permissions_in(msgforw_channel).send_messages:
			emb = discord.Embed( title = 'Новое сообщения!', description = f'{ctx.author.mention} Перенаправил сообщения в этот канал. ***Само сообщения: {msg}***', colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_thumbnail( url = ctx.author.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
			await msgforw_channel.send( embed = emb)
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f'**Отказанно в доступе! Вы не имеете прав в указном канале**', colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb)
			await ctx.message.add_reaction('❌')
			self.msgforw.reset_cooldown(ctx)
			return


	@commands.command(description = '**Отправляет ваше сообщения от именни бота(Cooldown - 30 сек после трёх попыток)**', usage = 'say [Сообщения]')
	@commands.cooldown(3, 30, commands.BucketType.member)
	async def say( self, ctx, *, text ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		await ctx.send(text)


	@commands.command(aliases=['rnum', 'randomnumber'], name = 'random-number', description = '**Пишет рандомное число в указаном диапазоне**', usage = 'random-number [Первое число (От)] [Второе число (До)]')
	async def rnum( self, ctx, rnum1: int, rnum2: int ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		random_num = randint( rnum1, rnum2 )
		emb = discord.Embed( title = f'Рандомное число от {rnum1} до {rnum2}', description = f'**Бот зарандомил число {random_num}**', colour = discord.Color.green() )
		emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
		emb.set_footer( text = self.FOOTER, icon_url = client.user.avatar_url )
		await ctx.send( embed = emb )

	
	@commands.command(description = '**Устанавливает краткое описания о вас**', usage = 'bio [Текст]')
	async def bio( self, ctx, *, text: str = None ):
		DB().add_amout_command(entity=ctx.command.name)
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if not text:
			sql = ("""UPDATE users SET bio = %s WHERE user_id = %s""")
			val = ('', ctx.author.id)

			self.cursor.execute(sql, val)
			self.conn.commit()

			await ctx.message.add_reaction('✅')

		if len(text) > 1000:
			await ctx.message.add_reaction('❌')
			return

		sql = ("""UPDATE users SET bio = %s WHERE user_id = %s""")
		val = (text, ctx.author.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		await ctx.message.add_reaction('✅')


	@commands.command(name='calc', aliases=['calculator', 'c'], description='Выполняет математические операции', usage='calc [Операция]')
	async def calc(self, ctx, *, exp = None):
		if not exp:
			await ctx.send('**Укажите пример!**')
			return

		link = 'http://api.mathjs.org/v4/'
		data = {"expr": [exp]}

		try:
			re = requests.get(link, params=data)
			responce = re.json()

			emb = discord.Embed(title='Калькулятор', color=discord.Color.green())
			emb.add_field(name='Задача:', value=exp)
			emb.add_field(name='Решение:', value=str(responce))
			await ctx.send(embed=emb)
		except:
			await ctx.send('**Это калькулятор, текст нельзя -.-**')

def setup( client ):
	client.add_cog(Different(client))