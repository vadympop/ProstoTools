import json

from core.services.database.models import Guild
from core.bases.cog_base import BaseCog
from discord.ext import tasks


class TasksServerStat(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.server_stat_loop.start()

	@tasks.loop(minutes=10)
	async def server_stat_loop(self):
		await self.client.wait_until_ready()
		for stat in Guild.objects.all():
			if stat.server_stats:
				for stat_type, channel_id in stat.server_stats.items():
					if stat_type != "message":
						guild = self.client.get_guild(stat.guild_id)
						if guild is not None:
							try:
								counters = {
									"members": len([member.id for member in guild.members if not member.bot]),
									"bots": len([bot.id for bot in guild.members if bot.bot]),
									"channels": len([channel.id for channel in guild.channels]),
									"roles": len([role.id for role in guild.roles]),
									"all": guild.member_count,
								}
								counter = counters[stat_type]
								channel = guild.get_channel(channel_id)
								numbers = "".join(
									char for char in channel.name if char.isdigit()
								)
								new_name = channel.name.replace(numbers, str(counter))

								await channel.edit(name=new_name)
							except:
								pass


def setup(client):
	client.add_cog(TasksServerStat(client))
