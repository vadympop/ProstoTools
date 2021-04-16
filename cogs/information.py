import discord
import datetime
import sanic
import psutil as ps
import humanize

from core.services.database.models import BotStat
from core.bases.cog_base import BaseCog
from discord.ext import commands


class Information(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.HELP_SERVER = self.client.config.HELP_SERVER
        humanize.i18n.activate("ru_RU")

    def _get_bio(self, data):
        if data.bio == "":
            return ""
        else:
            return f"""\n\n**Краткая информация о пользователе:**\n{data.bio}\n\n"""

    def _get_activity(self, activity: discord.Activity):
        if activity is None:
            return ""

        if isinstance(activity, discord.Game):
            return f"\n**Пользовательский статус:** {activity.name}"

        if activity.emoji is not None and activity.emoji.is_unicode_emoji():
            activity_info = f"\n**Пользовательский статус:** {activity.emoji} {activity.name}"
        else:
            if activity.emoji in self.client.emojis:
                activity_info = f"\n**Пользовательский статус:** {activity.emoji} {activity.name}"
            else:
                activity_info = f"\n**Пользовательский статус:** {activity.name}"

        return activity_info

    @commands.command(
        aliases=["userinfo", "user", "u"],
        name="user-info",
        description="Показывает информацию указанного учасника",
        usage="user-info |@Участник|",
        help="**Примеры использования:**\n1. {Prefix}user-info @Участник\n2. {Prefix}user-info 660110922865704980\n3. {Prefix}user-info\n\n**Пример 1:** Покажет информацию о упомянутом участнике\n**Пример 2:** Покажет информацию о участнике с указаным id\n**Пример 3:** Покажет информацию о вас",
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def userinfo(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        statuses = {
            "dnd": "<:dnd:730391353929760870> - Не беспокоить",
            "online": "<:online:730393440046809108> - В сети",
            "offline": "<:offline:730392846573633626> - Не в сети",
            "idle": "<:sleep:730390502972850256> - Отошёл",
        }
        joined_at = None
        if ctx.guild is not None:
            joined_at = datetime.datetime.strftime(member.joined_at, "%d %B %Y %X")

        created_at = datetime.datetime.strftime(member.created_at, "%d %B %Y %X")

        if not member.bot:
            data = None
            if ctx.guild is not None:
                data = await self.client.database.sel_user(target=member)

            description = (f"""
{self._get_bio(data) if data else ''}**Имя пользователя:** {member}
{f"** Статус:** {statuses[member.status.name]}{self._get_activity(member.activity)}" if ctx.guild is not None else ""}
**Id пользователя:** {member.id}
**Акаунт создан:** {created_at}
{f"**Присоеденился:** {joined_at}" if joined_at is not None else ""}
""")

        else:
            description = f"""
**Имя бота:** {member}
{f"** Статус:** {statuses[member.status.name]}{self._get_activity(member.activity)}" if ctx.guild is not None else ""}
**Id бота:** {member.id}
**Акаунт создан:** {created_at}
{f"**Присоеденился:** {joined_at}" if joined_at is not None else ""}
"""

        emb = discord.Embed(
            title=f"Информация о пользователе - {member}", colour=discord.Color.green()
        )
        emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        emb.set_thumbnail(url=member.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        emb.add_field(
            name="Основная информация",
            value=description,
            inline=False,
        )
        await ctx.send(embed=emb)

    @commands.command(
        name="info-bot",
        aliases=["botinfo", "infobot", "bot-info", "about", "bot"],
        usage="info-bot",
        description="Подробная информация о боте",
        help="**Примеры использования:**\n1. {Prefix}info-bot\n2. {Prefix}info-bot system\n\n**Пример 1:** Покажет информацию обо мне\n**Пример 2:** Покажет информацию о моей системе",
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def bot(self, ctx, action: str = None):
        if action != "system":
            links = [
                "[Приглашение Бота](https://discord.com/api/oauth2/authorize?client_id=700767394154414142&permissions=268954870&scope=bot)",
                f"[Сервер поддержки]({self.HELP_SERVER})",
                "[Patreon](https://www.patreon.com/join/prostotools)",
                "[API](https://api.prosto-tools.ml/)",
                "[Документация](https://docs.prosto-tools.ml/)",
                "[SDC](https://bots.server-discord.com/700767394154414142)",
                "[Boticord](https://boticord.top/bot/pt)",
                "[TBL](https://top-bots.xyz/bot/700767394154414142)",
                "[TopBots](https://bots.topcord.ru/bots/700767394154414142)",
            ]
            commands_count = BotStat.objects.filter(entity="all commands").order_by("-count")[0].count
            embed1 = discord.Embed(
                title=f"{self.client.user.name}#{self.client.user.discriminator}",
                description=f"Информация о боте **{self.client.user.name}**.\nМного-функциональный бот со своей экономикой, кланами и системой модерации!",
                color=discord.Color.green(),
            )
            embed1.add_field(
                name="Создатель бота:", value="Vython.lui#9339", inline=False
            )
            embed1.add_field(
                name="Проект был создан с помощью:",
                value=f"discord.py, sanic\ndiscord.py: {discord.__version__}, sanic: {sanic.__version__}",
                inline=False,
            )
            embed1.add_field(
                name="Статистика:",
                value=f"Участников: {len(self.client.users)}, Серверов: {len(self.client.guilds)}, Шардов: {self.client.shard_count}\nОбработано команд: {commands_count}",
                inline=False,
            )
            embed1.add_field(
                name="Бот запущен:",
                value=humanize.naturaltime(
                    datetime.datetime.utcnow() - self.client.launched_at,
                ).capitalize(),
                inline=False
            )
            embed1.add_field(
                name="Полезные ссылки",
                value="\n".join(links),
                inline=False,
            )
            embed1.set_thumbnail(url=self.client.user.avatar_url)
            embed1.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=embed1)
        else:
            mem = ps.virtual_memory()
            ping = self.client.latency

            ping_emoji = "🟩🔳🔳🔳🔳"
            ping_list = [
                {"ping": 0.00000000000000000, "emoji": "🟩🔳🔳🔳🔳"},
                {"ping": 0.10000000000000000, "emoji": "🟧🟩🔳🔳🔳"},
                {"ping": 0.15000000000000000, "emoji": "🟥🟧🟩🔳🔳"},
                {"ping": 0.20000000000000000, "emoji": "🟥🟥🟧🟩🔳"},
                {"ping": 0.25000000000000000, "emoji": "🟥🟥🟥🟧🟩"},
                {"ping": 0.30000000000000000, "emoji": "🟥🟥🟥🟥🟧"},
                {"ping": 0.35000000000000000, "emoji": "🟥🟥🟥🟥🟥"},
            ]
            for ping_one in ping_list:
                if ping <= ping_one["ping"]:
                    ping_emoji = ping_one["emoji"]
                    break

            embed2 = discord.Embed(title="Статистика Бота", color=discord.Color.green())
            embed2.add_field(
                name="Использование CPU",
                value=f"В настоящее время используется: {ps.cpu_percent()}%",
                inline=True,
            )
            embed2.add_field(
                name="Использование RAM",
                value=f'Доступно: {humanize.naturalsize(mem.available)}\nИспользуется: {humanize.naturalsize(mem.used)} ({mem.percent}%)\nВсего: {humanize.naturalsize(mem.total)}',
                inline=True,
            )
            embed2.add_field(
                name="Пинг Бота",
                value=f"Пинг: {ping * 1000:.0f}ms\n`{ping_emoji}`",
                inline=True,
            )

            for disk in ps.disk_partitions():
                usage = ps.disk_usage(disk.mountpoint)
                embed2.add_field(name="‎‎‎‎", value=f"```{disk.device}```", inline=False)
                embed2.add_field(
                    name="Всего на диске",
                    value=humanize.naturalsize(usage.total),
                    inline=True,
                )
                embed2.add_field(
                    name="Свободное место на диске",
                    value=humanize.naturalsize(usage.free),
                    inline=True,
                )
                embed2.add_field(
                    name="Используемое дисковое пространство",
                    value=humanize.naturalsize(usage.used),
                    inline=True,
                )
            await ctx.send(embed=embed2)

    @commands.command(
        description="Отправляет ссылку на приглашения бота на сервер",
        usage="invite",
        help="**Примеры использования:**\n1. {Prefix}invite\n\n**Пример 1:** Отправит приглашения на меня",
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def invite(self, ctx):
        links = [
            "[Приглашение Бота](https://discord.com/api/oauth2/authorize?client_id=700767394154414142&permissions=268954870&scope=bot)",
            f"[Сервер поддержки]({self.HELP_SERVER})",
            "[Patreon](https://www.patreon.com/join/prostotools)",
            "[API](https://api.prosto-tools.ml/)",
            "[Документация](https://docs.prosto-tools.ml/)",
            "[SDC](https://bots.server-discord.com/700767394154414142)",
            "[Boticord](https://boticord.top/bot/pt)",
            "[TBL](https://top-bots.xyz/bot/700767394154414142)",
            "[TopBots](https://bots.topcord.ru/bots/700767394154414142)",
        ]
        emb = discord.Embed(colour=discord.Color.green())
        emb.add_field(
            name="Полезные ссылки",
            value="\n".join(links),
        )
        emb.set_thumbnail(url=self.client.user.avatar_url)
        await ctx.send(embed=emb)

    @commands.command(
        aliases=["server", "serverinfo", "guild", "guildinfo", "guild-info"],
        name="server-info",
        description="Показывает информацию о сервере",
        usage="server-info",
        help="**Примеры использования:**\n1. {Prefix}server-info\n\n**Пример 1:** Покажет информацию о сервере",
    )
    @commands.guild_only()
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def serverinfo(self, ctx):
        created_at = datetime.datetime.strftime(ctx.guild.created_at, "%d %B %Y %X")
        verifications = {
            "none": ":white_circle: — Нет верификации",
            "low": ":green_circle: — Маленькая верификация",
            "medium": ":yellow_circle: — Средняя верификация",
            "high": ":orange_circle: — Большая верификация",
            "extreme": ":red_circle: - Наивысшая верификация",
        }
        regions = {
            "us_west": ":flag_us: — Запад США",
            "us_east": ":flag_us: — Восток США",
            "us_central": ":flag_us: — Центральный офис США",
            "us_south": ":flag_us: — Юг США",
            "sydney": ":flag_au: — Сидней",
            "eu_west": ":flag_eu: — Западная Европа",
            "eu_east": ":flag_eu: — Восточная Европа",
            "eu_central": ":flag_eu: — Центральная Европа",
            "singapore": ":flag_sg: — Сингапур",
            "russia": ":flag_ru: — Россия",
            "southafrica": ":flag_za:  — Южная Африка",
            "japan": ":flag_jp: — Япония",
            "brazil": ":flag_br: — Бразилия",
            "india": ":flag_in: — Индия",
            "hongkong": ":flag_hk: — Гонконг",
            "europe": ":flag_eu: — Европа"
        }

        dnd = len([
            str(member.id)
            for member in ctx.guild.members
            if member.status.name == "dnd"
        ])
        sleep = len([
            str(member.id)
            for member in ctx.guild.members
            if member.status.name == "idle"
        ])
        online = len([
            str(member.id)
            for member in ctx.guild.members
            if member.status.name == "online"
        ])
        offline = len([
            str(member.id)
            for member in ctx.guild.members
            if member.status.name == "offline"
        ])
        bots = len([str(member.id) for member in ctx.guild.members if member.bot])

        emb = discord.Embed(
            title="Информация о вашем сервере", colour=discord.Color.green()
        )

        emb.add_field(
            name=f"Основная информация",
            value=f"**Название сервера:** {ctx.guild.name}\n**Id сервера:** {ctx.guild.id}\n**Регион сервера:** {regions[ctx.guild.region.name]}\n**Уровень верификации:** {verifications[ctx.guild.verification_level.name]}\n**Владелец сервера:** {ctx.guild.owner}\n**Создан:** {created_at}",
            inline=False,
        )
        emb.add_field(
            name="Статистика",
            value=f"**<:channels:730400768049414144> Всего каналов:** {len(ctx.guild.channels)}\n**<:text_channel:730396561326211103> Текстовых каналов:** {len(ctx.guild.text_channels)}\n**<:voice_channel:730399079418429561> Голосовых каналов:** {len(ctx.guild.voice_channels)}\n**<:category:730399838897963038> Категорий:** {len(ctx.guild.categories)}\n**<:role:730396229220958258> Количество ролей:** {len(ctx.guild.roles)}",
            inline=False,
        )
        emb.add_field(
            name="Участники",
            value=f"**:baby: Общее количество участников:** {ctx.guild.member_count}\n**<:bot:731819847905837066> Боты:** {bots}\n**<:sleep:730390502972850256> Отошли:** {sleep}\n**<:dnd:730391353929760870> Не беспокоить:** {dnd}\n**<:offline:730392846573633626> Не в сети:** {offline}\n**<:online:730393440046809108> В сети:** {online}",
            inline=False,
        )

        emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)

    @commands.command(
        aliases=["inviteinfo"],
        name="invite-info",
        description="Показывает информацию о приглашении",
        usage="invite-info [Код приглашения]",
        help="**Примеры использования:**\n1. {Prefix}invite-info aGeFrt46\n\n**Пример 1:** Покажет информацию о приглашении с указаным кодом",
    )
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def invite_info(self, ctx, invite_code: str):
        async with ctx.typing():
            invites = await ctx.guild.invites()
            if invite_code not in [i.code for i in invites]:
                emb = await self.client.utils.create_error_embed(
                    ctx, "Я не смог найти указанное приглашения"
                )
                await ctx.send(embed=emb)
                return

            for invite in invites:
                if invite.code == invite_code:
                    max_age = "\nБесконечный: Да" if invite.max_age == 0 else f"\nБесконечный: Нет\nВремени до окончания: {datetime.timedelta(seconds=invite.max_age)}"
                    description = f"""[Ссылка на приглашения]({invite.url})
Временное членство: {"Да" if invite.temporary else "Нет"}
Использований: {invite.uses if invite.uses is not None else 0}
Максимальное количество использований: {invite.max_uses if invite.max_uses != 0 else "Не указано"}
Канал: `#{invite.channel.name}`{max_age}
Создан: `{invite.created_at.strftime("%d %B %Y %X")}`
"""
                    emb = discord.Embed(
                        title=f"Информация о приглашении - `{invite.code}`",
                        description=description,
                        colour=discord.Color.green()
                    )
                    emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
                    emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
                    await ctx.send(embed=emb)
                    break

    @commands.command(
        name="c-help",
        aliases=["chelp"],
        description="Помощь по кастомным командам",
        usage="c-help",
        help="**Примеры использования:**\n1. {Prefix}c-help\n\n**Пример 1:** Показывает помощь по кастомным командам",
    )
    @commands.guild_only()
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def c_help(self, ctx):
        custom_commands = (await self.client.database.sel_guild(guild=ctx.guild)).custom_commands
        commands = ("\n".join([
            f"`{command['name']}` - {command['description']}"
            if "description" in command.keys()
            else f"`{command['name']}` - Не указано"
            for command in custom_commands
        ]) if custom_commands != [] else "На сервере ещё нет кастомных команд")
        emb = discord.Embed(
            title="Кастомные команды сервера",
            description=commands,
            colour=discord.Color.green(),
        )
        emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)


def setup(client):
    client.add_cog(Information(client))