import discord
import colorama
import datetime
import json
import jinja2
import sys
from discord.ext import commands
from discord.utils import get
from discord.ext.commands import Bot
from Tools.database import DB
from configs import configs
from colorama import *

init()


class Errors(commands.Cog, name="Errors"):
    def __init__(self, client):
        self.client = client
        self.FOOTER = configs["FOOTER_TEXT"]

    def dump(self, filename, filecontent):
        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(filecontent)

    def load(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        PREFIX = DB().sel_guild(guild=ctx.guild)["prefix"]
        now_date = str(datetime.datetime.today())[:-16]
        filename = f"./Data/Logs/log-{now_date}.txt"
        space = ""
        log_error = f"\n\n=============================================================\nВремя: {str(datetime.datetime.today())}\n\nОшибка:\n{error}\n============================================================="

        try:
            log = self.load(filename)
        except:
            self.dump(filename, space)
            log = self.load(filename)

        if log == "":
            self.dump(filename, log_error)
        else:
            log_error = log + log_error
            self.dump(filename, log_error)

        if isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.message.add_reaction("❌")
            retry_after = error.retry_after
            if retry_after < 60:
                emb = discord.Embed(
                    title="Ошибка!",
                    description=f"**Кулдавн в команде еще не прошёл! Подождите {int(retry_after)} секунд**",
                    colour=discord.Color.green(),
                )
            elif retry_after > 60 and retry_after < 1800:
                emb = discord.Embed(
                    title="Ошибка!",
                    description=f"**Кулдавн в команде еще не прошёл! Подождите {int(retry_after / 60)} минут**",
                    colour=discord.Color.green(),
                )
            elif retry_after > 1800:
                emb = discord.Embed(
                    title="Ошибка!",
                    description=f"**Кулдавн в команде еще не прошёл! Подождите {int(retry_after / 60 / 24)} часа**",
                    colour=discord.Color.green(),
                )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.message.add_reaction("❌")
            emb = discord.Embed(
                title="Ошибка!",
                description=f"**Вы не указали аргумент. Укажити аргумент - {error.param.name} к указаной команде!**\n\n{ctx.command.help.format(Prefix=PREFIX)}",
                colour=discord.Color.green(),
            )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
        elif isinstance(error, commands.errors.CommandNotFound):
            pass
        elif isinstance(error, commands.errors.NotOwner):
            emb = discord.Embed(
                title="Ошибка!",
                description="**Вы неявляетесь создателем бота! Эта команда только для создателей!**",
                colour=discord.Color.green(),
            )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
        elif isinstance(error, commands.errors.MissingPermissions):
            emb = discord.Embed(
                title="Ошибка!",
                description="**У вас не достаточно прав! Для этой команды нужны права администратора**",
                colour=discord.Color.green(),
            )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
        elif isinstance(error, commands.errors.BadArgument):
            emb = discord.Embed(
                title="Ошибка!",
                description=f"**Указан не правильный аргумент!**\n\n{ctx.command.help.format(Prefix=PREFIX)}",
                colour=discord.Color.green(),
            )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
        elif isinstance(error, commands.errors.BotMissingPermissions):
            owner = get(ctx.guild.members, id=ctx.guild.owner_id)
            emb_err = discord.Embed(
                title="Ошибка!",
                description=f"У бота отсутствуют права: {' '.join(error.missing_perms)}\nВыдайте их ему для полного функционирования бота",
                colour=discord.Color.green(),
            )
            emb_err.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb_err.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await owner.send(embed=emb_err)
        elif isinstance(error, jinja2.exceptions.TemplateError):
            emb = discord.Embed(
                title="Ошибка!", description=error, colour=discord.Color.green()
            )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
        elif isinstance(error, commands.errors.CheckFailure):
            pass
        elif isinstance(error, jinja2.exceptions.UndefinedError):
            emb = discord.Embed(
                title="Ошибка!", description=error, colour=discord.Color.green()
            )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
        elif isinstance(error, commands.errors.MemberNotFound):
            emb = discord.Embed(
                title="Ошибка!",
                description="**Указаный пользователь не найден!**",
                colour=discord.Color.green(),
            )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
        # elif isinstance(error, commands.errors.CommandInvokeError):
        # 	pass
        else:
            raise error


def setup(client):
    client.add_cog(Errors(client))
