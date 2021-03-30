import re
import typing
import pytz

from dateutil.relativedelta import relativedelta

DURATION_REGEX = re.compile(
    r"((?P<years>\d+?) ?(years|year|Y|y|год|г|Г|лет|годов) ?)?"
    r"((?P<months>\d+?) ?(months|month|mo|Mo|мес|месяц|месяцов) ?)?"
    r"((?P<weeks>\d+?) ?(weeks|week|W|w|н|Н|нед|неделя|недель) ?)?"
    r"((?P<days>\d+?) ?(days|day|D|d|д|Д|дней|день) ?)?"
    r"((?P<hours>\d+?) ?(hours|hour|H|h|ч|час|Ч|часов) ?)?"
    r"((?P<minutes>\d+?) ?(minutes|minute|m|м|М|мин|минут|минута) ?)?"
    r"((?P<seconds>\d+?) ?(seconds|second|S|s|с|С|сек|секунд))?"
)


def parse_duration_string(duration: str) -> typing.Optional[relativedelta]:
    match = DURATION_REGEX.fullmatch(duration)
    if not match:
        return None

    duration_dict = {unit: int(amount) for unit, amount in match.groupdict(default=0).items()}
    delta = relativedelta(**duration_dict)

    return delta


def get_timezone_obj(timezone: str):
    if timezone is None:
        return pytz.timezone("utc")

    try:
        return pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        return pytz.timezone("utc")