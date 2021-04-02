import datetime
import dateutil.parser
import dateutil.tz
import typing
import discord

from core.exceptions import *
from core.utils.time_utils import parse_duration_string, get_timezone_obj
from dateutil.relativedelta import relativedelta
from discord.ext import commands


class DurationDelta(commands.Converter):
    async def convert(self, ctx: commands.Context, duration: str) -> relativedelta:
        if not (delta := parse_duration_string(duration)):
            raise BadTimeArgument

        return delta


class Duration(DurationDelta):
    async def convert(self, ctx: commands.Context, duration: str) -> datetime.datetime:
        delta = await super().convert(ctx, duration)
        now = await ctx.bot.utils.get_guild_time(ctx.guild)

        try:
            new_time = now + delta
        except (ValueError, OverflowError):
            raise BadTimeArgument

        timezone = get_timezone_obj(await ctx.bot.database.get_guild_timezone(ctx.guild))
        new_time.astimezone(tz=timezone)
        new_time.replace(tzinfo=timezone)
        return new_time


class ISODateTime(commands.Converter):
    async def convert(self, ctx: commands.Context, datetime_string: str) -> datetime.datetime:
        try:
            dt = dateutil.parser.isoparse(datetime_string)
        except ValueError:
            raise BadTimeArgument

        timezone = get_timezone_obj(await ctx.bot.database.get_guild_timezone(ctx.guild))
        dt.astimezone(tz=timezone)
        dt.replace(tzinfo=timezone)
        return dt


class TargetUser(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: typing.Union[str, int]) -> discord.Member:
        user = await commands.MemberConverter().convert(ctx, argument)
        if ctx.author == ctx.guild.owner:
            return user

        if user.top_role >= ctx.me.top_role:
            raise RoleHigherThanMy

        if user.top_role >= ctx.author.top_role:
            raise RoleHigherThanYour

        if user == ctx.author:
            raise TakeActionWithYourself

        if user == ctx.guild.me:
            raise TakeActionWithMe

        if user == ctx.guild.owner:
            raise TakeActionWithOwner
        return user


class GuildConverter(commands.IDConverter):
    async def convert(self, ctx: commands.Context, argument):
        match = self._get_id_match(argument)
        if not match:
            guild = discord.utils.get(ctx.bot.guilds, name=argument)
        else:
            guild_id = int(match.group(1))
            guild = ctx.bot.get_guild(guild_id) or await ctx.bot.fetch_guild(guild_id)

        if not guild:
            raise commands.BadArgument(f"Guild {argument} not found")
        return guild


class ColorConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument) -> int:
        try:
            return int(hex(int(argument.replace("#", ""), 16)), 0)
        except ValueError:
            raise commands.BadColourArgument(argument)


BlacklistEntity = typing.Union[commands.MemberConverter, GuildConverter]
Expiry = typing.Union[Duration, ISODateTime]