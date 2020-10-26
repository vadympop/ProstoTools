# Imports
import requests
import json
import os
import mysql.connector

# Create new class Utils
class Utils:
	def __init__(self):
		# Const variables
		self.conn = mysql.connector.connect(user='root', passwd=os.environ['DB_PASSWORD'], host='localhost', db='data')
		self.cursor = self.conn.cursor(buffered=True)
		self.CLIENT_ID = '700767394154414142'
		self.CLIENT_SECRET = 'DsxERoWInGaqcX1CoJQu3QfNX7pak-Yd'
		self.SCOPE = 'identify%20guilds'
		self.REDIRECT_URI = 'http://127.0.0.1:5000/servers'
		self.DISCORD_LOGIN_URI = f'https://discord.com/api/oauth2/authorize?client_id={self.CLIENT_ID}&redirect_uri={self.REDIRECT_URI}&response_type=code&scope={self.SCOPE}'
		self.DISCORD_TOKEN_URI = 'https://discord.com/api/v6/oauth2/token'
		self.DISCORD_API_URI = 'https://discord.com/api/v6'
		self.CLIENT_TOKEN = os.environ['BOT_TOKEN']

	def get_access_token(self, code):
		"""Return the access token of user
		Requires code

		"""

		payload = {
			'client_id': self.CLIENT_ID,
			'client_secret': self.CLIENT_SECRET,
			'grant_type': 'authorization_code',
			'code': code,
			'redirect_uri': self.REDIRECT_URI,
			'scope': self.SCOPE
		}
		headers = {
			'Content-Type': 'application/x-www-form-urlencoded'
		}

		access_token = requests.post(url=self.DISCORD_TOKEN_URI, data=payload, headers=headers) # Get a data from discord API
		json = access_token.json()

		return json.get('access_token')

	
	def get_user_data(self, access_token):
		"""Return an user data and user guilds
		Requires user access token 

		"""

		url = self.DISCORD_API_URI+'/users/@me'

		headers = {
			'Authorization': f'Bearer {access_token}'
		}
		user_data = requests.get(url = url, headers = headers)
		user_json = user_data.json()
		user_data_guilds = requests.get(url = url+'/guilds', headers = headers) # Get a data from discord API
		user_guilds = user_data_guilds.json()

		return [user_json, user_guilds]

	
	def get_guild_channel_roles(self, guild_id):
		"""Return a guild channels and roles
		Requires guild id

		"""

		headers = {
			'Authorization': f'Bot {self.CLIENT_TOKEN}'
		}

		guild_channels_obj = requests.get(url=self.DISCORD_API_URI+f'/guilds/{guild_id}/channels', headers=headers) # Get a data from discord API
		guild_channels = guild_channels_obj.json()
		guild_channels = sorted(guild_channels, key=lambda channel: channel['position']) # Sort a guild channels of position 

		guild_roles_obj = requests.get(url=self.DISCORD_API_URI+f'/guilds/{guild_id}/roles', headers=headers) # Get a data from discord API
		guild_roles = guild_roles_obj.json()
		guild_roles = sorted(guild_roles, key=lambda role: role['position']) # Sort a guild roles of position 
		guild_roles.reverse()

		return [guild_channels, guild_roles]


	def get_db_guild_data(self, guild_id):
		"""Return a guild settings from database
		Requires a guild id

		"""

		self.cursor.execute("""SELECT * FROM guilds WHERE guild_id = %s AND guild_id = %s""", (guild_id, guild_id))
		guild_data = self.cursor.fetchone()

		donate = guild_data[8]
		react_channels = []

		# Re-work string "bool" format in bool
		if donate == 'True':
			donate = True
		elif donate == 'False':
			donate = False

		# Int channels ids re-work in string format
		for channel in json.loads(guild_data[17]):
			react_channels.append(str(channel))

		# Create a dict with settings guild from database
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
