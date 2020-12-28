import discord

from tools import Commands
from discord.ext import commands


class EventsReactionsCmds(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		reaction = payload.emoji
		author = payload.member
		channel = self.client.get_channel(payload.channel_id)
		message = await channel.fetch_message(payload.message_id)
		member = message.author
		guild = message.guild
		if guild:
			data = await self.client.database.sel_guild(guild=guild)

			if data["auto_mod"]["react_coomands"]:
				if not author.bot:
					if author.guild_permissions.administrator:
						if reaction.name == "❌":
							try:
								await member.ban(reason="Нарушения правил")
							except:
								return

							emb = discord.Embed(
								description=f"**{author.mention} Забанил {member.mention}**",
								colour=discord.Color.green(),
							)
							emb.set_author(name=author.name, icon_url=author.avatar_url)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await message.channel.send(embed=emb)

							emb = discord.Embed(
								description=f"**Вы были забанены на сервере {message.guild.name}**",
								colour=discord.Color.green(),
							)
							emb.set_author(name=author.name, icon_url=author.avatar_url)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							try:
								await member.send(embed=emb)
							except:
								pass
						elif reaction.name == "🤐":
							emb = await self.client.support_commands.main_mute(
								ctx=message,
								member=member,
								reason="Команды по реакциям: Нарушения правил",
								check_role=True,
							)
							await message.channel.send(embed=emb)
						elif reaction.name == "💀":
							await member.kick(reason="Нарушения правил")

							emb = discord.Embed(
								description=f"**{author.mention} Кикнул {member.mention}**",
								colour=discord.Color.green(),
							)
							emb.set_author(name=author.name, icon_url=author.avatar_url)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await message.channel.send(embed=emb)

							emb = discord.Embed(
								description=f"**Администратор {author.mention} кикнул вас из сервера** ***{guild.name}***",
								colour=discord.Color.green(),
							)
							emb.set_author(name=author.name, icon_url=author.avatar_url)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							try:
								await member.send(embed=emb)
							except:
								pass


def setup(client):
	client.add_cog(EventsReactionsCmds(client))
