# Imports
import datetime
import json
import mysql.connector
import requests

from Site.config import Config
from Site.utils import Utils
from Site import app, cursor, conn, utils
from flask import render_template, redirect, request, url_for, session

utils = Utils()

@app.before_request
def make_session_permanent():
	session.permanent = True
	app.permanent_session_lifetime = datetime.timedelta(days=365)


def site_run(client):
	"""Needs for start flask app in a bot start file and sending bot object to the site
	Requires a bot object

	"""

	@app.route('/')
	def index():
		cursor.execute("""SELECT count FROM bot_stats WHERE entity = 'all commands'""") # Database query
		amout_used_commands = cursor.fetchall()
		amout_used_commands.reverse()
		amout_used_commands = amout_used_commands[0] # Get the biggest value

		try:
			return render_template('index.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], bot_stats=[len(client.guilds), len(client.users), amout_used_commands])
		except:
			return render_template('index.html', url=utils.DISCORD_LOGIN_URI, bot_stats=[len(client.guilds), len(client.users), amout_used_commands])


	@app.route('/servers')
	def servers():
		code = request.args.get('code') # Get code from url
		access_token = utils.get_access_token(code) # Get an user access token 

		if code: # If code is not None, it redirects to the servers page

			# Work with session
			session['access_token'] = access_token
			session['user_state_login'] = True
			return redirect('/servers')

		access_token = session['access_token']
		user_datas = utils.get_user_data(access_token)

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
		session['user_name'] = user_name
		session['user_avatar'] = user_avatar

		datas = []
		session_guild_datas = {}
		guilds = ' '.join(str(guild.id) for guild in client.guilds).split() # Get the user guilds

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
		
		if 'user_guilds' in session:
			if session['user_guilds'] != session_guild_datas:
				session['user_guilds'] = session_guild_datas
		else:
			session['user_guilds'] = session_guild_datas

		return render_template('servers.html', url=utils.DISCORD_LOGIN_URI, datas=datas, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'])


	@app.route('/dashboard/<int:guild_id>', methods=['POST', 'GET'])
	def dashboard(guild_id):

		# Check if user is logging 
		if not session['user_state_login']:
			return redirect(utils.DISCORD_LOGIN_URI)

		# Get the guilds, roles and channels
		datas_guild = utils.get_guild_channel_roles(guild_id)
		guilds = session['user_guilds']
		guild_data = utils.get_db_guild_data(guild_id)
		new_idea_channel = 0
		
		if request.method == 'POST':

			# Check if prefix is incorect introduced
			if len(request.form['new_prefix']) < 1:
				return render_template('dashboard.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='global', alert=['danger', 'Укажите префикс'])
			elif len(request.form['new_prefix']) > 3:
				return render_template('dashboard.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='global', alert=['danger', 'Префикс должен быть меньше 4 символов'])
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
			
		guild_data = utils.get_db_guild_data(guild_id)
		return render_template('dashboard.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='global')


	@app.route('/dashboard/<int:guild_id>/moderation')
	def dashboard_moderation(guild_id):

		# Check if user is logging 
		if not session['user_state_login']:
			return redirect(utils.DISCORD_LOGIN_URI)

		guild_data = utils.get_db_guild_data(guild_id)
		datas_guild = utils.get_guild_channel_roles(guild_id)
		guilds = session['user_guilds']

		return render_template('dashboard.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='moderation')


	@app.route('/dashboard/<int:guild_id>/economy')
	def dashboard_economy(guild_id):

		# Check if user is logging 
		if not session['user_state_login']:
			return redirect(utils.DISCORD_LOGIN_URI)

		guild_data = utils.get_db_guild_data(guild_id)
		datas_guild = utils.get_guild_channel_roles(guild_id)
		guilds = session['user_guilds']

		return render_template('dashboard.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='economy')


	@app.route('/dashboard/<int:guild_id>/levels')
	def dashboard_levels(guild_id):

		# Check if user is logging 
		if not session['user_state_login']:
			return redirect(utils.DISCORD_LOGIN_URI)

		guild_data = utils.get_db_guild_data(guild_id)
		datas_guild = utils.get_guild_channel_roles(guild_id)
		guilds = session['user_guilds']

		return render_template('dashboard.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='levels')


	@app.route('/dashboard/<int:guild_id>/welcome')
	def dashboard_welcome(guild_id):

		# Check if user is logging 
		if not session['user_state_login']:
			return redirect(utils.DISCORD_LOGIN_URI)

		guild_data = utils.get_db_guild_data(guild_id)
		datas_guild = utils.get_guild_channel_roles(guild_id)
		guilds = session['user_guilds']

		return render_template('dashboard.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='welcome')


	@app.route('/dashboard/<int:guild_id>/utils')
	def dashboard_utils(guild_id):

		# Check if user is logging 
		if not session['user_state_login']:
			return redirect(utils.DISCORD_LOGIN_URI)

		guild_data = utils.get_db_guild_data(guild_id)
		datas_guild = utils.get_guild_channel_roles(guild_id)
		guilds = session['user_guilds']

		return render_template('dashboard.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='utils')


	@app.route('/commands')
	def commands():		
		try:
			return render_template('commands.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], client=client)
		except:
			return render_template('commands.html', url=utils.DISCORD_LOGIN_URI, client=client)


	@app.route('/profile')
	def profile():

		# Check if user is logging 
		if not session['user_state_login']:
			return redirect(utils.DISCORD_LOGIN_URI)

		access_token = session['access_token'] # Get the user access token form session
		user_datas = utils.get_user_data(access_token)

		sql_1 = ("""SELECT money FROM users WHERE user_id = %s AND user_id = %s""")
		val_1 = (user_datas[0]['id'], user_datas[0]['id'])

		cursor.execute(sql_1, val_1) # Database query
		list_money = cursor.fetchall()
		money = 0

		# Get all money from all user guilds
		all_money = ' '.join(str(i[0]) for i in list_money).split(' ')
		for num in all_money:
			money += int(num)

		sql_2 = ("""SELECT bio FROM global_users_data WHERE user_id = %s AND user_id = %s""")
		val_2 = (user_datas[0]['id'], user_datas[0]['id'])

		cursor.execute(sql_2, val_2) # Database query
		bio = cursor.fetchone()[0]

		try:
			return render_template('profile.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], user_data=[user_datas[0]['id'], len(user_datas[1]), money, bio])
		except:
			return render_template('profile.html', url=utils.DISCORD_LOGIN_URI)


	@app.route('/stats')
	def stats():
		channels = len([str(channel.id) for guild in client.guilds for channel in guild.channels ])

		try:
			return render_template('stats.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], bot_stats=[channels, len(client.guilds), len(client.users)])
		except:
			return render_template('stats.html', url=utils.DISCORD_LOGIN_URI, bot_stats=[channels, len(client.guilds), len(client.users)])


	@app.route('/logout')
	def logout():
		"""Logout function"""
		
		# Work with session
		session.pop('access_token', None)
		session['user_state_login'] = False
		session.pop('user_name', None)
		session.pop('user_avatar', None)
		session.pop('user_guilds', None)

		return redirect('/')


	@app.errorhandler(404)
	def not_found_error(error):
		"""Catch the 404 code error
		And return html page

		"""
		
		try:
			return render_template('error_404.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name']), 404
		except:
			return render_template('error_404.html', url=utils.DISCORD_LOGIN_URI), 404


	@app.errorhandler(500)
	def internal_error(error):
		"""Catch the 500 code error
		And return html page

		"""
		
		try:
			return render_template('error_500.html', url=utils.DISCORD_LOGIN_URI, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], error=error), 500
		except:
			return render_template('error_500.html', url=utils.DISCORD_LOGIN_URI, error=error), 500

	# Run the flask app
	app.run()