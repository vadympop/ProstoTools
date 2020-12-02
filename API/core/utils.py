import os
from .database import Database

class Utils:
	def __init__(self):
		pass

	async def check_api_key(self, api_key: str, guild_id: int) -> bool:
		db_api_key = await Database()._get_guild_api_key(guild_id)
		if api_key != db_api_key:
			return False
		
		return True

	async def check_bot_token(self, token: str) -> bool:
		if token != os.environ["BOT_TOKEN"]:
			return False

		return True