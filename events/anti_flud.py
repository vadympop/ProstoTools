import asyncio
import discord
import jinja2
from tools import TimeConverter
from discord.ext import commands


class EventsAntiFlud(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.SOFTBAN_ROLE = self.client.config.SOFTBAN_ROLE
        self.FOOTER = self.client.config.FOOTER_TEXT
        self.time_converter = TimeConverter()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        data = await self.client.database.sel_guild(guild=message.guild)
        member_data = await self.client.database.sel_user(target=message.author)
        try:
            await self.client.wait_for(
                "message",
                check=lambda m: m.content == member_data["messages"][2] and m.channel == message.channel,
                timeout=2.0,
            )
        except asyncio.TimeoutError:
            pass
        else:
            if data["auto_mod"]["anti_flud"]["state"]:
                if "target_channels" in data["auto_mod"]["anti_flud"].keys():
                    if data["auto_mod"]["anti_flud"]["target_channels"]:
                        if message.channel.id not in data["auto_mod"]["anti_flud"]["target_channels"]:
                            return

                if "target_roles" in data["auto_mod"]["anti_flud"].keys():
                    if data["auto_mod"]["anti_flud"]["target_roles"]:
                        state = False
                        for role in message.author.roles:
                            if role.id in data["auto_mod"]["anti_flud"]["target_roles"]:
                                state = True

                        if not state:
                            return

                if "ignore_channels" in data["auto_mod"]["anti_flud"].keys():
                    if message.channel.id in data["auto_mod"]["anti_flud"]["ignore_channels"]:
                        return

                if "ignore_roles" in data["auto_mod"]["anti_flud"].keys():
                    for role in message.author.roles:
                        if role.id in data["auto_mod"]["anti_flud"]["ignore_roles"]:
                            return

                if "punishment" in data["auto_mod"]["anti_flud"].keys():
                    reason = "Авто-модерация: Флуд"
                    type_punishment = data["auto_mod"]["anti_flud"]["punishment"]["type"]
                    ctx = await self.client.get_context(message)
                    expiry_in = None
                    if data["auto_mod"]["anti_flud"]["punishment"]["time"] is not None:
                        try:

                            expiry_in = await self.time_converter.convert(
                                ctx, data["auto_mod"]["anti_flud"]["punishment"]["time"]
                            )
                        except commands.BadArgument:
                            pass

                    if type_punishment == "mute":
                        await self.client.support_commands.mute(
                            ctx=ctx,
                            member=message.author,
                            author=message.guild.me,
                            expiry_in=expiry_in,
                            reason=reason,
                        )
                    elif type_punishment == "warn":
                        await self.client.support_commands.warn(
                            ctx=ctx,
                            member=message.author,
                            author=message.guild.me,
                            reason=reason,
                        )
                    elif type_punishment == "kick":
                        await self.client.support_commands.kick(
                            ctx=ctx,
                            member=message.author,
                            author=message.guild.me,
                            reason=reason
                        )
                    elif type_punishment == "ban":
                        await self.client.support_commands.ban(
                            ctx=ctx,
                            member=message.author,
                            author=message.guild.me,
                            expiry_in=expiry_in,
                            reason=reason,
                        )
                    elif type_punishment == "soft-ban":
                        await self.client.support_commands.soft_ban(
                            ctx=ctx,
                            member=message.author,
                            author=message.guild.me,
                            expiry_in=expiry_in,
                            reason=reason,
                        )

                if "message" in data["auto_mod"]["anti_flud"].keys():
                    member_data.update({"multi": data["exp_multi"]})
                    try:
                        try:
                            text = await self.client.template_engine.render(
                                message,
                                message.author,
                                member_data,
                                data["auto_mod"]["anti_flud"]["message"]["text"]
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
                            return
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
                        return

                    if data["auto_mod"]["anti_flud"]["message"]["type"] == "channel":
                        await message.channel.send(text)
                    elif data["auto_mod"]["anti_flud"]["message"]["type"] == "dm":
                        try:
                            await message.author.send(text)
                        except discord.errors.Forbidden:
                            pass


def setup(client):
    client.add_cog(EventsAntiFlud(client))
