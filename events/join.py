import discord

from tools import DB

from discord.ext import commands
from configs import configs


class EventsJoin(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.HELP_SERVER = configs["HELP_SERVER"]

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		emb = discord.Embed(
			title="Спасибо за приглашения нашего бота! Мы вам всегда рады",
			description=f"**Стандартний префикс - *, команда помощи - *help, \nкоманда настроёк - *settings. Наш сервер поддержки: \n {self.HELP_SERVER}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(
			text="ProstoChelovek and Mr.Kola Copyright",
			icon_url=self.client.user.avatar_url,
		)
		await guild.text_channels[0].send(embed=emb)

		DB().sel_guild(guild=guild)
		DB().add_amout_command(entity="guilds", add_counter=len(self.client.guilds))

		for member in guild.members:
			if not member.bot:
				DB().sel_user(target=member)

		guild_owner_bot = self.client.get_guild(717776571406090310)
		channel = guild_owner_bot.text_channels[3]
		invite = await guild.text_channels[0].create_invite(
			reason="For more information"
		)

		emb_info = discord.Embed(
			title=f"Бот добавлен на новый сервер, всего серверов - {len(self.client.guilds)}",
			description=f"Названия сервера - `{guild.name}`\nАйди сервера - `{guild.id}`\nИнвайт - {invite}\nВладелец - `{guild.owner}`\nКол-во участников - `{guild.member_count}`",
		)
		emb_info.set_thumbnail(url=guild.icon_url)
		await channel.send(embed=emb_info)


def setup(client):
	client.add_cog(EventsJoin(client))
