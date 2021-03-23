import datetime
import dateutil.parser
import dateutil.tz
import typing

from tools.utils.time_utils import parse_duration_string
from dateutil.relativedelta import relativedelta
from discord.ext import commands


class DurationDelta(commands.Converter):
    async def convert(self, ctx: commands.Context, duration: str) -> relativedelta:
        if not (delta := parse_duration_string(duration)):
            raise commands.BadArgument(f"`{duration}` is not a valid duration string.")

        return delta


class Duration(DurationDelta):
    async def convert(self, ctx: commands.Context, duration: str) -> datetime.datetime:
        delta = await super().convert(ctx, duration)
        now = datetime.datetime.now()

        try:
            return now + delta
        except (ValueError, OverflowError):
            raise commands.BadArgument(
                f"`{duration}` results in a datetime outside the supported range."
            )


class ISODateTime(commands.Converter):
    async def convert(self, ctx: commands.Context, datetime_string: str) -> datetime.datetime:
        try:
            dt = dateutil.parser.isoparse(datetime_string)
        except ValueError:
            raise commands.BadArgument(f"`{datetime_string}` is not a valid ISO-8601 datetime string")

        return dt


Expiry = typing.Union[Duration, ISODateTime]