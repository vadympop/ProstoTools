import discord
import json
import jinja2
import math
import datetime
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

		role = get(message.guild.roles, name=self.MUTE_ROLE)
		if role in message.author.roles:
			await message.delete()

		guild_data = await self.client.database.sel_guild(guild=message.guild)
		data = await self.client.database.sel_user(target=message.author)

		all_message = guild_data["all_message"]
		multi = guild_data["exp_multi"]
		ignored_channels = guild_data["ignored_channels"]
		all_message += 1

		await self.client.database.update(
			"guilds",
			where={"guild_id": message.guild.id},
			all_message=all_message
		)

		if ignored_channels != []:
			if message.channel.id in ignored_channels:
				return

		rand_number_1 = randint(1, 5)
		exp_first = rand_number_1
		coins_first = exp_first // 2 + 1

		exp_member = data["exp"]
		coins_member = data["coins"]
		pets_member = data["pets"]
		if "hamster" in pets_member:
			coins_first += math.ceil(coins_first*70/100)
		exp = exp_first + exp_member
		coins = coins_first + coins_member
		reputation = data["reputation"]
		messages = data["messages"]
		lvl_member = data["level"]

		reput_msg = 150
		print(messages)
		print(type(messages))
		messages[0] = int(messages[0])+1
		messages[1] = int(messages[1])+1
		messages[2] = message.content

		exp_end = math.floor(9 * (lvl_member ** 2) + 50 * lvl_member + 125 * multi)
		if exp_end < exp:
			lvl_member += 1
			if not guild_data["rank_message"]["state"]:
				emb_lvl = discord.Embed(
					title="Сообщения о повышении уровня",
					description=f"Участник {message.author.mention} повысил свой уровень! Текущий уровень - `{lvl_member}`",
					timestamp=datetime.datetime.utcnow(),
					colour=discord.Color.green(),
				)

				emb_lvl.set_author(
					name=message.author.name, icon_url=message.author.avatar_url
				)
				emb_lvl.set_footer(
					text=self.FOOTER, icon_url=self.client.user.avatar_url
				)
				await message.channel.send(embed=emb_lvl)
			else:
				data.update({"multi": guild_data["exp_multi"]})
				try:
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
						except:
							pass
						emb = discord.Embed(
							title="Ошибка!",
							description=f"**Во время выполнения кастомной команды пройзошла ошибка неизвестная ошибка!**",
							colour=discord.Color.red(),
						)
						emb.set_author(name=message.author.name, icon_url=message.author.avatar_url)
						emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
						await message.channel.send(embed=emb)
						return
				except jinja2.exceptions.TemplateSyntaxError as e:
					try:
						await message.add_reaction("❌")
					except:
						pass
					emb = discord.Embed(
						title="Ошибка!",
						description=f"Во время выполнения кастомной команды пройзошла ошибка:\n```{repr(e)}```",
						colour=discord.Color.red(),
					)
					emb.set_author(name=message.author.name, icon_url=message.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await message.channel.send(embed=emb)
					return

				if guild_data["rank_message"]["type"] == "channel":
					await message.channel.send(text)
				elif guild_data["rank_message"]["type"] == "dm":
					await message.author.send(text)

		if messages[0] >= reput_msg:
			reputation += 1
			messages[0] = 0

		if reputation >= 100:
			reputation = 100

		try:
			await self.client.database.update(
				"users",
				where={"user_id": message.author.id, "guild_id": message.guild.id},
				exp=exp,
				coins=coins,
				reputation=reputation,
				messages=json.dumps(messages),
				level=lvl_member
			)
		except pymysql.err.InternalError:
			pass


def setup(client):
	client.add_cog(EventsLeveling(client))
