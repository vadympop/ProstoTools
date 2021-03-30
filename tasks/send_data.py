import os
import json
import logging

from core.bases.cog_base import BaseCog
from discord.ext import tasks

logger = logging.getLogger(__name__)


class TasksSendData(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.allowed_cogs = self.client.config.ALLOWED_COGS
		self.api_url = "https://api.prosto-tools.ml/v2/"
		self.sdc_api_url = "https://api.server-discord.com/v2/bots/{0}/stats"
		self.boticord_api_url = "https://boticord.top/api/stats"
		self.send_data_loop.start()
		self.send_sdc_data_loop.start()
		self.send_boticord_data_loop.start()

	@tasks.loop(hours=6)
	async def send_data_loop(self):
		await self.client.wait_until_ready()
		data = {
			"guilds": [guild.id for guild in self.client.guilds],
			"users": [user.id for user in self.client.users],
			"channels": [channel.id for channel in self.client.get_all_channels()],
			"commands": {
				"commands": [
					{
						"name": str(command),
						"description": command.description.replace("\n", "/n"),
						"usage": command.usage,
						"category": command.cog_name,
						"help": command.help.replace("\n", "/n")
						if command.help is not None
						else "Подробной информации о команде не указанно"
					}
					for command in self.client.walk_commands()
					if command.cog_name in self.allowed_cogs
				],
				"categories": [
					cog_name
					for cog_name in self.client.cogs
					if cog_name in self.allowed_cogs
				]
			}
		}
		headers = {
			"Authorization": os.getenv("API_KEY", default="")
		}

		logger.info(f"Trying to post bot stats into {self.api_url}")
		try:
			r = await self.client.http_client.post(url=self.api_url + "private/client", json=data, headers=headers)
			logger.info(f"Response of posting bot stats into {self.api_url}: {r}")
		except Exception as e:
			logger.error(f"An error occurred when posting bot stats: {repr(e)}")
		else:
			logger.info(f"Bot stats was successful posted into {self.api_url}")

	@tasks.loop(hours=6)
	async def send_sdc_data_loop(self):
		await self.client.wait_until_ready()
		if os.getenv("SDC_TOKEN") is not None:
			headers = {
				"Authorization": f"SDC {os.getenv('SDC_TOKEN')}"
			}
			data = {
				"shards": self.client.shard_count,
				"servers": len(self.client.guilds)
			}

			logger.info(f"Trying to post bot stats into {self.sdc_api_url}")
			try:
				r = await self.client.http_client.post(
					url=self.sdc_api_url.format(self.client.user.id),
					data=data,
					headers=headers
				)
				logger.info(f"Response of posting bot stats into {self.sdc_api_url}: {r}")
			except Exception as e:
				logger.error(f"An error occurred when adding ping stat: {repr(e)}")
			else:
				logger.info(f"Bot stats was successful posted into {self.sdc_api_url}")

	@tasks.loop(hours=6)
	async def send_boticord_data_loop(self):
		await self.client.wait_until_ready()
		if os.getenv("BOTICORD_TOKEN") is not None:
			headers = {
				"Authorization": os.getenv('BOTICORD_TOKEN')
			}
			data = {
				"shards": self.client.shard_count,
				"servers": len(self.client.guilds),
				"users": len(self.client.users)
			}

			logger.info(f"Trying to post bot stats into {self.boticord_api_url}")
			try:
				r = await self.client.http_client.post(
					url=self.boticord_api_url,
					json=json.dumps(data),
					headers=headers
				)
				logger.info(f"Response of posting bot stats into {self.boticord_api_url}: {r}")
			except Exception as e:
				logger.error(f"An error occurred when adding ping stat: {repr(e)}")
			else:
				logger.info(f"Bot stats was successful posted into {self.boticord_api_url}")


def setup(client):
	client.add_cog(TasksSendData(client))
