from discord.ext import commands


class EventsCustomCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is not None:
            PREFIX = self.client.database.get_prefix(guild=message.guild)
            if message.content.startswith(PREFIX):
                guild_data = await self.client.database.sel_guild(guild=message.guild)
                command = message.content.split(" ")[0].replace(PREFIX, "")
                if command in guild_data["custom_commands"].keys():
                    member_data = await self.client.database.sel_user(target=message.author)
                    member_data.update({"multi": guild_data["exp_multi"]})
                    await message.channel.send(
                        await self.client.template_engine.render(
                            message, message.author, member_data, guild_data["custom_commands"][command]
                        )
                    )


def setup(client):
    client.add_cog(EventsCustomCommands(client))
