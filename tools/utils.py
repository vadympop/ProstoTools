import discord
import datetime
import calendar


class Utils:
    def __init__(self, client):
        self.client = client
        self.FOOTER = self.client.config.FOOTER_TEXT
    
    def time_to_num(self, str_time: str):
        if str_time is not None:
            time = int("".join(char for char in list(str_time) if char.isdigit()))
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

        now = datetime.datetime.now()
        if int(date[1]) < now.day:
            return 0

        if int(date[2]) < now.month:
            return 0

        if int(date[3]) < now.year:
            return 0

        splited_time = date[0].split(":")
        if len(splited_time) != 2:
            return 0

        if int(splited_time[0]) < now.hour:
            return 0

        new_time = datetime.datetime.strptime(str_d, "%H:%M.%d.%m.%Y")
        return ((new_time-datetime.datetime(year=1970, month=1, day=1))-datetime.timedelta(hours=2)).total_seconds()

    async def create_error_embed(self, ctx, error_msg: str, bold: bool = True):
        emb = discord.Embed(title="Ошибка!", description=f"**{error_msg}**" if bold else error_msg, colour=discord.Color.green())
        emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.message.add_reaction("❌")
        return emb

    async def build_help(self, ctx, prefix, groups, moder_roles):
        state = False
        group_name = ""
        locks = {
            "Different": 6,
            "Economy": 5,
            "Games": 7,
            "Moderate": 6,
            "Settings": 3,
            "Utils": 5,
            "Works": 7,
            "Clans": 3,
            "EconomyBuyCmd": 3,
            "FunOther": 5,
            "FunEditImage": 6,
            "FunRandomImage": 7
        }
        exceptions = ["Help", "Loops", "Events", "Owner", "Errors"]

        def add_command_loop(command, commands, count, group_name):
            try:
                for c in command.commands:
                    if not c.hidden:
                        if command.brief != "True":
                            commands += f" {prefix}{c.name} "
                            count += 1
                            group_name = command.name
                        else:
                            state = False
                            for role_id in moder_roles:
                                if ctx.guild.get_role(role_id) in ctx.author.roles:
                                    state = True
                                    break

                            if state or ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
                                commands += f" {prefix}{c.name} "
                                count += 1
                                group_name = command.name
                    else:
                        if ctx.author.guild_permissions.administrator:
                            commands += f" {prefix}{c.name} "
                            count += 1
                            group_name = command.name

                    if count >= locks[soft_cog_name]:
                        count = 0
                        commands += "`\n`"
            except:
                commands += f" {prefix}{command.name} "

            return [commands, count, group_name]

        emb = discord.Embed(
            title="**Доступние команды:**",
            description=f'**Префикс на этом сервере - **`{prefix}`**, если команды после двое-точия значит их надо использовать как групу, пример: "В хелп - група: команда, надо писать - `[Префикс на сервере]група команда`", если надо ввести названия чего-либо с пробелом, укажите его в двойных кавычках**',
            colour=discord.Color.green()
        )
        for soft_cog_name in self.client.cogs:
            if soft_cog_name in exceptions:
                continue
            else:
                cog = self.client.get_cog(soft_cog_name)
                commands = ""
                count = 0
                for command in cog.get_commands():
                    if not command.hidden:
                        if command.brief != "True":
                            commands, count, group_name = add_command_loop(
                                command, commands, count, group_name
                            )
                            count += 1
                            if count >= locks[soft_cog_name]:
                                count = 0
                                commands += "`\n`"
                        else:
                            for role_id in moder_roles:
                                role = ctx.guild.get_role(role_id)
                                if role in ctx.author.roles:
                                    state = True
                                    break

                            if state or ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator:
                                commands, count, group_name = add_command_loop(
                                    command, commands, count, group_name
                                )
                                count += 1
                                if count >= locks[soft_cog_name]:
                                    count = 0
                                    commands += "`\n`"
                    else:
                        if ctx.author.guild_permissions.administrator:
                            commands, count, group_name = add_command_loop(
                                command, commands, count, group_name
                            )
                            count += 1
                            if count >= locks[soft_cog_name]:
                                count = 0
                                commands += "`\n`"
                if commands != "":
                    if soft_cog_name.lower() in groups:
                        value = f"` {group_name.lower()}: {commands}`"
                    else:
                        value = f"`{commands}`"

                    emb.add_field(
                        name=f"Категория команд: {soft_cog_name.capitalize()} - {prefix}help {soft_cog_name.lower()}",
                        value=value,
                        inline=False,
                    )
        emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        emb.set_footer(text=f"Вызвал: {ctx.author.name}", icon_url=ctx.author.avatar_url)
        return emb
