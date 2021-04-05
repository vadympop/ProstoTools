import discord
import jinja2

from core.bases.cog_base import BaseCog
from discord.ext import commands


class EventsLeave(BaseCog):
	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		await self.client.database.add_stat_counter(entity="users", add_counter=len(self.client.users))
		await self.client.database.add_stat_counter(entity="guilds", add_counter=len(self.client.guilds))

		emb_info = discord.Embed(
			title=f"Бот изгнан из сервера, всего серверов - {len(self.client.guilds)}",
			colour=discord.Color.green(),
			description=f"Названия сервера - `{guild.name}`\nАйди сервера - `{guild.id}`\nВладелец - `{guild.owner}`\nКол-во участников - `{guild.member_count}`",
		)
		emb_info.set_thumbnail(url=guild.icon_url)
		await self.client.get_guild(717776571406090310).get_channel(737685906873647165).send(embed=emb_info)

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		await self.client.database.add_stat_counter(entity="members", add_counter=len(self.client.users))

		guild_data = await self.client.database.sel_guild(guild=member.guild)
		if not member.bot:
			if guild_data.audit["member_leave"]["state"]:
				e = discord.Embed(
					description=f"Пользователь `{member}` покинул сервер",
					colour=discord.Color.green(),
					timestamp=await self.client.utils.get_guild_time(member.guild)
				)
				e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
				e.set_author(
					name="Журнал аудита | Пользователь изгнан", icon_url=member.avatar_url
				)
				e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				channel = member.guild.get_channel(guild_data.audit["member_leave"]["channel_id"])
				if channel is not None:
					await channel.send(embed=e)

				if guild_data.donate:
					await self.client.database.add_audit_log(
						user=member,
						channel=channel,
						guild_id=member.guild.id,
						action_type="member_leave",
					)
		else:
			if guild_data.audit["bot_leave"]["state"]:
				e = discord.Embed(
					description=f"Бот `{member}` покинул сервер",
					colour=discord.Color.light_grey(),
					timestamp=await self.client.utils.get_guild_time(member.guild)
				)
				e.add_field(name="Id Бота", value=f"`{member.id}`", inline=False)
				e.set_author(
					name="Журнал аудита | Бот изгнан", icon_url=member.avatar_url
				)
				e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				channel = member.guild.get_channel(guild_data.audit["bot_leave"]["channel_id"])
				if channel is not None:
					await channel.send(embed=e)

				if guild_data.donate:
					await self.client.database.add_audit_log(
						user=member,
						channel=channel,
						guild_id=member.guild.id,
						action_type="bot_leave",
					)
				return

		if not guild_data.welcomer["leave"]["state"]:
			return

		try:
			try:
				if guild_data.welcomer["leave"]["type"] == "dm":
					await member.send(
						await self.client.template_engine.render(
							member=member,
							render_text=guild_data.welcomer["leave"]["text"]
						)
					)
				elif guild_data.welcomer["leave"]["type"] == "channel":
					channel = member.guild.get_channel(
						guild_data.welcomer["leave"]["channel"]
					)
					if channel is not None:
						await channel.send(
							await self.client.template_engine.render(
								member=member,
								render_text=guild_data.welcomer["leave"]["text"]
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
	client.add_cog(EventsLeave(client))
