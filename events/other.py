import os
import mysql.connector

from tools import DB
from discord.ext import commands


class EventsOther(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(
			user="root",
			password=os.getenv("DB_PASSWORD"),
			host="localhost",
			database="data",
		)
		self.cursor = self.conn.cursor(buffered=True)

	@commands.Cog.listener()
	async def on_command(self, ctx):
		DB().add_amout_command(entity=ctx.command.name)

		self.cursor.execute(
			"""UPDATE users SET num_commands = num_commands + 1 WHERE user_id = %s AND guild_id = %s""",
			(ctx.author.id, ctx.guild.id),
		)
		self.conn.commit()


def setup(client):
	client.add_cog(EventsOther(client))
