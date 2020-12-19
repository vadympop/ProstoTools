class Utils:
    def time_to_num(self, str_time: str):
        if str_time is not None:
            time = int("".join(char for char in str_time if not char.isalpha()))
            typetime = str(str_time.replace(str(time), ""))
        else:
            typetime = None
            time = 0

        minutes = [
            "m",
            "min",
            "mins",
            "minute",
            "minutes",
            "м",
            "мин",
            "минута",
            "минуту",
            "минуты",
            "минут",
        ]
        hours = ["h", "hour", "hours", "ч", "час", "часа", "часов"]
        days = ["d", "day", "days", "д", "день", "дня", "дней"]
        weeks = [
            "w",
            "week",
            "weeks",
            "н",
            "нед",
            "неделя",
            "недели",
            "недель",
            "неделю",
        ]
        monthes = [
            "m",
            "month",
            "monthes",
            "mo",
            "mos",
            "months",
            "мес",
            "месяц",
            "месяца",
            "месяцев",
        ]
        years = ["y", "year", "years", "г", "год", "года", "лет"]
        if typetime in minutes:
            minutes = time * 60
        elif typetime in hours:
            minutes = time * 60 * 60
        elif typetime in days:
            minutes = time * 60 * 60 * 12
        elif typetime in weeks:
            minutes = time * 60 * 60 * 12 * 7
        elif typetime in monthes:
            minutes = time * 60 * 60 * 12 * 7 * 31
        elif typetime in years:
            minutes = time * 60 * 60 * 12 * 7 * 31 * 12
        else:
            minutes = time
            
        return minutes, time, typetime
