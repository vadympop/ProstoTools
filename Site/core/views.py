# Imports
import datetime
import json
import asyncio
import os
import socket

import mysql.connector
import requests

from Site.config import Config
from Site.core.utils import Utils
from Site.app import jinja
from sanic import Blueprint
from sanic.exceptions import NotFound, ServerError
from sanic import response

client = None
conn = mysql.connector.connect(user='root', passwd=os.environ['DB_PASSWORD'], host='localhost', db='data')
cursor = conn.cursor(buffered=True)
bp = Blueprint('views', url_prefix='/')

@bp.route('/')
async def index(request):
	cursor.execute("""SELECT count FROM bot_stats WHERE entity = 'all commands'""") # Database query
	amout_used_commands = cursor.fetchall()
	amout_used_commands.reverse()
	amout_used_commands = amout_used_commands[0] # Get the biggest value

	try:
		return jinja.render('index.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], bot_stats=[len(client.guilds), len(client.users), amout_used_commands])
	except:
		return jinja.render('index.html', request, url=Utils().DISCORD_LOGIN_URI, bot_stats=[len(client.guilds), len(client.users), amout_used_commands])


@bp.route('/servers')
async def servers(request):
	code = request.args.get('code') # Get code from url
	access_token = Utils().get_access_token(code) # Get an user access token 

	if code: # If code is not None, it redirects to the servers page

		# Work with session
		request.ctx.session['access_token'] = access_token
		request.ctx.session['user_state_login'] = True
		return response.redirect('/servers')

	access_token = request.ctx.session['access_token']
	user_datas = Utils().get_user_data(access_token)

	# If length of username the biggest than 16, it is shorting the username and it is unating a username and disciminator 
	if len(user_datas[0]['username']) > 16:
		user_name = user_datas[0]['username'][:14]+'...#'+user_datas[0]['discriminator']
	else:
		user_name = user_datas[0]['username']+'#'+user_datas[0]['discriminator']

	user_hash_avatar = user_datas[0]['avatar']
	user_id = user_datas[0]['id']

	# Check if user has not default avatar
	if user_hash_avatar:

		# Check if useravatar is animated
		if user_hash_avatar.startswith('a_'):
			user_avatar = f'https://cdn.discordapp.com/avatars/{user_id}/{user_hash_avatar}.gif'
		else:
			user_avatar = f'https://cdn.discordapp.com/avatars/{user_id}/{user_hash_avatar}.png'
	else:
		user_avatar = 'https://cdn.discordapp.com/attachments/717783820308316272/743448353672790136/1.png'

	# Write the user data to session
	request.ctx.session['user_name'] = user_name
	request.ctx.session['user_avatar'] = user_avatar

	datas = []
	session_guild_datas = {}
	guilds = [str(guild.id) for guild in client.guilds] # Get the id client guilds in format string

	try:

		# Check if the user has more permissions on guild and check if bot on this guild
		for guild in user_datas[1]:
			bot = False
			guild_id = guild['id']
			guild_icon = guild['icon']
			guild_perms = guild['permissions']
			guild_perms |= guild['permissions']
			guild_name = guild['name']
			if len(guild_name) > 14:
				guild_name = guild_name[:14]+'...'
			
			# Check the user permissions on guild
			if guild_perms & 0x20 == 0x20:
				manage_server = True
			else:
				manage_server = False  

			# Check if bot on the guild
			if str(guild_id) in guilds:
				bot = True

			# Add guild data to variable datas
			if not guild_icon and manage_server:
				datas.append(['https://cdn.discordapp.com/attachments/717783820308316272/743448353672790136/1.png', bot, guild_name, guild_id])
				session_guild_datas.update({guild['id']: ['https://cdn.discordapp.com/attachments/717783820308316272/743448353672790136/1.png', guild['name']]})
			elif guild_icon and manage_server: 
				session_guild_datas.update({guild['id']: [f'https://cdn.discordapp.com/icons/{guild_id}/{guild_icon}.png', guild['name']]})
				datas.append([f'https://cdn.discordapp.com/icons/{guild_id}/{guild_icon}.png', bot, guild_name, guild_id])
	except:
		pass
	
	if 'user_guilds' in request.ctx.session:
		if request.ctx.session['user_guilds'] != session_guild_datas:
			request.ctx.session['user_guilds'] = session_guild_datas
	else:
		request.ctx.session['user_guilds'] = session_guild_datas

	return jinja.render('servers.html', request, url=Utils().DISCORD_LOGIN_URI, datas=datas, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'])


@bp.route('/dashboard/<int:guild_id>', methods=['POST', 'GET'])
async def dashboard(request, guild_id):

	# Check if user is logging 
	if not request.ctx.session['user_state_login']:
		return response.redirect(Utils().DISCORD_LOGIN_URI)

	# Get the guilds, roles and channels
	datas_guild = Utils().get_guild_channel_roles(guild_id)
	guilds = request.ctx.session['user_guilds']
	guild_data = Utils().get_db_guild_data(guild_id)
	new_idea_channel = 0
	
	if request.method == 'POST':

		# Check if prefix is incorect introduced
		if len(request.form['new_prefix']) < 1:
			return jinja.render( url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='global', alert=['danger', 'Укажите префикс'])
		elif len(request.form['new_prefix']) > 3:
			return jinja.render(url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='global', alert=['danger', 'Префикс должен быть меньше 4 символов'])
		else:
			new_prefix = request.form['new_prefix']

		# Purge commands setting
		if request.form['clear_commands'] == '\xa0Выключена':
			new_purge = 0
		elif request.form['clear_commands'] == '\xa0Включена':
			new_purge = 1
		else:
			return request.form['clear_commands']
		
		# Idea channel setting
		if 'idea_channel' in request.form:
			for channel in datas_guild[0]:
				if '\xa0'+channel['name'] == request.form['idea_channel']:
					new_idea_channel = int(channel['id'])
		else:
			new_idea_channel = guild_data['idea_channel']

		# Check if user delete react channel
		if 'react_channels_remove' in request.form:
			for item in request.form.getlist("react_channels_remove"):
				react_channels = guild_data['react_channels']
				for channel in datas_guild[0]:
					if channel['name'] == item:
						try:
							react_channels.remove(channel['id'])
						except:
							pass
		else:
			react_channels = guild_data['react_channels']

		# Check if user add react channel
		if 'react_channel' in request.form:
			for channel in datas_guild[0]:
				if '\xa0'+channel['name'] == request.form['react_channel']:
					react_channels = list(guild_data['react_channels'])
					react_channels.append(int(channel['id']))
		else:
			react_channels = guild_data['react_channels']

		sql = ("""UPDATE guilds SET prefix = %s, `purge` = %s, idea_channel = %s, react_channels = %s WHERE guild_id = %s""")
		val = (str(new_prefix), int(new_purge), int(new_idea_channel), json.dumps(list(react_channels)), int(guild_id))
		
		cursor.execute(sql, val) # Database query
		conn.commit()
		
	guild_data = Utils().get_db_guild_data(guild_id)
	return jinja.render('dashboard.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='global')


@bp.route('/dashboard/<int:guild_id>/moderation')
async def dashboard_moderation(request, guild_id):

	# Check if user is logging 
	if not request.ctx.session['user_state_login']:
		return response.redirect(Utils().DISCORD_LOGIN_URI)

	guild_data = Utils().get_db_guild_data(guild_id)
	datas_guild = Utils().get_guild_channel_roles(guild_id)
	guilds = request.ctx.session['user_guilds']

	return jinja.render('dashboard.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='moderation')


@bp.route('/dashboard/<int:guild_id>/economy')
async def dashboard_economy(request, guild_id):

	# Check if user is logging 
	if not request.ctx.session['user_state_login']:
		return response.redirect(Utils().DISCORD_LOGIN_URI)

	guild_data = Utils().get_db_guild_data(guild_id)
	datas_guild = Utils().get_guild_channel_roles(guild_id)
	guilds = request.ctx.session['user_guilds']

	return jinja.render('dashboard.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='economy')


@bp.route('/dashboard/<int:guild_id>/levels')
async def dashboard_levels(request, guild_id):

	# Check if user is logging 
	if not request.ctx.session['user_state_login']:
		return response.redirect(Utils().DISCORD_LOGIN_URI)

	guild_data = Utils().get_db_guild_data(guild_id)
	datas_guild = Utils().get_guild_channel_roles(guild_id)
	guilds = request.ctx.session['user_guilds']

	return jinja.render('dashboard.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='levels')


@bp.route('/dashboard/<int:guild_id>/welcome')
async def dashboard_welcome(request, guild_id):

	# Check if user is logging 
	if not request.ctx.session['user_state_login']:
		return response.redirect(Utils().DISCORD_LOGIN_URI)

	guild_data = Utils().get_db_guild_data(guild_id)
	datas_guild = Utils().get_guild_channel_roles(guild_id)
	guilds = request.ctx.session['user_guilds']

	return jinja.render('dashboard.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='welcome')


@bp.route('/dashboard/<int:guild_id>/utils')
async def dashboard_utils(request, guild_id):

	# Check if user is logging 
	if not request.ctx.session['user_state_login']:
		return response.redirect(Utils().DISCORD_LOGIN_URI)

	guild_data = Utils().get_db_guild_data(guild_id)
	datas_guild = Utils().get_guild_channel_roles(guild_id)
	guilds = request.ctx.session['user_guilds']

	return jinja.render('dashboard.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='utils')


@bp.route('/commands')
async def commands(request):		
	try:
		return jinja.render('commands.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], client=client)
	except:
		return jinja.render('commands.html', request, url=Utils().DISCORD_LOGIN_URI, client=client)


@bp.route('/profile')
async def profile(request):

	# Check if user is logging 
	if not request.ctx.session['user_state_login']:
		return response.redirect(Utils().DISCORD_LOGIN_URI)

	access_token = request.ctx.session['access_token'] # Get the user access token form request.ctx.session
	user_datas = Utils().get_user_data(access_token)

	sql_1 = ("""SELECT money FROM users WHERE user_id = %s AND user_id = %s""")
	val_1 = (user_datas[0]['id'], user_datas[0]['id'])

	cursor.execute(sql_1, val_1) # Database query
	list_money = cursor.fetchall()
	money = 0

	# Get all money from all user guilds
	all_money = [str(i[0]) for i in list_money]
	for num in all_money:
		money += int(num)

	sql_2 = ("""SELECT bio FROM global_users_data WHERE user_id = %s AND user_id = %s""")
	val_2 = (user_datas[0]['id'], user_datas[0]['id'])

	cursor.execute(sql_2, val_2) # Database query
	bio = cursor.fetchone()[0]

	return jinja.render('profile.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], user_data=[user_datas[0]['id'], len(user_datas[1]), money, bio])


@bp.route('/stats')
async def stats(request):
	channels = len([str(channel.id) for guild in client.guilds for channel in guild.channels ])

	try:
		return jinja.render('stats.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], bot_stats=[channels, len(client.guilds), len(client.users)])
	except:
		return jinja.render('stats.html', request, url=Utils().DISCORD_LOGIN_URI, bot_stats=[channels, len(client.guilds), len(client.users)])


@bp.route('/transactions')
async def transactions(request):
	
	# Check if user is logging 
	if not request.ctx.session['user_state_login']:
		return response.redirect(Utils().DISCORD_LOGIN_URI)

	access_token = request.ctx.session['access_token'] # Get the user access token form session
	user_datas = Utils().get_user_data(access_token)

	sql = ("""SELECT transantions FROM users WHERE user_id = %s AND user_id = %s""")
	val = (user_datas[0]['id'], user_datas[0]['id'])

	cursor.execute(sql, val) # Database query
	data = cursor.fetchall()
	transactions = [t for transactions in data for transaction in transactions for t in json.loads(transaction)]
	for t in transactions:
		if isinstance(t['to'], int):
			t.update({'to': client.get_user(int(t['to']))})

		if isinstance(t['from'], int):
			t.update({'from': client.get_user(int(t['from']))})
		
		guild_icon = client.get_guild(int(t['guild_id'])).icon_url
		if str(guild_icon) == '':
			guild_icon = 'https://cdn.discordapp.com/attachments/717783820308316272/743448353672790136/1.png'
		t.update({'guild_icon': guild_icon})

	return jinja.render('transactions.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], transactions=transactions)


@bp.route('/leaderboard')
async def leaderboard(request):
	cursor.execute("""SELECT money, reputation, exp, level, coins, user_id FROM users ORDER BY exp DESC LIMIT 100""") # Database query
	data = cursor.fetchall()
	users = {}

	for user in data:
		if client.get_user(int(user[5])) is not None:
			users.update({user[5]: {
										'exp': user[2], 
										'reputation': user[1], 
										'money': user[0], 
										'lvl': user[3], 
										'coins': user[4],
										'avatar': client.get_user(int(user[5])).avatar_url,
										'user': client.get_user(int(user[5])).name+client.get_user(int(user[5])).discriminator
									}
								})

	users_list = sorted(users, key=lambda user: users[user]['exp'], reverse=True)
	try:
		return jinja.render('leaderboard.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], users_data=users, users_list=users_list)
	except:
		return jinja.render('leaderboard.html', request, url=Utils().DISCORD_LOGIN_URI, users_data=users, users_list=users_list)


@bp.route('/logout')
async def logout(request):
	"""Logout function"""
	
	# Work with session
	request.ctx.session['access_token'] = None
	request.ctx.session['user_state_login'] = False
	request.ctx.session['user_name'] = None
	request.ctx.session['user_avatar'] = None
	request.ctx.session['user_guilds'] = None

	return response.redirect('/')

@bp.route('/test')
async def test(request):
	return response.json({'message': "message"})


@bp.exception(NotFound)
async def not_found_error(request, exception):
	"""Catch the 404 code error
	And return html page

	"""
	
	try:
		return jinja.render('error_404.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'])
	except:
		return jinja.render('error_404.html', request, url=Utils().DISCORD_LOGIN_URI)


@bp.exception(ServerError)
async def internal_error(request, exception):
	"""Catch the 500 code error
	And return html page

	"""
	
	try:
		return jinja.render('error_500.html', request, url=Utils().DISCORD_LOGIN_URI, avatar=request.ctx.session['user_avatar'], login=request.ctx.session['user_state_login'], user_name=request.ctx.session['user_name'], error=exception)
	except:
		return jinja.render('error_500.html', request, url=Utils().DISCORD_LOGIN_URI, error=exception)
