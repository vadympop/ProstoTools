from flask import Flask, render_template, redirect, request, url_for, make_response, session
from flask_socketio import SocketIO
from Site.oauth import oAuth
import datetime
import json
import mysql.connector
import requests

app = Flask(__name__)
app.secret_key = 'jjpEHeewQQRBaVSrKZZ4R32Y-$hhP9$*&k?ZN766@5_&TJDwMgNajELZ%Vu+'
conn = mysql.connector.connect(user = 'root', password = '9fr8-PkM;M4+', host = 'localhost', database = 'data')
cursor = conn.cursor(buffered = True)


def site_run(client):

	@app.before_request
	def make_session_permanent():
		session.permanent = True
		app.permanent_session_lifetime = datetime.timedelta(days=365)


	@app.route('/')
	def index():
		cursor.execute("""SELECT used_commands FROM bot_stats WHERE entity = 'all commands'""")
		amout_used_commands = cursor.fetchall()
		amout_used_commands.reverse()
		amout_used_commands = amout_used_commands[0]
		try:
			return render_template('index.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], bot_stats=[len(client.guilds), len(client.users), amout_used_commands])
		except:
			return render_template('index.html', url=oAuth.discord_login_uri, bot_stats=[len(client.guilds), len(client.users), amout_used_commands])


	@app.route('/servers')
	def servers():
		code = request.args.get('code')
		access_token = oAuth.get_access_token(code)

		if code:
			session['access_token'] = access_token
			session['user_state_login'] = True
			return redirect('/servers')

		access_token = session['access_token']
		user_datas = oAuth.get_user_data(access_token)

		if len(user_datas[0]['username']) > 16:
			user_name = user_datas[0]['username'][:14]+'...#'+user_datas[0]['discriminator']
		else:
			user_name = user_datas[0]['username']+'#'+user_datas[0]['discriminator']

		user_hash_avatar = user_datas[0]['avatar']
		user_id = user_datas[0]['id']
		if user_hash_avatar:
			user_avatar = f'https://cdn.discordapp.com/avatars/{user_id}/{user_hash_avatar}.gif'
		else:
			user_avatar = 'https://cdn.discordapp.com/attachments/717783820308316272/743448353672790136/1.png'

		session['user_name'] = user_name
		session['user_avatar'] = user_avatar

		datas = []
		session_guild_datas = {}
		guilds = ' '.join(str(guild.id) for guild in client.guilds).split()

		try:
			for guild in user_datas[1]:
				bot = False
				guild_id = guild['id']
				guild_icon = guild['icon']
				guild_perms = guild['permissions']
				guild_perms |= guild['permissions']
				guild_name = guild['name']
				if len(guild_name) > 14:
					guild_name = guild_name[:14]+'...'
				
				if guild_perms & 0x20 == 0x20:
					manage_server = True
				else:
					manage_server = False  

				if str(guild_id) in guilds:
					bot = True

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

		return render_template('servers.html', url=oAuth.discord_login_uri, datas=datas, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'])


	@app.route('/dashboard/<int:guild_id>', methods=['POST', 'GET'])
	def dashboard(guild_id):
		datas_guild = oAuth.get_guild_channel_roles(guild_id)
		guilds = session['user_guilds']
		guild_data = oAuth.get_db_guild_data(guild_id)
		new_idea_channel = 0

		if request.method == 'POST':
			if len(request.form['new_prefix']) < 1:
				return render_template('dashboard.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='global', alert=['danger', 'Укажите префикс'])
			elif len(request.form['new_prefix']) > 3:
				return render_template('dashboard.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='global', alert=['danger', 'Префикс должен быть меньше 4 символов'])
			else:
				new_prefix = request.form['new_prefix']

			if request.form['clear_commands'] == '\xa0Выключена':
				new_purge = 0
			elif request.form['clear_commands'] == '\xa0Включена':
				new_purge = 1
			else:
				return request.form['clear_commands']

			if 'idea_channel' in request.form:
				for channel in datas_guild[0]:
					if '\xa0'+channel['name'] == request.form['idea_channel']:
						new_idea_channel = int(channel['id'])
			else:
				new_idea_channel = guild_data['idea_channel']

			if 'server_stats_remove' in request.form:
				for item in request.form.getlist("server_stats_remove"):
					server_stats = guild_data['server_stats']
					try:
						server_stats.pop(item)
					except:
						pass
			else:
				server_stats = guild_data['server_stats']

			if 'server_stats' in request.form:
				stats_dict = {
					'\xa0Все': 'all',
					'\xa0Только боты': 'bots',
					'\xa0Только люди': 'members',
					'\xa0Каналы': 'channels',
					'\xa0Роли': 'roles'
				}
				server_stats = guild_data['server_stats']
				server_stats.update({stats_dict[request.form['server_stats']]: 0})
			else:
				server_stats = guild_data['server_stats']

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

			if 'react_channel' in request.form:
				for channel in datas_guild[0]:
					if '\xa0'+channel['name'] == request.form['react_channel']:
						react_channels = list(guild_data['react_channels'])
						react_channels.append(int(channel['id']))
			else:
				react_channels = guild_data['react_channels']

			sql = ("""UPDATE guilds SET prefix = %s, `purge` = %s, idea_channel = %s, server_stats = %s, react_channels = %s WHERE guild_id = %s""")
			val = (str(new_prefix), int(new_purge), int(new_idea_channel), json.dumps(server_stats), json.dumps(list(react_channels)), int(guild_id))
			
			cursor.execute(sql, val)
			conn.commit()
			
		guild_data = oAuth.get_db_guild_data(guild_id)
		return render_template('dashboard.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='global')


	@app.route('/dashboard/<int:guild_id>/moderation')
	def dashboard_moderation(guild_id):
		guild_data = oAuth.get_db_guild_data(guild_id)
		datas_guild = oAuth.get_guild_channel_roles(guild_id)
		guilds = session['user_guilds']

		return render_template('dashboard.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='moderation')


	@app.route('/dashboard/<int:guild_id>/economy')
	def dashboard_economy(guild_id):
		guild_data = oAuth.get_db_guild_data(guild_id)
		datas_guild = oAuth.get_guild_channel_roles(guild_id)
		guilds = session['user_guilds']

		return render_template('dashboard.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='economy')


	@app.route('/dashboard/<int:guild_id>/levels')
	def dashboard_levels(guild_id):
		guild_data = oAuth.get_db_guild_data(guild_id)
		datas_guild = oAuth.get_guild_channel_roles(guild_id)
		guilds = session['user_guilds']

		return render_template('dashboard.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='levels')


	@app.route('/dashboard/<int:guild_id>/welcome')
	def dashboard_welcome(guild_id):
		guild_data = oAuth.get_db_guild_data(guild_id)
		datas_guild = oAuth.get_guild_channel_roles(guild_id)
		guilds = session['user_guilds']

		return render_template('dashboard.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='welcome')

	@app.route('/dashboard/<int:guild_id>/utils')
	def dashboard_utils(guild_id):
		guild_data = oAuth.get_db_guild_data(guild_id)
		datas_guild = oAuth.get_guild_channel_roles(guild_id)
		guilds = session['user_guilds']

		return render_template('dashboard.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], guild_data=[[guild_id, guilds[str(guild_id)][0], guilds[str(guild_id)][1]], guild_data, datas_guild], category='utils')


	@app.route('/commands')
	def commands():
		try:
			return render_template('commands.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], client=client)
		except:
			return render_template('commands.html', url=oAuth.discord_login_uri, client=client)


	@app.route('/profile')
	def profile():
		access_token = session['access_token']
		user_datas = oAuth.get_user_data(access_token)

		sql = ("""SELECT money FROM users WHERE user_id = %s AND user_id = %s""")
		val = (user_datas[0]['id'], user_datas[0]['id'])

		cursor.execute(sql, val)
		list_money = cursor.fetchall()
		money = 0
		all_money = ' '.join(str(i[0]) for i in list_money).split(' ')
		for num in all_money:
			money += int(num)

		try:
			return render_template('profile.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], user_data=[user_datas[0]['id'], len(user_datas[1]), money])
		except:
			return render_template('profile.html', url=oAuth.discord_login_uri)


	@app.route('/stats')
	def stats():
		try:
			return render_template('stats.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'])
		except:
			return render_template('stats.html', url=oAuth.discord_login_uri)


	@app.route('/logout')
	def logout():
		session.pop('access_token', None)
		session['user_state_login'] = False
		session.pop('user_name', None)
		session.pop('user_avatar', None)
		session.pop('user_guilds', None)

		return redirect('/')

	
	@app.errorhandler(404)
	def not_found_error(error):
		try:
			return render_template('error_404.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name']), 404
		except:
			return render_template('error_404.html', url=oAuth.discord_login_uri), 404

	@app.errorhandler(500)
	def internal_error(error):
		try:
			return render_template('error_500.html', url=oAuth.discord_login_uri, avatar=session['user_avatar'], login=session['user_state_login'], user_name=session['user_name'], error=error), 500
		except:
			return render_template('error_500.html', url=oAuth.discord_login_uri, error=error), 500

	app.run()

