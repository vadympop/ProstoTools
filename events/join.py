import discord
from discord.ext import commands


class EventsJoin(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.HELP_SERVER = self.client.config.HELP_SERVER

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		emb = discord.Embed(
			title="Спасибо за приглашения нашего бота! Мы вам всегда рады",
			description=f"Стандартний префикс - `p.`, команда помощи - p.help, \nкоманда настроёк - p.settings. \n Полезные ссылки:\n[Наш сервер поддержки]({self.HELP_SERVER})\n[Patreon](https://www.patreon.com/join/prostotools)\n[API](https://api.prosto-tools.ml/)\n[Документация](https://vythonlui.gitbook.io/prostotools/)",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(
			text="Vython.lui Copyright",
			icon_url=self.client.user.avatar_url,
		)
		for channel in guild.text_channels:
			if channel.permissions_for(guild.me).send_messages:
				await channel.send(embed=emb)
				break

		await self.client.database.sel_guild(guild=guild)
		await self.client.database.add_amout_command(entity="guilds", add_counter=len(self.client.guilds))

		for member in guild.members:
			if not member.bot:
				await self.client.database.sel_user(target=member)

		guild_owner_bot = self.client.get_guild(717776571406090310)
		channel = guild_owner_bot.text_channels[3]
		emb_info = discord.Embed(
			title=f"Бот добавлен на новый сервер, всего серверов - {len(self.client.guilds)}",
			description=f"Названия сервера - `{guild.name}`\nАйди сервера - `{guild.id}`\nВладелец - `{guild.owner}`\nКол-во участников - `{guild.member_count}`",
		)
		emb_info.set_thumbnail(url=guild.icon_url)
		await channel.send(embed=emb_info)


def setup(client):
	client.add_cog(EventsJoin(client))
