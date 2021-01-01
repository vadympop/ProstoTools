import discord
import json
import asyncio
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
		elif not message.guild:
			return
		else:
			role = get(message.guild.roles, name=self.MUTE_ROLE)
			if role in message.author.roles:
				await message.delete()

			guild_data = await self.client.database.sel_guild(guild=message.guild)
			data = await self.client.database.sel_user(target=message.author)

			if message.channel.id in guild_data["react_channels"]:
				await message.add_reaction("👍")
				await message.add_reaction("👎")

			all_message = guild_data["all_message"]
			guild_moder_settings = guild_data["auto_mod"]
			multi = guild_data["exp_multi"]
			ignored_channels = guild_data["ignored_channels"]
			all_message += 1

			scr = """UPDATE guilds SET all_message = %s WHERE guild_id = %s AND guild_id = %s"""
			val_1 = (all_message, message.guild.id, message.guild.id)

			await self.client.database.execute(scr, val_1)

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
			lvl_member = data["lvl"]
			last_msg = messages[2]

			reput_msg = 150
			messages[0] += 1
			messages[1] += 1
			messages[2] = message.content

			exp_end = math.floor(9 * (lvl_member ** 2) + 50 * lvl_member + 125 * multi)
			if exp_end < exp:
				lvl_member += 1
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

			if messages[0] >= reput_msg:
				reputation += 1
				messages[0] = 0

			if reputation >= 100:
				reputation = 100

			sql = """UPDATE users SET exp = %s, coins = %s, reputation = %s, messages = %s, level = %s WHERE user_id = %s AND guild_id = %s"""
			val = (
				exp,
				coins,
				reputation,
				json.dumps(messages),
				lvl_member,
				message.author.id,
				message.guild.id,
			)
			try:
				await self.client.database.execute(sql, val)
			except pymysql.err.InternalError:
				pass
			try:
				await self.client.wait_for(
					"message",
					check=lambda m: m.content == last_msg
					and m.channel == message.channel,
					timeout=2.0,
				)
			except asyncio.TimeoutError:
				pass
			else:
				if guild_moder_settings["anti_flud"]:
					emb = await self.client.support_commands.main_mute(
						ctx=message,
						member=message.author,
						type_time="4h",
						reason="Авто-модерация: Флуд",
						author=message.guild.me
					)
					if emb is not None:
						await message.channel.send(embed=emb)


def setup(client):
	client.add_cog(EventsLeveling(client))
