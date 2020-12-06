import requests
import os

from discord.ext import commands, tasks


class TasksSendData(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.api_url = "https://prosto-tools-api.herokuapp.com/api/"
		self.send_data_loop.start()

	@tasks.loop(hours=12)
	async def send_data_loop(self):
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
					"Works"
				)
			},
		}
		headers = {
			"token": os.getenv("BOT_TOKEN")
		}
		requests.post(url=self.api_url + "private/client", json=data, headers=headers)


def setup(client):
	client.add_cog(TasksSendData(client))
