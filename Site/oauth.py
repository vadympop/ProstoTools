import requests
import json
import os
import mysql.connector

class oAuth:
	client_id = '700767394154414142'
	client_secret = 'DsxERoWInGaqcX1CoJQu3QfNX7pak-Yd'
	scope = 'identify%20guilds'
	redirect_uri = 'http://127.0.0.1:5000/servers'
	discord_login_uri = f'https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}'
	discord_token_url = 'https://discord.com/api/v6/oauth2/token'
	discord_api_url = 'https://discord.com/api/v6'
	client_token = os.environ['BOT_TOKEN']

	@staticmethod
	def get_access_token(code):
		payload = {
			'client_id': oAuth.client_id,
			'client_secret': oAuth.client_secret,
			'grant_type': 'authorization_code',
			'code': code,
			'redirect_uri': oAuth.redirect_uri,
			'scope': oAuth.scope
		}
		headers = {
			'Content-Type': 'application/x-www-form-urlencoded'
		}

		access_token = requests.post(url = oAuth.discord_token_url, data = payload, headers = headers)
		json = access_token.json()

		return json.get('access_token')

	
	@staticmethod
	def get_user_data(access_token):
		url = oAuth.discord_api_url+'/users/@me'

		headers = {
			'Authorization': f'Bearer {access_token}'
		}
		user_data = requests.get(url = url, headers = headers)
		user_json = user_data.json()
		user_data_guilds = requests.get(url = url+'/guilds', headers = headers)
		user_guilds = user_data_guilds.json()

		return [user_json, user_guilds]

	
	@staticmethod
	def get_guild_channel_roles(guild_id):
		headers = {
			'Authorization': f'Bot {oAuth.client_token}'
		}

		guild_channels_obj = requests.get(url=oAuth.discord_api_url+f'/guilds/{guild_id}/channels', headers=headers)
		guild_channels = guild_channels_obj.json()
		guild_channels = sorted(guild_channels, key=lambda channel: channel['position'])

		guild_roles_obj = requests.get(url=oAuth.discord_api_url+f'/guilds/{guild_id}/roles', headers=headers)
		guild_roles = guild_roles_obj.json()
		guild_roles = sorted(guild_roles, key=lambda role: role['position'])
		guild_roles.reverse()

		return [guild_channels, guild_roles]


	@staticmethod
	def get_db_guild_data(guild_id):
		conn = mysql.connector.connect(user = 'root', password = '9fr8-PkM;M4+', host = 'localhost', database = 'data')
		cursor = conn.cursor(buffered = True)

		cursor.execute("""SELECT * FROM guilds WHERE guild_id = %s AND guild_id = %s""", (guild_id, guild_id))
		guild_data = cursor.fetchone()

		donate = guild_data[8]
		react_channels = []
		if donate == 'True':
			donate = True
		elif donate == 'False':
			donate = False

		for channel in json.loads(guild_data[17]):
			react_channels.append(str(channel))

		dict_guild_data = {
			'guild_id': int(guild_data[0]),
			'purge': int(guild_data[1]),
			'all_message': int(guild_data[2]),
			'textchannels_category': int(guild_data[3]),
			'max_warns': int(guild_data[4]),
			'exp_multi': float(guild_data[5]),
			'idea_channel': str(guild_data[6]),
			'timedelete_textchannel': int(guild_data[7]),
			'donate': donate,
			'prefix': str(guild_data[9]),
			'server_stats': json.loads(guild_data[10]),
			'voice_channel': json.loads(guild_data[11]),
			'shop_list': json.loads(guild_data[12]),
			'ignored_channels': json.loads(guild_data[13]),
			'auto_mod': json.loads(guild_data[14]),
			'clans': json.loads(guild_data[15]),
			'moder_roles': json.loads(guild_data[16]),
			'react_channels': set(react_channels),
			'welcome': json.loads(guild_data[18])
		}

		return dict_guild_data


