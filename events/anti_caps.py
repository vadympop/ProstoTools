import discord
import jinja2
from core.utils.other import process_converters
from core.converters import Expiry
from discord.ext import commands


class EventsAntiCaps(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.SOFTBAN_ROLE = self.client.config.SOFTBAN_ROLE
        self.FOOTER = self.client.config.FOOTER_TEXT

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        data = await self.client.database.sel_guild(guild=message.guild)
        if data["auto_mod"]["anti_caps"]["state"]:
            content_without_spaces = message.content.replace(" ", "")
            num_upper_chars = 0
            for char in list(content_without_spaces):
                if char.isupper():
                    num_upper_chars += 1

            upper_percent = (num_upper_chars/len(content_without_spaces))*100
            if not upper_percent >= data["auto_mod"]["anti_caps"]["percent"]:
                return

            if "target_channels" in data["auto_mod"]["anti_caps"].keys():
                if data["auto_mod"]["anti_caps"]["target_channels"]:
                    if message.channel.id not in data["auto_mod"]["anti_caps"]["target_channels"]:
                        return

            if "target_roles" in data["auto_mod"]["anti_caps"].keys():
                if data["auto_mod"]["anti_caps"]["target_roles"]:
                    state = False
                    for role in message.author.roles:
                        if role.id in data["auto_mod"]["anti_caps"]["target_roles"]:
                            state = True

                    if not state:
                        return

            if "ignore_channels" in data["auto_mod"]["anti_caps"].keys():
                if message.channel.id in data["auto_mod"]["anti_caps"]["ignore_channels"]:
                    return

            if "ignore_roles" in data["auto_mod"]["anti_caps"].keys():
                for role in message.author.roles:
                    if role.id in data["auto_mod"]["anti_caps"]["ignore_roles"]:
                        return

            if "punishment" in data["auto_mod"]["anti_caps"].keys():
                reason = "Авто-модерация: Приглашения"
                type_punishment = data["auto_mod"]["anti_caps"]["punishment"]["type"]
                ctx = await self.client.get_context(message)
                expiry_at = None
                if data["auto_mod"]["anti_caps"]["punishment"]["time"] is not None:
                    expiry_at = await process_converters(
                        ctx, Expiry.__args__, data["auto_mod"]["anti_caps"]["punishment"]["time"]
                    )

                if type_punishment == "mute":
                    await self.client.support_commands.mute(
                        ctx=ctx,
                        member=message.author,
                        author=message.guild.me,
                        expiry_at=expiry_at,
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
                        expiry_at=expiry_at,
                        reason=reason,
                    )
                elif type_punishment == "soft-ban":
                    await self.client.support_commands.soft_ban(
                        ctx=ctx,
                        member=message.author,
                        author=message.guild.me,
                        expiry_at=expiry_at,
                        reason=reason,
                    )

            if "delete_message" in data["auto_mod"]["anti_caps"].keys():
                await message.delete()

            if "message" in data["auto_mod"]["anti_caps"].keys():
                member_data = await self.client.database.sel_user(target=message.author)
                member_data.update({"multi": data["exp_multi"]})
                try:
                    try:
                        text = await self.client.template_engine.render(
                            message,
                            message.author,
                            member_data,
                            data["auto_mod"]["anti_caps"]["message"]["text"]
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

                if data["auto_mod"]["anti_caps"]["message"]["type"] == "channel":
                    await message.channel.send(text)
                elif data["auto_mod"]["anti_caps"]["message"]["type"] == "dm":
                    try:
                        await message.author.send(text)
                    except discord.errors.Forbidden:
                        pass


def setup(client):
    client.add_cog(EventsAntiCaps(client))
