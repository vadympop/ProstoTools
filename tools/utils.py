import discord
import datetime
import calendar


class Utils:
    def __init__(self, client):
        self.client = client
        self.FOOTER = self.client.config.FOOTER_TEXT

    def time_to_num(self, str_time: str):
        if str_time is not None:
            try:
                time = int("".join(char for char in list(str_time) if char.isdigit()))
                typetime = str(str_time.replace(str(time), ""))
            except ValueError:
                return [0, 0]
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
            minutes = time * 60 * 60 * 24
        elif typetime in weeks:
            minutes = time * 60 * 60 * 24 * 7
        elif typetime in monthes:
            minutes = time * 60 * 60 * 24 * 7 * calendar.mdays[datetime.datetime.now().month]
        elif typetime in years:
            minutes = time * 60 * 60 * 24 * 7 * calendar.mdays[datetime.datetime.now().month] * 12
        else:
            minutes = time
            
        return minutes, time, typetime

    def date_to_time(self, date: list, str_d: str):
        if len(date) != 4:
            return 0

        new_time = datetime.datetime.strptime(str_d, "%H:%M.%d.%m.%Y")
        if new_time < datetime.datetime.now():
            return 0
        return ((new_time-datetime.datetime(year=1970, month=1, day=1))-datetime.timedelta(hours=2)).total_seconds()

    async def create_error_embed(self, ctx, error_msg: str, bold: bool = True):
        emb = discord.Embed(
            title="Ошибка!", description=f"**{error_msg}**" if bold else error_msg, colour=discord.Color.green()
        )
        emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        try:
            await ctx.message.add_reaction("❌")
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass
        return emb

    async def build_help(self, ctx, prefix, groups, moder_roles):
        state = False
        exceptions = ("owner", "help", "jishaku")
        emb = discord.Embed(
            title="**Доступные команды:**",
            description=f'Префикс на этом сервере - `{prefix}`, если надо ввести названия чего-либо с пробелом, укажите его в двойных кавычках',
            colour=discord.Color.green()
        )
        for soft_cog_name in self.client.cogs:
            if soft_cog_name.lower() not in exceptions:
                cog = self.client.get_cog(soft_cog_name)
                commands = ""
                for command in cog.get_commands():
                    if command.name not in groups:
                        if not command.hidden:
                            if command.brief != "True":
                                commands += f" `{prefix}{command.name}` "
                            else:
                                for role_id in moder_roles:
                                    role = ctx.guild.get_role(role_id)
                                    if role in ctx.author.roles:
                                        state = True
                                        break

                                if state or ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
                                    commands += f" `{prefix}{command.name}` "
                        else:
                            commands += f" `{prefix}{command.name}` "
                    else:
                        for c in command.commands:
                            if not c.hidden:
                                if c.brief != "True":
                                    commands += f" `{prefix}{command.name} {c.name}` "
                                else:
                                    for role_id in moder_roles:
                                        role = ctx.guild.get_role(role_id)
                                        if role in ctx.author.roles:
                                            state = True
                                            break

                                    if state or ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
                                        commands += f" `{prefix}{command.name} {c.name}` "
                            else:
                                if ctx.author.guild_permissions.administrator:
                                    commands += f" `{prefix}{command.name} {c.name}` "

                if commands != "":
                    emb.add_field(
                        name=f"Категория команд: {soft_cog_name.capitalize()} - {prefix}help {soft_cog_name.lower()}",
                        value=commands,
                        inline=False,
                    )
        emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        emb.set_footer(text=f"Вызвал: {ctx.author.name}", icon_url=ctx.author.avatar_url)
        return emb
