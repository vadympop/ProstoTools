import re
import discord
import time
import json
import jinja2
from discord.ext import commands


class EventsAntiInvite(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.SOFTBAN_ROLE = self.client.config.SOFTBAN_ROLE
        self.FOOTER = self.client.config.FOOTER_TEXT
        self.pattern = re.compile(
            "discord\s?(?:(?:.|dot|(.)|(dot))\s?gg|(?:app)?\s?.\s?com\s?/\s?invite)\s?/\s?([A-Z0-9-]{2,18})", re.I
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        data = await self.client.database.sel_guild(guild=message.guild)
        if data["auto_mod"]["anti_invite"]["state"]:
            finded_codes = re.findall(self.pattern, message.content)
            try:
                guild_invites_codes = [invite.code for invite in await message.guild.invites()]
            except discord.errors.Forbidden:
                return

            invites = [
                invite
                for item in finded_codes
                for invite in item
                if invite
                if invite not in guild_invites_codes
            ]
            if invites == []:
                return

            if "target_channels" in data["auto_mod"]["anti_invite"].keys():
                if message.channel.id not in data["auto_mod"]["anti_invite"]["target_channels"]:
                    return

            if "target_roles" in data["auto_mod"]["anti_invite"].keys():
                for role in message.author.roles:
                    if role.id not in data["auto_mod"]["anti_invite"]["target_roles"]:
                        return

            if "ignore_channels" in data["auto_mod"]["anti_invite"].keys():
                if message.channel.id in data["auto_mod"]["anti_invite"]["ignore_channels"]:
                    return

            if "ignore_roles" in data["auto_mod"]["anti_invite"].keys():
                for role in message.author.roles:
                    if role.id in data["auto_mod"]["anti_invite"]["ignore_roles"]:
                        return

            if "punishment" in data["auto_mod"]["anti_invite"].keys():
                reason = "Авто-модерация: Приглашения"
                type_punishment = data["auto_mod"]["anti_invite"]["punishment"]["type"]
                if type_punishment == "mute":
                    await self.client.support_commands.main_mute(
                        ctx=message,
                        member=message.author,
                        type_time=data["auto_mod"]["anti_invite"]["punishment"]["time"],
                        reason=reason,
                        author=message.guild.me,
                        check_role=False,
                        message=False
                    )
                elif type_punishment == "warn":
                    await self.client.support_commands.main_mute(
                        member=message.author,
                        reason=reason,
                        author=message.guild.me
                    )
                elif type_punishment == "kick":
                    try:
                        await message.author.kick(reason=reason)
                    except discord.errors.Forbidden:
                        return
                elif type_punishment == "ban":
                    ban_time = self.client.utils.time_to_num(
                        data["auto_mod"]["anti_invite"]["punishment"]["time"]
                    )
                    times = time.time() + ban_time[0]
                    try:
                        await message.author.ban(reason=reason)
                    except discord.errors.Forbidden:
                        return

                    if ban_time > 0:
                        await self.client.database.update(
                            "users",
                            where={"user_id": message.author.id, "guild_id": message.guild.id},
                            money=0,
                            coins=0,
                            reputation=-100,
                            items=json.dumps([]),
                            clan=""
                        )
                        await self.client.database.set_punishment(
                            type_punishment="ban", time=times, member=message.author
                        )
                elif type_punishment == "soft-ban":
                    softban_time = self.client.utils.time_to_num(
                        data["auto_mod"]["anti_invite"]["punishment"]["time"]
                    )
                    times = time.time() + softban_time[0]
                    overwrite = discord.PermissionOverwrite(
                        connect=False, view_channel=False, send_messages=False
                    )
                    role = discord.utils.get(
                        message.guild.roles, name=self.SOFTBAN_ROLE
                    )
                    if role is None:
                        role = await message.guild.create_role(name=self.SOFTBAN_ROLE)

                    await message.author.edit(voice_channel=None)
                    for channel in message.guild.channels:
                        await channel.set_permissions(role, overwrite=overwrite)

                    await message.author.add_roles(role)
                    if softban_time[0] > 0:
                        await self.client.database.set_punishment(
                            type_punishment="temprole", time=times, member=message.author, role=role.id
                        )

            if "message" in data["auto_mod"]["anti_invite"].keys():
                member_data = await self.client.database.sel_user(target=message.author)
                member_data.update({"multi": data["exp_multi"]})
                try:
                    try:
                        text = await self.client.template_engine.render(
                            message,
                            message.author,
                            member_data,
                            data["auto_mod"]["anti_invite"]["message"]["text"]
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

                if data["auto_mod"]["anti_invite"]["message"]["type"] == "channel":
                    await message.channel.send(text)
                elif data["auto_mod"]["anti_invite"]["message"]["type"] == "dm":
                    try:
                        await message.author.send(text)
                    except discord.errors.Forbidden:
                        pass


def setup(client):
    client.add_cog(EventsAntiInvite(client))
