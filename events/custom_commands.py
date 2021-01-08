import jinja2
import discord
from discord.ext import commands


class EventsCustomCommands(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.FOOTER = self.client.config.FOOTER_TEXT

    def find_custom_command(self, command_name: str, commands: list):
        for command in commands:
            if command["name"] == command_name:
                return command
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is not None:
            PREFIX = self.client.database.get_prefix(guild=message.guild)
            if message.content.startswith(PREFIX):
                guild_data = await self.client.database.sel_guild(guild=message.guild)
                command = message.content.split(" ")[0].replace(PREFIX, "")
                commands_names = [c["name"] for c in guild_data["custom_commands"]]
                if command in commands_names:
                    custom_command_data = self.find_custom_command(command, guild_data["custom_commands"])
                    member_data = await self.client.database.sel_user(target=message.author)
                    member_data.update({"multi": guild_data["exp_multi"]})
                    try:
                        try:
                            await message.channel.send(
                                await self.client.template_engine.render(
                                    message, message.author, member_data, custom_command_data["code"]
                                )
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


def setup(client):
    client.add_cog(EventsCustomCommands(client))
