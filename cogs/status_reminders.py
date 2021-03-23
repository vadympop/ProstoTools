import discord
from discord.ext import commands


class StatusReminders(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.FOOTER = self.client.config.FOOTER_TEXT

    @commands.group(
        name="status-reminder",
        usage="reminder [Команда]",
        description="**Категория команд - напоминания**",
        help=f"""**Команды групы:** create, delete, list\n\n""",
        aliases=[
            "sr",
            "statusreminder",
            "status_reminder",
            "status-remin",
            "statusremin",
            "status_remin"
        ]
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def status_reminder(self, ctx):
        if ctx.invoked_subcommand is None:
            emb = discord.Embed(
                title="Напоминания статусов",
                description=f"`create` - создаст новое напоминания\n`delete` - удалит напоминания\n`list` - покажет список ваших напоминаний статусов",
                colour=discord.Color.green(),
            )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

    @status_reminder.command(
        description="**Создаст новое напоминание**",
        help="Пусто",
        usage="status-reminder create [repeated/default] [@Участник] [Ожидаемый статус]",
    )
    async def create(self, ctx, type_reminder: str, member: discord.Member, *, status: str):
        types = ("default", "repeated")
        convert_shorts = {
            "r": "repeated",
            "d": "default"
        }
        statuses = ("dnd", "online", "offline", "idle")
        convert_statuses = {
            "не беспокоить": "dnd",
            "онлайн": "online",
            "оффлайн": "offline",
            "отошел": "idle"
        }
        if type_reminder.lower() in convert_shorts.keys():
            type_reminder = convert_shorts[type_reminder.lower()]

        if type_reminder.lower() not in types:
            emb = await self.client.utils.create_error_embed(
                ctx, "**Укажите один из этих типов: default, repeated!**"
            )
            await ctx.send(embed=emb)
            return

        if status.lower() in convert_statuses.keys():
            status = convert_statuses[status.lower()]

        if status.lower() not in statuses:
            emb = await self.client.utils.create_error_embed(
                ctx, "**Укажите один из этих статусов: dnd, online, offline, idle!**"
            )
            await ctx.send(embed=emb)
            return

        state = await self.client.database.set_status_reminder(
            member.id, ctx.author.id, status.lower(), type_reminder.lower()
        )
        if not state:
            emb = await self.client.utils.create_error_embed(
                ctx,
                "**У вас уже есть напоминания статуса на этого участника/вы превысили максимальное количество напоминания(20)!**"
            )
            await ctx.send(embed=emb)
            return

        invert_convert_statuses = {k: x for x, k in convert_statuses.items()}
        emb = discord.Embed(
            title=f"Создано новое напоминая статуса #{state}",
            description=f"Смотрит за: `{member}`\nЖдет статус: `{invert_convert_statuses[status.lower()]}`",
            colour=discord.Color.green(),
        )
        emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)

    @status_reminder.command(
        description="**Удалить напоминание**",
        help="Пусто",
        usage="status-reminder delete [Id]",
    )
    async def delete(self, ctx, reminder_id: int):
        state = await self.client.database.del_status_reminder(reminder_id)
        if not state:
            emb = await self.client.utils.create_error_embed(
                ctx, "**Напоминания с указаным id не существует!**"
            )
            await ctx.send(embed=emb)
            return

        try:
            await ctx.message.add_reaction("✅")
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

    @status_reminder.command(
        description="**Покажет список ваших напоминаний**",
        help="Пусто",
        usage="status-reminder list",
    )
    async def list(self, ctx):
        data = await self.client.database.get_status_reminder(member_id=ctx.author.id)
        if data != ():
            convert_statuses = {
                "dnd": "не беспокоить",
                "online": "онлайн",
                "offline": "оффлайн",
                "idle": "отошел"
            }

            description = "\n".join([
                f"Id: `{setting[0]}` Пользователь: `{self.client.get_user(setting[1])}` Ждет: `{convert_statuses[setting[3]]}` Повторяемый: `{'Да' if setting[4] == 'repeated' else 'Нет'}`"
                for setting in data
            ])
        else:
            description = "У вас нету напоминаний статуса"

        emb = discord.Embed(
            title="Список напоминаний статуса",
            description=description,
            colour=discord.Color.green(),
        )
        emb.set_author(
            name=self.client.user.name, icon_url=self.client.user.avatar_url
        )
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)


def setup(client):
    client.add_cog(StatusReminders(client))