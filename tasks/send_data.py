import os
import json
from tools.http import async_requests as requests
from discord.ext import commands, tasks


class TasksSendData(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.api_url = "https://api.prosto-tools.ml/api/"
		self.sdc_api_url = "https://api.server-discord.com/v2/bots/{0}/stats"
		self.boticord_api_url = "https://boticord.top/api/stats"
		self.send_data_loop.start()
		self.send_sdc_data_loop.start()
		self.send_boticord_data_loop.start()

	@tasks.loop(hours=6)
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

	@tasks.loop(hours=6)
	async def send_sdc_data_loop(self):
		print(len(self.client.guilds))
		if len(self.client.guilds) > 0:
			print("Send to SDC")
			if os.getenv("SDC_TOKEN") is not None:
				headers = {
					"Authorization": f"SDC {os.getenv('SDC_TOKEN')}"
				}
				data = {
					"shards": self.client.shard_count,
					"servers": len(self.client.guilds)
				}
				await requests.post(url=self.sdc_api_url.format(self.client.user.id), data=data, headers=headers)

	@tasks.loop(hours=6)
	async def send_boticord_data_loop(self):
		print(len(self.client.guilds))
		if len(self.client.guilds) > 0:
			print("Send to Boticord")
			if os.getenv("BOTICORD_TOKEN") is not None:
				headers = {
					"Authorization": os.getenv('BOTICORD_TOKEN')
				}
				data = {
					"shards": self.client.shard_count,
					"servers": len(self.client.guilds),
					"users": len(self.client.users)
				}
				resp = await requests.post(url=self.boticord_api_url, json=json.dumps(data), headers=headers)
				print(resp.status)


def setup(client):
	client.add_cog(TasksSendData(client))
