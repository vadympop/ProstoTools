import discord
import json
import asyncio
import time
import os
import mysql.connector
from discord.ext import commands, tasks
from discord.utils import get
from discord.voice_client import VoiceClient
from discord.ext.commands import Bot
from random import randint
from configs import configs
from Tools.database import DB


def check_role(ctx):
    data = DB().sel_guild(guild=ctx.guild)["moder_roles"]
    roles = ctx.guild.roles[::-1]
    data.append(roles[0].id)

    if data != []:
        for role in data:
            role = get(ctx.guild.roles, id=role)
            yield role in ctx.author.roles
    else:
        return roles[0] in ctx.author.roles


class Utils(commands.Cog, name="Utils"):
    def __init__(self, client):
        self.client = client
        self.conn = mysql.connector.connect(
            user="root",
            password=os.environ["DB_PASSWORD"],
            host="localhost",
            database="data",
        )
        self.cursor = self.conn.cursor(buffered=True)
        self.FOOTER = configs["FOOTER_TEXT"]

    @commands.command(
        brief="True",
        description="**Устанавливает анти-рейд режим. Есть не сколько режымов, 1 - Слабый 5сек задержка в текстовых каналах и средний уровень модерации, 2 - Сильний 10сек задержка в текстовых каналах и високий уровень модерации, 3 - Найвисшый 15сек задержка в текстовых каналах и найвисшый уровень модерации**",
        usage="anti-rade [Время действия] [Уровень защиты]",
    )
    @commands.check(check_role)
    async def antirade(self, ctx, time:int, mode:int):
        purge = self.client.clear_commands(ctx.guild)
        await ctx.channel.purge(limit=purge)

        first_verfLevel = ctx.guild.verification_level

        if mode == 1:
            emb = discord.Embed(
                title=f"**Уставлен анти-рейд режим 1-го уровня на {time}мин**",
                colour=discord.Color.green(),
            )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

            await ctx.guild.edit(verification_level=discord.VerificationLevel.medium)
            for i in ctx.guild.text_channels:
                await i.edit(slowmode_delay=5)

            await asyncio.sleep(time * 60)
            await ctx.guild.edit(verification_level=first_verfLevel)

            for k in ctx.guild.text_channels:
                await k.edit(slowmode_delay=0)
        elif mode == 2:
            emb = discord.Embed(
                title=f"**Уставлен анти-рейд режим 2-го уровня на {time}мин**",
                colour=discord.Color.green(),
            )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

            await ctx.guild.edit(verification_level=discord.VerificationLevel.high)
            for i in ctx.guild.text_channels:
                await i.edit(slowmode_delay=10)

            await asyncio.sleep(time * 60)
            await ctx.guild.edit(verification_level=first_verfLevel)

            for k in ctx.guild.text_channels:
                await k.edit(slowmode_delay=0)
        elif mode == 3:
            emb = discord.Embed(
                title=f"**Уставлен анти-рейд режим 3-го уровня на {time}мин**",
                colour=discord.Color.green(),
            )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

            await ctx.guild.edit(verification_level=discord.VerificationLevel.extreme)
            for i in ctx.guild.text_channels:
                await i.edit(slowmode_delay=15)

            await asyncio.sleep(time * 60)
            await ctx.guild.edit(verification_level=first_verfLevel)

            for k in ctx.guild.text_channels:
                await k.edit(slowmode_delay=0)

    @commands.command(
        aliases=["banlist"],
        brief="True",
        name="ban-list",
        description="**Показывает заблокированных пользователей**",
        usage="ban-list",
    )
    @commands.check(check_role)
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def bannedusers(self, ctx):
        purge = self.client.clear_commands(ctx.guild)
        await ctx.channel.purge(limit=purge)

        banned_users = await ctx.guild.bans()

        if banned_users == []:
            emb = discord.Embed(
                title="На этом сервере нету заблокированых участников",
                colour=discord.Color.green(),
            )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
        else:
            emb = discord.Embed(
                title="Список заблокированных участников", colour=discord.Color.green()
            )
            for user in banned_users:
                emb.add_field(
                    name=f"Участник: {user.user}",
                    value=f"**Причина бана: {user.reason}**"
                    if user.reason
                    else "**Причина бана: Причина не указана**",
                )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

    @commands.command(
        aliases=["voicerooms"],
        name="voice-rooms",
        hidden=True,
        description="**Создает голосовой канал для создания приватных голосовых комнат**",
        usage="voice-rooms [Вкл/Выкл]",
    )
    @commands.check(lambda ctx: ctx.author == ctx.guild.owner)
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def voicechannel(self, ctx, state:str):
        purge = self.client.clear_commands(ctx.guild)
        await ctx.channel.purge(limit=purge)

        channel_category = await ctx.guild.create_category("Голосовые комнаты")
        await asyncio.sleep(1)

        on_answers = ["on", "вкл", "включить", "true"]
        off_answers = ["off", "выкл", "выключить", "false"]

        if state.lower() in on_answers:
            data = DB().sel_guild(guild=ctx.guild)["voice_channel"]

            if "channel_id" not in data:
                voice_channel = await ctx.guild.create_voice_channel(
                    "Нажми на меня", category=channel_category
                )
                await ctx.message.add_reaction("✅")
                data.update({"channel_id": voice_channel.id})

                sql = """UPDATE guilds SET voice_channel = %s WHERE guild_id = %s AND guild_id = %s"""
                val = (json.dumps(data), ctx.guild.id, ctx.guild.id)

                self.cursor.execute(sql, val)
                self.conn.commit()
            else:
                emb = discord.Embed(
                    desciption="**На этом сервере приватные голосовые комнаты уже есть**",
                    color=discord.Color.green(),
                )
                emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
                await ctx.send(embed=emb)
                await ctx.message.add_reaction("❌")
                return

        elif state in off_answers:
            await ctx.message.add_reaction("✅")

            sql = """UPDATE guilds SET voice_channel = %s WHERE guild_id = %s AND guild_id = %s"""
            val = (json.dumps({}), ctx.guild.id, ctx.guild.id)

            self.cursor.execute(sql, val)
            self.conn.commit()
        else:
            emb = discord.Embed(
                title="Ошибка!",
                desciption="**Вы не правильно указали действие! Укажите on - что бы включить, off - что бы выключить**",
                color=discord.Color.green(),
            )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
            await ctx.message.add_reaction("❌")
            return

    @commands.command(
        aliases=["serverstats"],
        name="server-stats",
        hidden=True,
        description="**Создает статистику сервера**",
        usage="server-stats [Счетчик]",
    )
    @commands.check(lambda ctx: ctx.author == ctx.guild.owner)
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def serverstats(self, ctx, stats_count):
        purge = self.client.clear_commands(ctx.guild)
        await ctx.channel.purge(limit=purge)

        members_count = len(
            [
                member.id
                for member in ctx.guild.members
                if not member.bot and member.id != self.client.user.id
            ]
        )
        bots_count = len([bot.id for bot in ctx.guild.members if bot.bot])
        channels_count = len([channel.id for channel in ctx.guild.channels])
        roles_count = len([role.id for role in ctx.guild.roles])
        counters = {
            "all": ["Пользователей", ctx.guild.member_count],
            "bots": ["Ботов", bots_count],
            "roles": ["Ролей", roles_count],
            "channels": ["Каналов", channels_count],
            "members": ["Участников", members_count],
        }

        if stats_count.lower() not in counters.keys():
            emb = discord.Embed(
                title="Ошибка!",
                description="**Вы не правильно указали счетчик. Укажите из этих: bots, all, members, roles, channels**",
                color=discord.Color.green(),
            )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
            await ctx.message.add_reaction("❌")
            return

        stats_category = await ctx.guild.create_category("Статистика")
        await asyncio.sleep(1)

        overwrite = discord.PermissionOverwrite(connect=False)
        stats_channel = await ctx.guild.create_voice_channel(
            f"[{counters[stats_count.lower()][1]}] {counters[stats_count.lower()][0]}",
            category=stats_category,
        )
        await stats_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        await stats_category.edit(position=0)
        await ctx.message.add_reaction("✅")

        data = DB().sel_guild(guild=ctx.guild)["server_stats"]
        data.update({stats_count.lower(): stats_channel.id})

        sql = """UPDATE guilds SET server_stats = %s WHERE guild_id = %s AND guild_id = %s"""
        val = (json.dumps(data), ctx.guild.id, ctx.guild.id)

        self.cursor.execute(sql, val)
        self.conn.commit()

    @commands.command(
        aliases=["massrole"],
        name="mass-role",
        hidden=True,
        description="**Удаляет или добавляет роль участникам с указаной ролью**",
        usage="mass-role [Действие(add/del/remove)] [@Роль] [@Изменяемая роль]",
    )
    @commands.cooldown(1, 1800, commands.BucketType.member)
    @commands.has_permissions(administrator=True)
    async def mass_role(
        self, ctx, type_act:str, for_role:discord.Role, role:discord.Role
    ):
        purge = self.client.clear_commands(ctx.guild)
        await ctx.channel.purge(limit=purge)

        if type_act == "add":
            for member in ctx.guild.members:
                if for_role in member.roles:
                    if role not in member.roles:
                        await member.add_roles(role)

            emb = discord.Embed(
                title="Операция добавления роли проведенна успешно",
                description=f"У пользователей с ролью `{for_role.name}` была добавленна роль - `{role.name}`",
                colour=discord.Color.green(),
            )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
        elif type_act == "remove" or type_act == "del":
            for member in ctx.guild.members:
                if for_role in member.roles:
                    if role in member.roles:
                        await member.remove_roles(role)

            emb = discord.Embed(
                title="Операция снятия роли проведенна успешно",
                description=f"У пользователей с ролью `{for_role.name}` была снята роль - `{role.name}`",
                colour=discord.Color.green(),
            )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
        else:
            emb = discord.Embed(
                title="Ошибка!",
                description=f"Вы указали не правильное действие! Укажите add - для добавления, del или remove - для удаления",
                colour=discord.Color.green(),
            )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

    @commands.command(
        brief="True",
        aliases=["list-moders", "moders", "moderators"],
        name="list-moderators",
        description="**Показывает список ролей модераторов**",
        usage="list-moderators",
    )
    @commands.check(check_role)
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def list_moderators(self, ctx):
        purge = self.client.clear_commands(ctx.guild)
        await ctx.channel.purge(limit=purge)

        data = DB().sel_guild(guild=ctx.guild)["moder_roles"]
        if data != []:
            roles = "\n".join(f"`{get(ctx.guild.roles, id=i).name}`" for i in data)
        else:
            roles = "Роли модераторов не настроены"

        emb = discord.Embed(
            title="Роли модераторов", description=roles, colour=discord.Color.green()
        )
        emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)

    @commands.command(
        aliases=["mutes-list", "listmutes", "muteslist"],
        name="list-mutes",
        description="Показывает все мьюты на сервере",
        usage="list-mutes",
    )
    @commands.check(check_role)
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def mutes(self, ctx):
        purge = self.client.clear_commands(ctx.guild)
        await ctx.channel.purge(limit=purge)

        data = DB().get_mutes(ctx.guild.id)

        if data != []:
            mutes = "\n\n".join(
                f"**Пользователь:** `{ctx.guild.get_member(mute[1])}`, **Причина:** `{mute[3]}`\n**Автор:** {mute[6]}, **Время мьюта:** `{mute[5]}`\n**Активный до**: `{mute[4]}`"
                for mute in data
            )
        else:
            mutes = "На сервере нету мьютов"

        emb = discord.Embed(
            title="Список всех мьютов на сервере",
            description=mutes,
            colour=discord.Color.green(),
        )
        emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)


def setup(client):
    client.add_cog(Utils(client))
