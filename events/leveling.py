import discord
import jinja2
import math

from core.bases.cog_base import BaseCog
from discord.ext import commands
from discord.utils import get
from random import randint


class EventsLeveling(BaseCog):
	def __init__(self, client):
		super().__init__(client)
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

		if message.channel.id not in guild_data.ignored_channels:
			added_exp = randint(1, 5)
			added_coins = added_exp // 2 + 1

			pets_member = data.pets
			if "hamster" in pets_member:
				added_coins += math.ceil(added_coins*70/100)

			data.exp += added_exp
			data.coins += added_coins

		await self.client.database.update(
			"users",
			where={"user_id": message.author.id, "guild_id": message.guild.id},
			exp=data.exp,
			coins=data.coins,
		)

		exp_end = math.floor(9 * (data.level ** 2) + 50 * data.level + 125 * guild_data.exp_multi)
		if exp_end < data.exp:
			data.level += 1
			if guild_data.rank_message["state"]:
				ctx = await self.client.get_context(message)
				try:
					text = await self.client.template_engine.render(
						message, message.author, guild_data.rank_message["text"]
					)
				except discord.errors.HTTPException:
					emb = await self.client.utils.create_error_embed(
						ctx, "**Во время выполнения кастомной команды пройзошла неизвестная ошибка!**"
					)
					await message.channel.send(embed=emb)
				except jinja2.exceptions.TemplateSyntaxError as e:
					emb = await self.client.utils.create_error_embed(
						ctx, f"Во время выполнения кастомной команды пройзошла ошибка:\n```{repr(e)}```"
					)
					await message.channel.send(embed=emb)
				else:
					if guild_data.rank_message["type"] == "channel":
						level_channel = message.guild.get_channel(guild_data.rank_message["channel_id"])
						if level_channel is None:
							await message.channel.send(text)
						else:
							await level_channel.send(text)
					elif guild_data.rank_message["type"] == "dm":
						await message.author.send(text)

			await self.client.database.update(
				"users",
				where={"user_id": message.author.id, "guild_id": message.guild.id},
				level=data.level
			)


def setup(client):
	client.add_cog(EventsLeveling(client))
