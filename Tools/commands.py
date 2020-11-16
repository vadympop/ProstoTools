import discord
import json
import asyncio
import typing
import time
import datetime
import random
import mysql.connector
from Tools.database import DB
from random import randint
from datetime import datetime
from discord.ext import commands
from discord.utils import get
from discord.ext.commands import Bot
from configs import configs


class Commands:
    def __init__(self, client):
        self.client = client
        self.conn = mysql.connector.connect(
            user="root", password="9fr8-PkM;M4+", host="localhost", database="data"
        )
        self.cursor = self.conn.cursor(buffered=True)
        self.MUTE_ROLE = configs["MUTE_ROLE"]
        self.VMUTE_ROLE = configs["VMUTE_ROLE"]
        self.SOFTBAN_ROLE = configs["SOFTBAN_ROLE"]
        self.FOOTER = configs["FOOTER_TEXT"]

    async def main_mute(
        self,
        ctx,
        member:discord.Member,
        author:discord.User=None,
        mute_time:int=0,
        mute_typetime:str=None,
        check_role:bool=True,
        reason:str=None,
        message:bool=True,
    ) -> typing.Union[discord.Embed, bool]:
        client = self.client
        overwrite = discord.PermissionOverwrite(send_messages=False)
        types = [
            "мин",
            "м",
            "m",
            "min",
            "час",
            "ч",
            "h",
            "hour",
            "дней",
            "д",
            "d",
            "day",
            "недель",
            "н",
            "week",
            "w",
            "месяц",
            "м",
            "mounth",
            "m",
        ]

        if (
            mute_typetime == "мин"
            or mute_typetime == "м"
            or mute_typetime == "m"
            or mute_typetime == "min"
        ):
            mute_minutes = mute_time * 60
        elif (
            mute_typetime == "час"
            or mute_typetime == "ч"
            or mute_typetime == "h"
            or mute_typetime == "hour"
        ):
            mute_minutes = mute_time * 60
        elif (
            mute_typetime == "дней"
            or mute_typetime == "д"
            or mute_typetime == "d"
            or mute_typetime == "day"
        ):
            mute_minutes = mute_time * 120 * 12
        elif (
            mute_typetime == "недель"
            or mute_typetime == "н"
            or mute_typetime == "week"
            or mute_typetime == "w"
        ):
            mute_minutes = mute_time * 120 * 12 * 7
        elif (
            mute_typetime == "месяц"
            or mute_typetime == "м"
            or mute_typetime == "mounth"
            or mute_typetime == "m"
        ):
            mute_minutes = mute_time * 120 * 12 * 30
        else:
            mute_minutes = mute_time * 60

        times = time.time()
        times += mute_minutes

        if not reason and mute_typetime not in types:
            reason = mute_typetime

        if member in ctx.guild.members:
            data = DB().sel_user(target=member)

        role = get(ctx.guild.roles, name=self.MUTE_ROLE)
        if not role:
            role = await ctx.guild.create_role(name=self.MUTE_ROLE)

        if check_role:
            if role in member.roles:
                emb = discord.Embed(
                    title="Ошибка!",
                    description=f"**Указаный пользователь уже замьючен!**",
                    colour=discord.Color.green(),
                )
                emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
                emb.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
                return

        await member.add_roles(role)
        for channel in ctx.guild.text_channels:
            await channel.set_permissions(role, overwrite=overwrite)

        cur_lvl = data["lvl"]
        cur_coins = data["coins"] - 1500
        cur_money = data["money"]
        cur_reputation = data["reputation"] - 15
        cur_items = data["items"]
        prison = data["prison"]

        if cur_reputation < -100:
            cur_reputation = -100

        if cur_lvl <= 3:
            cur_money -= 250
        elif cur_lvl > 3 and cur_lvl <= 5:
            cur_money -= 500
        elif cur_lvl > 5:
            cur_money -= 1000

        if cur_money <= -5000:
            prison = True
            cur_items = []
            emb_member = discord.Embed(
                description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**",
                colour=discord.Color.green(),
            )
            emb_member.set_author(
                name=client.user.name, icon_url=client.user.avatar_url
            )
            emb_member.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
            await member.send(embed=emb_member)

        sql = """UPDATE users SET money = %s, coins = %s, reputation = %s, items = %s, prison = %s WHERE user_id = %s AND guild_id = %s"""
        val = (
            cur_money,
            cur_coins,
            cur_reputation,
            json.dumps(cur_items),
            str(prison),
            member.id,
            ctx.guild.id,
        )

        self.cursor.execute(sql, val)
        self.conn.commit()

        if mute_minutes <= 0:
            if message:
                if reason:
                    emb = discord.Embed(
                        description=f"**{member.mention} Был перманентно замьючен по причине {reason}**",
                        colour=discord.Color.green(),
                    )
                    emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                    emb.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
                elif not reason:
                    emb = discord.Embed(
                        description=f"**{member.mention} Был перманентно замьючен**",
                        colour=discord.Color.green(),
                    )
                    emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                    emb.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
        elif mute_minutes != 0:
            if message:
                if reason:
                    emb = discord.Embed(
                        description=f"**{member.mention} Был замьючен по причине {reason} на {mute_time}{mute_typetime}**",
                        colour=discord.Color.green(),
                    )
                    emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                    emb.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
                elif not reason:
                    emb = discord.Embed(
                        description=f"**{member.mention} Был замьючен на {mute_time}{mute_typetime}**",
                        colour=discord.Color.green(),
                    )
                    emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                    emb.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)

        if mute_minutes > 0:
            DB().set_punishment(
                type_punishment="mute",
                time=times,
                member=member,
                role_id=role.id,
                reason=reason,
                author=str(ctx.author),
            )

        if message:
            return emb
        elif not message:
            return True

    async def main_warn(
        self, ctx, member:discord.Member, author:discord.User, reason:str=None
    ) -> discord.Embed:
        client = self.client

        if member in ctx.guild.members:
            data = DB().sel_user(target=member)
        else:
            raise "The guild hasn`t that member {}".format(member.name)

        info = DB().sel_guild(guild=ctx.guild)
        max_warns = int(info["max_warns"])
        cur_lvl = data["lvl"]
        cur_coins = data["coins"]
        cur_money = data["money"]
        cur_warns = data["warns"]
        cur_state_pr = data["prison"]
        cur_reputation = data["reputation"] - 10

        DB().set_warn(
            target=member,
            reason=reason,
            author=str(ctx.author),
            time=str(datetime.today()),
        )

        if cur_lvl <= 3:
            cur_money -= 250
        elif cur_lvl > 3 and cur_lvl <= 5:
            cur_money -= 500
        elif cur_lvl > 5:
            cur_money -= 1000

        if cur_money <= -5000:
            cur_state_pr = True
            emb_member = discord.Embed(
                description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Текущий баланс - {cur_money}**",
                colour=discord.Color.green(),
            )
            emb_member.set_author(
                name=client.user.name, icon_url=client.user.avatar_url
            )
            emb_member.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
            await member.send(embed=emb_member)

        if cur_reputation < -100:
            cur_reputation = -100

        if len(cur_warns) >= 20:
            DB().del_warn([warn for warn in cur_warns if not warn["state"]][0]["id"])

        if len(cur_warns) >= max_warns:
            self.main_mute(
                ctx,
                member=member,
                author=ctx.author,
                mute_time=2,
                mute_typetime="h",
                check_role=False,
                message=False,
            )
            emb_ctx = discord.Embed(
                description=f"**{member.mention} Достиг максимального значения предупреждения и был замючен на 2 часа.**",
                colour=discord.Color.green(),
            )
            emb_ctx.set_author(name=client.user.name, icon_url=client.user.avatar_url)
            emb_ctx.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
        else:
            emb_member = discord.Embed(
                description=f"**Вы были предупреждены {author.mention} по причине {reason}. Предупрежденний `{len(cur_warns)}`, id - `{warn_id}`**",
                colour=discord.Color.green(),
            )
            emb_member.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb_member.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
            await member.send(embed=emb_member)

            emb_ctx = discord.Embed(
                description=f"**Пользователь {member.mention} получил предупреждения по причине {reason}. Количество предупрежденний - `{len(cur_warns)}`, id - `{warn_id}`**",
                colour=discord.Color.green(),
            )
            emb_ctx.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb_ctx.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)

        sql = """UPDATE users SET money = %s, coins = %s, reputation = %s, prison = %s WHERE user_id = %s AND guild_id = %s"""
        val = (cur_money, cur_coins, cur_reputation, str(cur_state_pr))

        self.cursor.execute(sql, val)
        self.conn.commit()

        return emb_ctx
