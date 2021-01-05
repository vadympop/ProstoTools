import os
from tools.http import async_requests as requests
from discord.ext import commands, tasks


class TasksSendData(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.api_url = "http://api.prosto-tools.ml/api/"
		self.sdc_api_url = "https://api.server-discord.com/v2/bots/{0}/stats"
		self.boticord_api_url = "https://boticord.top/api/stats?servers={0}&shards={1}&users={2}"
		self.send_data_loop.start()
		self.send_sdc_data_loop.start()
		self.send_boticord_data_loop.start()

	@tasks.loop(hours=12)
	async def send_data_loop(self):
		if len(self.client.guilds) > 0:
			data = {
				"guilds": [guild.id for guild in self.client.guilds],
				"users": [user.id for user in self.client.users],
				"channels": [channel.id for channel in self.client.get_all_channels()],
				"commands": {
					cog_name: {
						command.name: {
							"description": command.description,
							"usage": command.usage
						}
						for command in self.client.get_cog(cog_name).get_commands()
					}
					for cog_name in self.client.cogs if cog_name in (
						"Clans",
						"Different",
						"Economy",
						"Games",
						"Moderate",
						"Settings",
						"Utils",
						"Works",
						"FunOther",
						"FunEditImage",
						"FunRandomImage"
					)
				},
			}
			headers = {
				"Authorization": os.getenv("BOT_TOKEN")
			}
			await requests.post(url=self.api_url + "private/client", json=data, headers=headers)

	@tasks.loop(hours=12)
	async def send_sdc_data_loop(self):
		if len(self.client.guilds) > 0:
			if os.getenv("SDC_TOKEN") is not None:
				headers = {
					"Authorization": f"SDC {os.getenv('SDC_TOKEN')}"
				}
				data = {
					"shards": self.client.shard_count,
					"servers": len(self.client.guilds)
				}
				await requests.post(url=self.sdc_api_url.format(self.client.user.id), data=data, headers=headers)

	@tasks.loop(hours=12)
	async def send_boticord_data_loop(self):
		if len(self.client.guilds) > 0:
			if os.getenv("BOTICORD_TOKEN") is not None:
				headers = {
					"Authorization": os.getenv('BOTICORD_TOKEN')
				}
				resp = await requests.get(url=self.boticord_api_url.format(
					len(self.client.guilds),
					self.client.shard_count,
					len(self.client.users)
				), headers=headers)


def setup(client):
	client.add_cog(TasksSendData(client))
