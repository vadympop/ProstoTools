import jinja2
import discord
import typing

from core.bases.cog_base import BaseCog
from discord.ext import commands


class EventsCustomCommands(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.cd_mapping = commands.CooldownMapping.from_cooldown(1, 1, commands.BucketType.member)

    def find_custom_command(self, command_name: str, iterable: typing.Iterable):
        for command in iterable:
            if command["name"] == command_name:
                return command
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        PREFIX = str(await self.client.database.get_prefix(guild=message.guild))
        if message.content.startswith(PREFIX):
            guild_data = await self.client.database.sel_guild(guild=message.guild)
            command = message.content.split(" ")[0].replace(PREFIX, "")
            commands_names = [c["name"] for c in guild_data.custom_commands]
            if command in commands_names:
                custom_command_data = self.find_custom_command(command, guild_data.custom_commands)
                if not custom_command_data['state']:
                    return

                if self.cd_mapping.get_bucket(message).update_rate_limit():
                    try:
                        await message.add_reaction("⏰")
                    except discord.errors.Forbidden:
                        pass
                    except discord.errors.HTTPException:
                        pass
                    return

                if custom_command_data["target_channels"]:
                    if message.channel.id not in custom_command_data["target_channels"]:
                        return

                if custom_command_data["target_roles"]:
                    if not any([
                        role.id in custom_command_data["target_roles"]
                        for role in message.author.roles
                    ]):
                        return

                if message.channel.id in custom_command_data["ignore_channels"]:
                    return

                if any([
                    role.id in custom_command_data["ignore_roles"]
                    for role in message.author.roles
                ]):
                    return

                ctx = await self.client.get_context(message)
                try:
                    try:
                        await message.channel.send(await self.client.template_engine.render(
                            message, message.author, custom_command_data["message"]
                        ))
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
