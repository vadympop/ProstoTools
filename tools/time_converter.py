import re
from dateutil.relativedelta import relativedelta
from discord.ext import commands


class TimeConverter(commands.Converter):
    """Convert duration strings into dateutil.relativedelta.relativedelta objects."""

    duration_parser = re.compile(
        r"((?P<years>\d+?) ?(years|year|Y|y) ?)?"
        r"((?P<months>\d+?) ?(months|month|mo|Mo) ?)?"
        r"((?P<weeks>\d+?) ?(weeks|week|W|w) ?)?"
        r"((?P<days>\d+?) ?(days|day|D|d) ?)?"
        r"((?P<hours>\d+?) ?(hours|hour|H|h) ?)?"
        r"((?P<minutes>\d+?) ?(minutes|minute|m) ?)?"
        r"((?P<seconds>\d+?) ?(seconds|second|S|s))?"
    )

    async def convert(self, ctx: commands.Context, duration: str) -> relativedelta:
        """
        Converts a `duration` string to a relativedelta object.
        The converter supports the following symbols for each unit of time:
        - years: `Y`, `y`, `year`, `years`
        - months: `m`, `month`, `months`
        - weeks: `w`, `W`, `week`, `weeks`
        - days: `d`, `D`, `day`, `days`
        - hours: `H`, `h`, `hour`, `hours`
        - minutes: `M`, `minute`, `minutes`
        - seconds: `S`, `s`, `second`, `seconds`
        The units need to be provided in descending order of magnitude.
        """
        match = self.duration_parser.fullmatch(duration)
        if not match:
            raise commands.BadArgument(f"`{duration}` is not a valid duration string.")

        duration_dict = {unit: int(amount) for unit, amount in match.groupdict(default=0).items()}
        print(relativedelta(**duration_dict).normalized())
        return relativedelta(**duration_dict)