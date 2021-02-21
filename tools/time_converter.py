import re
from dateutil.relativedelta import relativedelta
from discord.ext import commands


class TimeConverter(commands.Converter):
    duration_parser = re.compile(
        r"((?P<years>\d+?) ?(years|year|Y|y|год|г|Г|лет|годов) ?)?"
        r"((?P<months>\d+?) ?(months|month|mo|Mo|мес|месяц|месяцов) ?)?"
        r"((?P<weeks>\d+?) ?(weeks|week|W|w|н|Н|нед|неделя|недель) ?)?"
        r"((?P<days>\d+?) ?(days|day|D|d|д|Д|дней|день) ?)?"
        r"((?P<hours>\d+?) ?(hours|hour|H|h|ч|час|Ч|часов) ?)?"
        r"((?P<minutes>\d+?) ?(minutes|minute|m|м|М|мин|минут|минута) ?)?"
        r"((?P<seconds>\d+?) ?(seconds|second|S|s|с|С|сек|секунд))?"
    )

    async def convert(self, ctx: commands.Context, duration: str) -> relativedelta:
        match = self.duration_parser.fullmatch(duration)
        if not match:
            raise commands.BadArgument(f"`{duration}` is not a valid duration string.")

        duration_dict = {unit: int(amount) for unit, amount in match.groupdict(default=0).items()}
        return relativedelta(**duration_dict)