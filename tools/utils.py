import discord
import datetime
import calendar
import typing
import random
from discord import ext
from tools.exceptions import *


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
            minutes = time * 60 * 60 * 24 * 7 * calendar.mdays[datetime.datetime.utcnow().month]
        elif typetime in years:
            minutes = time * 60 * 60 * 24 * 7 * calendar.mdays[datetime.datetime.utcnow().month] * 12
        else:
            minutes = time
            
        return minutes, time, typetime

    def date_to_time(self, date: list, str_d: str):
        if len(date) != 4:
            return 0

        new_time = datetime.datetime.strptime(str_d, "%H:%M.%d.%m.%Y")
        if new_time < datetime.datetime.utcnow():
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

    async def build_help(self, ctx, prefix, groups):
        exceptions = ("owner", "help", "jishaku")
        emb = discord.Embed(
            title="**Доступные команды:**",
            description=f'Префикс на этом сервере - `{prefix}`. Показаны только те команды которые вы можете выполнить',
            colour=discord.Color.green()
        )
        for soft_cog_name in self.client.cogs:
            if soft_cog_name.lower() not in exceptions:
                cog = self.client.get_cog(soft_cog_name)
                commands = ""
                for command in cog.get_commands():
                    if command.name not in groups:
                        try:
                            if await command.can_run(ctx):
                                commands += f" `{prefix}{command.name}` "
                        except ext.commands.CommandError:
                            pass
                    else:
                        for c in command.commands:
                            try:
                                if await c.can_run(ctx):
                                    commands += f" `{prefix}{command.name} {c.name}` "
                            except ext.commands.CommandError:
                                pass

                if commands != "":
                    emb.add_field(
                        name=f"Категория команд: {soft_cog_name.capitalize()} - {prefix}help {soft_cog_name.lower()}",
                        value=commands,
                        inline=False,
                    )
        emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        emb.set_footer(text=f"Вызвал: {ctx.author.name}", icon_url=ctx.author.avatar_url)
        return emb

    async def global_command_check(self, ctx):
        commands_settings = (await self.client.database.sel_guild(guild=ctx.guild))["commands_settings"]
        if ctx.command.name in commands_settings.keys():
            if not commands_settings[ctx.command.name]["state"]:
                raise CommandOff

            if commands_settings[ctx.command.name]["target_channels"]:
                if ctx.channel.id not in commands_settings[ctx.command.name]["target_channels"]:
                    raise CommandChannelRequired

            if commands_settings[ctx.command.name]["target_roles"]:
                state = False
                for role in ctx.author.roles:
                    if role.id in commands_settings[ctx.command.name]["target_roles"]:
                        state = True

                if not state:
                    raise CommandRoleRequired

            if ctx.channel.id in commands_settings[ctx.command.name]["ignore_channels"]:
                raise CommandChannelIgnored

            for role in ctx.author.roles:
                if role.id in commands_settings[ctx.command.name]["ignore_roles"]:
                    raise CommandRoleIgnored

        return True

    async def end_giveaway(self, giveaway: tuple) -> bool:
        guild = self.client.get_guild(giveaway[1])
        if guild is None:
            await self.client.database.del_giveaway(giveaway[0])
            return False

        channel = guild.get_channel(giveaway[2])
        if channel is None:
            await self.client.database.del_giveaway(giveaway[0])
            return False

        try:
            message = await channel.fetch_message(giveaway[3])
        except discord.errors.NotFound:
            await self.client.database.del_giveaway(giveaway[0])
            return False

        message_reactions = message.reactions
        if "🎉" not in [str(r.emoji) for r in message_reactions]:
            await self.client.database.del_giveaway(giveaway[0])
            return False

        reacted_users = []
        for reaction in message_reactions:
            if str(reaction.emoji) == "🎉":
                reacted_users = await reaction.users().flatten()
                break

        for user in reacted_users:
            if user.bot:
                reacted_users.remove(user)

        winners = []
        for _ in range(giveaway[5]):
            if reacted_users == []:
                break

            winner = random.choice(reacted_users)
            winners.append(winner)
            reacted_users.remove(winner)

        if winners == []:
            winners_str = "Не удалось определыть победителей!"
        else:
            winners_str = ", ".join([u.mention for u in winners])
        message.embeds[0].colour = discord.Color.green()
        message.embeds[0].description = f"**Розыгрыш окончен!**\n\nПобедители: {winners_str}\nОрганизатор: {guild.get_member(giveaway[4])}\nПриз:\n>>> {giveaway[8]}"
        await message.edit(content="⏰ Розыгрыш окончен!", embed=message.embeds[0])
        await channel.send(
            f"**Розыгрыш** {message.jump_url} **окончен**\n**Победители:** {winners_str}"
        )
        await self.client.database.del_giveaway(giveaway[0])
        return True
