import discord
import json
import jinja2
import math
import pymysql
from discord.ext import commands
from discord.utils import get
from random import randint


class EventsLeveling(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT
		self.MUTE_ROLE = self.client.config.MUTE_ROLE
		self.HELP_SERVER = self.client.config.HELP_SERVER

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author.bot:
			return

		if message.guild is None:
			return

		if message.author != message.guild.owner:
			role = get(message.guild.roles, name=self.MUTE_ROLE)
			if role in message.author.roles:
				try:
					await message.delete()
				except discord.errors.NotFound:
					pass

		guild_data = await self.client.database.sel_guild(guild=message.guild)
		data = await self.client.database.sel_user(target=message.author)

		multi = guild_data["exp_multi"]
		ignored_channels = guild_data["ignored_channels"]

		exp = data["exp"]
		coins = data["coins"]
		lvl_member = data["level"]

		if message.channel.id not in ignored_channels:
			added_exp = randint(1, 5)
			added_coins = added_exp // 2 + 1

			pets_member = data["pets"]
			if "hamster" in pets_member:
				added_coins += math.ceil(added_coins*70/100)
			exp += added_exp
			coins += added_coins

			exp_end = math.floor(9 * (lvl_member ** 2) + 50 * lvl_member + 125 * multi)
			if exp_end < exp:
				lvl_member += 1
				if guild_data["rank_message"]["state"]:
					data["level"] = lvl_member
					data["exp"] = exp
					data["coins"] = coins
					data.update({"multi": guild_data["exp_multi"]})
					try:
						text = await self.client.template_engine.render(
							message,
							message.author,
							data,
							guild_data["rank_message"]["text"]
						)
					except discord.errors.HTTPException:
						try:
							await message.add_reaction("❌")
						except discord.errors.Forbidden:
							pass
						except discord.errors.HTTPException:
							pass
						emb = discord.Embed(
							title="Ошибка!",
							description=f"**Во время выполнения кастомной команды пройзошла ошибка неизвестная ошибка!**",
							colour=discord.Color.red(),
						)
						emb.set_author(name=message.author.name, icon_url=message.author.avatar_url)
						emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
						await message.channel.send(embed=emb)
					except jinja2.exceptions.TemplateSyntaxError as e:
						try:
							await message.add_reaction("❌")
						except discord.errors.Forbidden:
							pass
						except discord.errors.HTTPException:
							pass
						emb = discord.Embed(
							title="Ошибка!",
							description=f"Во время выполнения кастомной команды пройзошла ошибка:\n```{repr(e)}```",
							colour=discord.Color.red(),
						)
						emb.set_author(name=message.author.name, icon_url=message.author.avatar_url)
						emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
						await message.channel.send(embed=emb)
					else:
						if guild_data["rank_message"]["type"] == "channel":
							await message.channel.send(text)
						elif guild_data["rank_message"]["type"] == "dm":
							await message.author.send(text)

		await self.client.database.update(
			"users",
			where={"user_id": message.author.id, "guild_id": message.guild.id},
			exp=exp,
			coins=coins,
			level=lvl_member
		)


def setup(client):
	client.add_cog(EventsLeveling(client))
