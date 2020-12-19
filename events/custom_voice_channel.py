import discord
from discord.ext import commands


class EventsCustomVoice(commands.Cog):
	def __init__(self, client):
		self.client = client

	@commands.Cog.listener()
	async def on_voice_state_update(self, member, before, after):
		if self.client.is_ready():
			data = await self.client.database.sel_guild(guild=member.guild)["voice_channel"]
			if data != {}:
				main_channel = data["channel_id"]
				main_channel_obj = self.client.get_channel(int(main_channel))
				category = main_channel_obj.category

			try:
				if after.channel.id == main_channel:
					if before.channel is None and after.channel:

						overwrites = {
							member.guild.default_role: discord.PermissionOverwrite(
								connect=False, manage_permissions=False
							),
							member: discord.PermissionOverwrite(
								connect=True, manage_permissions=True, manage_channels=True
							),
							self.client.user: discord.PermissionOverwrite(
								connect=True, manage_permissions=True, manage_channels=True
							),
						}

						member_channel = await member.guild.create_voice_channel(
							name=f"{member.name} Channel",
							overwrites=overwrites,
							category=category,
							guild=member.guild,
						)
						await member.move_to(member_channel)
						await self.client.wait_for(
							"voice_state_update",
							check=lambda a, b, c: len(member_channel.members) <= 0,
						)
						await member_channel.delete()
				else:
					return
			except:
				pass


def setup(client):
	client.add_cog(EventsCustomVoice(client))
