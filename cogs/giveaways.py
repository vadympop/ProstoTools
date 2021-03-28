import discord
import asyncio
import datetime

from core.bases.cog_base import BaseCog
from core.converters import Expiry
from core.paginator import Paginator
from discord.ext import commands


class Giveaways(BaseCog):
    @commands.group(
        usage="clan [Команда]",
        description="Категория команд - розыгрыши",
        help=f"""**Команды групы:** create, end, delete, list\n\n"""
    )
    async def giveaway(self, ctx):
        if ctx.invoked_subcommand is None:
            PREFIX = str(await self.client.database.get_prefix(ctx.guild))
            commands = "\n".join(
                [f"`{PREFIX}giveaway {c.name}`" for c in self.client.get_command("giveaway").commands]
            )
            emb = discord.Embed(
                title="Команды розыгрышей",
                description=commands,
                colour=discord.Color.green(),
            )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

    @giveaway.command(
        usage="giveaway create [Время] [Кол-во победителей] |Канал|",
        description="Создаёт розыгрыш"
    )
    async def create(self, ctx, expiry_at: Expiry, winners: int, channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel

        if winners > 20:
            await ctx.send(
                f":toolbox: **Настройки розыгрыша**\n*Победителей:* `{winners}`\n*Канал:* {channel.mention}\n>>> **Укажите число победителей не больше чем 20!**"
            )
            return

        await ctx.send(
            f":toolbox: **Настройки розыгрыша**\n*Победителей:* `{winners}`\n*Канал:* {channel.mention}\n>>> **Введите названия розыгрыша**"
        )
        try:
            name_msg = await self.client.wait_for(
                "message",
                check=lambda m: m.channel == ctx.channel and m.author == ctx.author,
                timeout=120
            )
        except asyncio.TimeoutError:
            await ctx.send(
                f":toolbox: Настройки розыгрыша**\n*Победителей:* `{winners}`\n*Канал:* {channel.mention}\n>>> **Время вышло!**"
            )
        else:
            if len(name_msg.content) >= 256:
                await ctx.send(
                    f":toolbox: **Настройки розыгрыша**\n*Победителей:* `{winners}`\n*Канал:* {channel.mention}\n>>> **Укажите названия меньше 256 символов!**"
                )
                return

            await ctx.send(
                f":toolbox: **Настройки розыгрыша**\n*Победителей:* `{winners}`\n*Канал:* {channel.mention}\n*Названия:* `{name_msg.content}`\n>>> **Введите приз розыгрыша**"
            )
            try:
                prize_msg = await self.client.wait_for(
                    "message",
                    check=lambda m: m.channel == ctx.channel and m.author == ctx.author,
                    timeout=120
                )
            except asyncio.TimeoutError:
                await ctx.send(
                    f":toolbox: **Настройки розыгрыша**\n*Победителей:* `{winners}`\n*Канал:* {channel.mention}\n*Названия:* `{name_msg.content}`\n>>> **Время вышло!**"
                )
            else:
                if len(prize_msg.content) >= 1024:
                    await ctx.send(
                        f":toolbox: **Настройки розыгрыша**\n*Победителей:* `{winners}`\n*Канал:* {channel.mention}\n*Названия:* `{name_msg.content}`\n>>> **Укажите приз меньше 1024 символов!**"
                    )
                    return

                emb = discord.Embed(
                    description=f"Добавь :tada: что бы участвовать\nОрганизатор: {ctx.author.mention}\nПриз:\n>>> {prize_msg.content}",
                    colour=discord.Color.blurple(),
                    timestamp=expiry_at
                )
                emb.set_author(name=name_msg.content)
                emb.set_footer(text=f"{winners} Победителей. Заканчивается в")
                message = await channel.send(embed=emb)
                try:
                    await message.add_reaction("🎉")
                except discord.errors.Forbidden:
                    await ctx.send(
                        f":toolbox: **Настройки розыгрыша**\n*Победителей:* `{winners}`\n*Канал:* {channel.mention}\n*Названия:* `{name_msg.content}`\n*Приз:* `{prize_msg.content}`\n>>> **Я не могу поставить реакцию на сообщения! Создание розыгрыша прервано!**"
                    )
                    return
                except discord.errors.HTTPException:
                    await ctx.send(
                        f":toolbox: **Настройки розыгрыша**\n*Победителей:* `{winners}`\n*Канал:* {channel.mention}\n*Названия:* `{name_msg.content}`\n*Приз:* `{prize_msg.content}`\n>>> **Сообщения удалено! Создание розыгрыша прервано!**"
                    )
                    return

                giveaway_id = await self.client.database.add_giveaway(
                    channel_id=channel.id,
                    message_id=message.id,
                    creator=ctx.author,
                    num_winners=winners,
                    time=expiry_at.timestamp(),
                    name=name_msg.content,
                    prize=prize_msg.content
                )
                await ctx.send(
                    f":toolbox: **Настройки розыгрыша**\n*Победителей:* `{winners}`\n*Канал:* {channel.mention}\n*Названия:* `{name_msg.content}`\n*Приз:* `{prize_msg.content}`\n>>> **Успешно создан новый розыгрыш** #`{giveaway_id}` **!**"
                )

    @giveaway.command(
        usage="giveaway delete [Id розыгрыша]",
        description="Удаляет розыгрыш"
    )
    async def delete(self, ctx, giveaway_id: int):
        if await self.client.database.get_giveaway(giveaway_id) is None:
            emb = await self.client.utils.create_error_embed(
                ctx, "**Розыгрыша с указанным id не существует**"
            )
            await ctx.send(embed=emb)
            return

        await self.client.database.del_giveaway(giveaway_id)
        try:
            await ctx.message.add_reaction("✅")
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

    @giveaway.command(
        usage="giveaway end [Id розыгрыша]",
        description="Заканчивает розыгрыш"
    )
    async def end(self, ctx, giveaway_id: int):
        data = await self.client.database.get_giveaway(giveaway_id)
        if data is None:
            emb = await self.client.utils.create_error_embed(
                ctx, "**Розыгрыша с указанным id не существует**"
            )
            await ctx.send(embed=emb)
            return

        state = await self.client.utils.end_giveaway(data)
        if not state:
            emb = await self.client.utils.create_error_embed(
                ctx,
                "Окончания розыгрыша прервано, розыгрыш был удален! Проверьте эти причины ошибки:\n1. Канал с розыгрышем удален\n2. Сообщения розыгрыша удалено\n3. На сообщении нету :tada: реакции",
            )
            await ctx.send(embed=emb)
            return

        try:
            await ctx.message.add_reaction("✅")
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

    @giveaway.command(
        usage="giveaway list",
        description="Покажет список всех розыгрышей на сервере"
    )
    async def list(self, ctx):
        data = await self.client.database.get_giveaways(guild_id=ctx.guild.id)
        if len(data) > 0:
            embeds = []
            for giveaway in data:
                active_to = datetime.datetime.fromtimestamp(giveaway.time).strftime("%d %B %Y %X")
                creator = str(ctx.guild.get_member(giveaway.creator_id))
                message_link = f"https://discord.com/channels/{giveaway.guild_id}/{giveaway.channel_id}/{giveaway.message_id}"
                description = f"""[Сообщения]({message_link})\nId: `{giveaway.id}`\nНазвание: `{giveaway.name}`\nКанал: {ctx.guild.get_channel(giveaway.channel_id)}\nОрганизатор: `{creator}`\nДействует до: `{active_to}`\nПобедителей: `{giveaway.num_winners}`\nПриз:\n>>> {giveaway.prize}"""
                emb = discord.Embed(
                    title=f"Все розыгрышы этого сервера",
                    description=description,
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
                title=f"Все розыгрышы этого сервера",
                description="Список розыгрышей пуст",
                colour=discord.Color.green(),
            )
            emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)


def setup(client):
    client.add_cog(Giveaways(client))
