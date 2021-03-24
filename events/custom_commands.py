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
            if message.author.bot:
                return

            PREFIX = str(await self.client.database.get_prefix(guild=message.guild))
            if message.content.startswith(PREFIX):
                guild_data = await self.client.database.sel_guild(guild=message.guild)
                command = message.content.split(" ")[0].replace(PREFIX, "")
                commands_names = [c["name"] for c in guild_data["custom_commands"]]
                if command in commands_names:
                    custom_command_data = self.find_custom_command(command, guild_data["custom_commands"])
                    if "target_channels" in custom_command_data.keys():
                        if custom_command_data["target_channels"]:
                            if message.channel.id not in custom_command_data["target_channels"]:
                                return

                    if "target_roles" in custom_command_data.keys():
                        if custom_command_data["target_roles"]:
                            state = False
                            for role in message.author.roles:
                                if role.id in custom_command_data["target_roles"]:
                                    state = True

                            if not state:
                                return

                    if "ignore_channels" in custom_command_data.keys():
                        if message.channel.id in custom_command_data["ignore_channels"]:
                            return

                    if "ignore_roles" in custom_command_data.keys():
                        for role in message.author.roles:
                            if role.id in custom_command_data["ignore_roles"]:
                                return

                    member_data = await self.client.database.sel_user(target=message.author)
                    member_data.update({"multi": guild_data["exp_multi"]})
                    ctx = await self.client.get_context(message)
                    try:
                        try:
                            await message.channel.send(
                                await self.client.template_engine.render(
                                    message, message.author, member_data, custom_command_data["code"]
                                )
                            )
                        except discord.errors.HTTPException:
                            emb = await self.client.utils.create_error_embed(
                                ctx, "**Во время выполнения кастомной команды пройзошла неизвестная ошибка!**"
                            )
                            await message.channel.send(embed=emb)
                            return
                    except jinja2.exceptions.TemplateSyntaxError as e:
                        emb = await self.client.utils.create_error_embed(
                            ctx, f"Во время выполнения кастомной команды пройзошла ошибка:\n```{repr(e)}```"
                        )
                        await message.channel.send(embed=emb)
                        return

                    if "functions" in custom_command_data.keys():
                        for name, value in custom_command_data["functions"].items():
                            if name == "role_add":
                                role = message.guild.get_role(int(value))
                                if role is not None:
                                    await message.author.add_roles(role)
                            elif name == "role_remove":
                                role = message.guild.get_role(int(value))
                                if role is not None:
                                    await message.author.remove_roles(role)


def setup(client):
    client.add_cog(EventsCustomCommands(client))
