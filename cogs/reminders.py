import datetime
import discord
from tools.converters import Expiry
from tools.paginator import Paginator
from discord.ext import commands


class Reminders(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.FOOTER = self.client.config.FOOTER_TEXT

    @commands.group()
    async def reminder(self, ctx):
        if ctx.invoked_subcommand is None:
            PREFIX = str(await self.client.database.get_prefix(ctx.guild))
            commands = "\n".join(
                [f"`{PREFIX}reminder {c.name}`" for c in self.client.get_command("setting").commands]
            )
            emb = discord.Embed(
                title="Команды напоминаний",
                description=commands,
                colour=discord.Color.green(),
            )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

    @reminder.command()
    async def create(self, ctx, expiry_at: Expiry, *, text: str):
        reminder_id = await self.client.database.set_reminder(
            member=ctx.author, channel=ctx.channel, time=expiry_at.timestamp(), text=text
        )
        if not reminder_id:
            emb = await self.client.utils.create_error_embed(
                ctx, "**Превишен лимит напоминалок(25)!**",
            )
            await ctx.send(embed=emb)
            return

        emb = discord.Embed(
            title=f"Создано новое напоминая #{reminder_id}",
            description=f"**Текст напоминая:**\n```{text}```\n**Действует до:**\n`{expiry_at.strftime('%d %B %Y %X')}`",
            colour=discord.Color.green(),
        )
        emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)

    @reminder.command()
    async def delete(self, ctx, reminder_id: int):
        state = await self.client.database.del_reminder(ctx.guild.id, reminder_id)
        if state:
            emb = discord.Embed(
                description=f"Напоминания `#{reminder_id}` было успешно удалено",
                colour=discord.Color.green(),
            )
            emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)
            return
        else:
            emb = await self.client.utils.create_error_embed(
                ctx, "**Напоминания с таким id не существует!**"
            )
            await ctx.send(embed=emb)
            return

    @reminder.command()
    async def list(self, ctx):
        data = await self.client.database.get_reminder(target=ctx.author)
        if data != ():
            embeds = []
            for reminder in data:
                active_to = datetime.datetime.fromtimestamp(reminder[4]).strftime('%d %B %Y %X')
                emb = discord.Embed(
                    title="Список напоминаний",
                    description=f"Id: **{reminder[0]}**\nДействует до: `{active_to}`\nТекст:\n>>> {reminder[5][:1024]}",
                    colour=discord.Color.green(),
                )
                emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
                emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
                embeds.append(emb)

            message = await ctx.send(embed=embeds[0])
            paginator = Paginator(ctx, message, embeds, footer=True)
            await paginator.start()
        else:
            emb = discord.Embed(
                title="Список напоминаний",
                description="У вас нету напоминаний",
                colour=discord.Color.green(),
            )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)


def setup(client):
    client.add_cog(Reminders(client))