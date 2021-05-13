import discord
import jinja2

from core.bases.cog_base import BaseCog
from discord.ext import commands


class EventsJoin(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.HELP_SERVER = self.client.config.HELP_SERVER

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		await self.client.database.add_stat_counter(entity="users", add_counter=len(self.client.users))
		await self.client.database.add_stat_counter(entity="guilds", add_counter=len(self.client.guilds))

		emb = discord.Embed(
			title="Спасибо за приглашения нашего бота! Мы вам всегда рады",
			description=f"Стандартний префикс - `p.`, команда помощи - p.help, \nкоманда настроёк - p.setting. \n Полезные ссылки:\n[Наш сервер поддержки]({self.HELP_SERVER})\n[Patreon](https://www.patreon.com/join/prostotools)\n[API](https://api.prosto-tools.ml/)\n[Документация](https://vythonlui.gitbook.io/prostotools/)",
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
		for member in guild.members:
			if not member.bot:
				await self.client.database.sel_user(target=member)

		emb_info = discord.Embed(
			title=f"Бот добавлен на новый сервер, всего серверов - {len(self.client.guilds)}",
			colour=discord.Color.green(),
			description=f"Названия сервера - `{guild.name}`\nАйди сервера - `{guild.id}`\nВладелец - `{guild.owner}`\nКол-во участников - `{guild.member_count}`",
		)
		emb_info.set_thumbnail(url=guild.icon_url)
		await self.client.get_guild(717776571406090310).get_channel(737685906873647165).send(embed=emb_info)

	@commands.Cog.listener()
	async def on_member_join(self, member):
		await self.client.database.add_stat_counter(entity="users", add_counter=len(self.client.users))

		guild_data = await self.client.database.sel_guild(guild=member.guild)
		if not member.bot:
			if guild_data.audit["member_join"]["state"]:
				e = discord.Embed(
					description=f"Пользователь `{member}` присоединился",
					colour=discord.Color.green(),
					timestamp=await self.client.utils.get_guild_time(member.guild)
				)
				e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
				e.set_author(
					name="Журнал аудита | Новый пользователь", icon_url=member.avatar_url
				)
				e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				channel = member.guild.get_channel(guild_data.audit["member_join"]["channel_id"])
				if channel is not None:
					await channel.send(embed=e)

				if guild_data.donate:
					await self.client.database.add_audit_log(
						user=member,
						channel=channel,
						guild_id=member.guild.id,
						action_type="member_join",
					)
		else:
			if guild_data.audit["bot_join"]["state"]:
				e = discord.Embed(
					description=f"Бот `{member}` присоединился",
					colour=discord.Color.light_grey(),
					timestamp=await self.client.utils.get_guild_time(member.guild)
				)
				e.add_field(name="Id Бота", value=f"`{member.id}`", inline=False)
				e.set_author(
					name="Журнал аудита | Новый бот", icon_url=member.avatar_url
				)
				e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				channel = member.guild.get_channel(guild_data.audit["bot_join"]["channel_id"])
				if channel is not None:
					await channel.send(embed=e)

				if guild_data.donate:
					await self.client.database.add_audit_log(
						user=member,
						channel=channel,
						guild_id=member.guild.id,
						action_type="bot_join",
					)
				return

		if not guild_data.welcomer["join"]["state"]:
			return

		try:
			try:
				if guild_data.welcomer["join"]["type"] == "dm":
					await member.send(
						await self.client.template_engine.render(
							member=member,
							render_text=guild_data.welcomer["join"]["message"]
						)
					)
				elif guild_data.welcomer["join"]["type"] == "channel":
					channel = member.guild.get_channel(guild_data.welcomer["join"]["channel_id"])
					if channel is not None:
						await channel.send(
							await self.client.template_engine.render(
								member=member,
								render_text=guild_data.welcomer["join"]["message"]
							)
						)
			except discord.errors.HTTPException:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**Во время выполнения кастомной команды пройзошла ошибка неизвестная ошибка!**",
					colour=discord.Color.red(),
				)
				emb.set_author(name=member.name, icon_url=member.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await member.send(embed=emb)
				return
		except jinja2.exceptions.TemplateSyntaxError as e:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"Во время выполнения кастомной команды пройзошла ошибка:\n```{repr(e)}```",
				colour=discord.Color.red(),
			)
			emb.set_author(name=member.name, icon_url=member.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await member.send(embed=emb)
			return


def setup(client):
	client.add_cog(EventsJoin(client))
