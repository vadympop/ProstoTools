import discord
import datetime
import uuid
import json
from configs import Config
from discord.utils import get
from discord.ext import commands


FOOTER = Config.FOOTER_TEXT


@commands.command(
    cog_name="Economy",
    description="**Купляет указанный товар**",
    usage="buy [Имя товара]",
    help="**Примеры использования:**\n1. {Prefix}buy gloves\n2. {Prefix}buy text-channel 10\n3. {Prefix}buy box-E\n\n**Пример 1:** Купляет товар с названиям `gloves`\n**Пример 2:** Купляет десять приватных каналов\n**Пример 3:** Купляет эпический лут-бокс",
)
@commands.cooldown(2, 10, commands.BucketType.member)
async def buy(ctx, item: str = None, num: int = None):
    member = ctx.author

    data = await ctx.bot.database.sel_user(target=ctx.author)
    cur_state_prison = data["prison"]
    member_items = data["items"]

    if not cur_state_prison:
        try:
            role = get(ctx.guild.roles, name=item)
        except:
            pass

        if item is None:
            emb = discord.Embed(
                title="Как купить товары?",
                description=f"Метало искатель 1-го уровня - metal_1 или металоискатель_1\nМетало искатель 2-го уровня - metal_2 или металоискатель_2\nТелефон - tel или телефон\nСим-карта - sim или сим-карта\nТекстовый канал - текстовый-канал или text-channel\nМетла - метла или broom\nШвабра - швабра или mop\nПерчатки - перчатки или gloves\nДля покупки роли нужно вести её названия\n\n**Все цены можно узнать с помощю команды {ctx.bot.database.get_prefix(ctx.guild)}shoplist**",
                colour=discord.Color.green(),
            )
            emb.set_author(
                name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url
            )
            emb.set_footer(text=FOOTER, icon_url=ctx.bot.user.avatar_url)
            await ctx.send(embed=emb)
            return

        costs = [500, 1000, 100, 1100, 100, 600, 800, 1800, 4600, 9800, 19600]
        info = await ctx.bot.database.sel_guild(guild=ctx.guild)
        roles = info["shop_list"]

        async def buy_func(func_item, func_cost):
            cur_money = data["money"] - func_cost
            cur_items = data["items"]
            cur_transantions = data["transantions"]
            prison = "False"
            prison_state = False

            if isinstance(cur_items, list):
                cur_items.append(func_item)
            elif cur_items == []:
                cur_items.append(func_item)

            if cur_money <= -5000:
                prison = "True"
                cur_items = []
                prison_state = True

            info_transantion = {
                "to": "Магазин",
                "from": ctx.author.id,
                "cash": func_cost,
                "time": str(datetime.datetime.today()),
                "id": str(uuid.uuid4()),
                "guild_id": ctx.guild.id,
            }
            cur_transantions.append(info_transantion)

            sql = """UPDATE users SET items = %s, prison = %s, money = %s, transantions = %s WHERE user_id = %s AND guild_id = %s"""
            val = (
                json.dumps(cur_items),
                prison,
                cur_money,
                json.dumps(cur_transantions),
                ctx.author.id,
                ctx.guild.id,
            )

            await ctx.bot.database.execute(sql, val)
            return prison_state

        async def buy_coins_func(func_item, func_cost):
            coins_member = data["coins"] - func_cost
            cur_items = data["items"]

            if isinstance(cur_items, list):
                cur_items.append(func_item)
            elif cur_items == []:
                cur_items.append(func_item)

            sql = """UPDATE users SET items = %s, coins = %s WHERE user_id = %s AND guild_id = %s"""
            val = (json.dumps(cur_items), coins_member, ctx.author.id, ctx.guild.id)

            await ctx.bot.database.execute(sql, val)

        async def buy_text_channel(func_cost, num):
            cost = func_cost * num
            cur_transantions = data["transantions"]
            cur_money = data["money"] - cost
            num_textchannels = data["text_channels"] + num
            cur_items = data["items"]
            prison = "False"
            prison_state = False

            if cur_money <= -5000:
                prison = "True"
                cur_items = []
                prison_state = True

            info_transantion = {
                "to": "Магазин",
                "from": ctx.author.id,
                "cash": cost,
                "time": str(datetime.datetime.today()),
                "id": str(uuid.uuid4()),
                "guild_id": ctx.guild.id,
            }
            cur_transantions.append(info_transantion)

            sql = """UPDATE users SET items = %s, prison = %s, money = %s, text_channel = %s, transantions = %s WHERE user_id = %s AND guild_id = %s"""
            val = (
                json.dumps(cur_items),
                prison,
                cur_money,
                num_textchannels,
                json.dumps(cur_transantions),
                ctx.author.id,
                ctx.guild.id,
            )

            await ctx.bot.database.execute(sql, val)
            return prison_state

        async def buy_item(item, cost, stacked=False):
            emb_cool = None
            emb_prison = None
            emb_fail = None

            if item not in member_items:
                if stacked:
                    cur_items = data["items"]
                    prison = data["prison"]
                    stack = False

                    for i in cur_items:
                        if isinstance(i, list):
                            if i[0] == item[0]:
                                stack = True

                    if not stack:
                        state = await buy_func(item, cost)

                        if state:
                            emb_prison = discord.Embed(
                                description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**",
                                colour=discord.Color.green(),
                            )
                            emb_prison.set_author(
                                name=ctx.bot.user.name,
                                icon_url=ctx.bot.user.avatar_url,
                            )
                            emb_prison.set_footer(
                                text=FOOTER,
                                icon_url=ctx.bot.user.avatar_url,
                            )

                        emb_cool = discord.Embed(
                            description=f"**Вы успешно приобрели - {item[0]}**",
                            colour=discord.Color.green(),
                        )
                        emb_cool.set_author(
                            name=ctx.bot.user.name,
                            icon_url=ctx.bot.user.avatar_url,
                        )
                        emb_cool.set_footer(
                            text=FOOTER, icon_url=ctx.bot.user.avatar_url
                        )
                    elif stack:
                        cur_money = data["money"] - cost

                        for i in cur_items:
                            if isinstance(i, list):
                                if i[0] == item[0]:
                                    i[1] += 1

                        if cur_money <= -5000:
                            prison = True
                            cur_items = []
                            emb_prison = discord.Embed(
                                description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**",
                                colour=discord.Color.green(),
                            )
                            emb_prison.set_author(
                                name=ctx.bot.user.name,
                                icon_url=ctx.bot.user.avatar_url,
                            )
                            emb_prison.set_footer(
                                text=FOOTER,
                                icon_url=ctx.bot.user.avatar_url,
                            )

                        emb_cool = discord.Embed(
                            description=f"**Вы успешно приобрели - {item[0]}**",
                            colour=discord.Color.green(),
                        )
                        emb_cool.set_author(
                            name=ctx.bot.user.name,
                            icon_url=ctx.bot.user.avatar_url,
                        )
                        emb_cool.set_footer(
                            text=FOOTER, icon_url=ctx.bot.user.avatar_url
                        )

                        sql = """UPDATE users SET items = %s, prison = %s, money = %s WHERE user_id = %s AND guild_id = %s"""
                        val = (
                            json.dumps(cur_items),
                            str(prison),
                            cur_money,
                            ctx.author.id,
                            ctx.guild.id,
                        )

                        await ctx.bot.database.execute(sql, val)

                elif not stacked:
                    state = await buy_func(item, cost)
                    if state:
                        emb_prison = discord.Embed(
                            description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**",
                            colour=discord.Color.green(),
                        )
                        emb_prison.set_author(
                            name=ctx.bot.user.name,
                            icon_url=ctx.bot.user.avatar_url,
                        )
                        emb_prison.set_footer(
                            text=FOOTER, icon_url=ctx.bot.user.avatar_url
                        )

                    emb_cool = discord.Embed(
                        description=f"**Вы успешно приобрели - {item}**",
                        colour=discord.Color.green(),
                    )
                    emb_cool.set_author(
                        name=ctx.bot.user.name,
                        icon_url=ctx.bot.user.avatar_url,
                    )
                    emb_cool.set_footer(
                        text=FOOTER, icon_url=ctx.bot.user.avatar_url
                    )
            else:
                if not stacked:
                    emb_fail = discord.Embed(
                        description="**Вы уже имеете этот товар!**",
                        colour=discord.Color.green(),
                    )
                    emb_fail.set_author(
                        name=ctx.bot.user.name,
                        icon_url=ctx.bot.user.avatar_url,
                    )
                    emb_fail.set_footer(
                        text=FOOTER, icon_url=ctx.bot.user.avatar_url
                    )
                elif stacked:
                    cur_items = data["items"]
                    prison = data["prison"]
                    stack = False

                    for i in cur_items:
                        if isinstance(i, list):
                            if i[0] == item[0]:
                                stack = True

                    if not stack:
                        state = await buy_func(item, cost)
                        if state:
                            emb_prison = discord.Embed(
                                description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**",
                                colour=discord.Color.green(),
                            )
                            emb_prison.set_author(
                                name=ctx.bot.user.name,
                                icon_url=ctx.bot.user.avatar_url,
                            )
                            emb_prison.set_footer(
                                text=FOOTER,
                                icon_url=ctx.bot.user.avatar_url,
                            )

                        emb_cool = discord.Embed(
                            description=f"**Вы успешно приобрели - {item[0]}**",
                            colour=discord.Color.green(),
                        )
                        emb_cool.set_author(
                            name=ctx.bot.user.name,
                            icon_url=ctx.bot.user.avatar_url,
                        )
                        emb_cool.set_footer(
                            text=FOOTER, icon_url=ctx.bot.user.avatar_url
                        )
                    elif stack:
                        cur_money = data["money"] - cost

                        for i in cur_items:
                            if isinstance(i, list):
                                if i[0] == item[0]:
                                    i[1] += 1

                        if cur_money <= -5000:
                            cur_items = []
                            prison = True
                            emb_prison = discord.Embed(
                                description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**",
                                colour=discord.Color.green(),
                            )
                            emb_prison.set_author(
                                name=ctx.bot.user.name,
                                icon_url=ctx.bot.user.avatar_url,
                            )
                            emb_prison.set_footer(
                                text=FOOTER,
                                icon_url=ctx.bot.user.avatar_url,
                            )

                        emb_cool = discord.Embed(
                            description=f"**Вы успешно приобрели - {item[0]}**",
                            colour=discord.Color.green(),
                        )
                        emb_cool.set_author(
                            name=ctx.bot.user.name,
                            icon_url=ctx.bot.user.avatar_url,
                        )
                        emb_cool.set_footer(
                            text=FOOTER, icon_url=ctx.bot.user.avatar_url
                        )

                        sql = """UPDATE users SET items = %s, prison = %s, money = %s WHERE user_id = %s AND guild_id = %s"""
                        val = (
                            json.dumps(cur_items),
                            str(prison),
                            cur_money,
                            ctx.author.id,
                            ctx.guild.id,
                        )

                        await ctx.bot.database.execute(sql, val)

            embeds = [emb_cool, emb_prison, emb_fail]
            return embeds

        if (
                item == "металоискатель1"
                or item == "metal_1"
                or item == "металоискатель_1"
        ):
            embeds = await buy_item("metal_1", costs[0])
            if embeds[0]:
                await ctx.send(embed=embeds[0])
            elif embeds[1]:
                await member.send(embed=embeds[1])
            elif embeds[2]:
                await ctx.message.add_reaction("❌")
                await ctx.send(embed=embeds[2])

        elif (
                item == "металоискатель2"
                or item == "metal_2"
                or item == "металоискатель_2"
        ):
            embeds = await buy_item("metal_2", costs[1])
            if embeds[0]:
                await ctx.send(embed=embeds[0])
            elif embeds[1]:
                await member.send(embed=embeds[1])
            elif embeds[2]:
                await ctx.message.add_reaction("❌")
                await ctx.send(embed=embeds[2])

        elif (
                item == "телефон"
                or item == "тел"
                or item == "telephone"
                or item == "tel"
        ):
            embeds = await buy_item("tel", costs[3])
            if embeds[0]:
                await ctx.send(embed=embeds[0])
            elif embeds[1]:
                await member.send(embed=embeds[1])
            elif embeds[2]:
                await ctx.message.add_reaction("❌")
                await ctx.send(embed=embeds[2])

        elif (
                item == "sim"
                or item == "sim_card"
                or item == "sim-card"
                or item == "симка"
                or item == "сим_карта"
        ):
            embeds = await buy_item("sim", costs[2])
            if embeds[0]:
                await ctx.send(embed=embeds[0])
            elif embeds[1]:
                await member.send(embed=embeds[1])
            elif embeds[2]:
                await ctx.message.add_reaction("❌")
                await ctx.send(embed=embeds[2])

        elif role is not None:
            role_state = False

            for i in roles:
                if i[0] == role.id:
                    role_state = True

            if role_state:
                if role.id not in member_items and role not in member.roles:

                    for i in roles:
                        if i[0] == role.id:
                            role_cost = i[1]

                    state = await buy_func(role.id, role_cost)
                    await member.add_roles(role)

                    if state:
                        emb = discord.Embed(
                            description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**",
                            colour=discord.Color.green(),
                        )
                        emb.set_author(
                            name=ctx.bot.user.name,
                            icon_url=ctx.bot.user.avatar_url,
                        )
                        emb.set_footer(
                            text=FOOTER, icon_url=ctx.bot.user.avatar_url
                        )
                        await member.send(embed=emb)
                        return

                    emb = discord.Embed(
                        description=f"**Вы успешно приобрели новую роль - `{role.name}`>**",
                        colour=discord.Color.green(),
                    )
                    emb.set_author(
                        name=ctx.bot.user.name,
                        icon_url=ctx.bot.user.avatar_url,
                    )
                    emb.set_footer(
                        text=FOOTER, icon_url=ctx.bot.user.avatar_url
                    )
                    await ctx.send(embed=emb)
                else:
                    emb = discord.Embed(
                        title="Ошибка!",
                        description="**Вы уже имеете эту роль!**",
                        colour=discord.Color.green(),
                    )
                    emb.set_author(
                        name=ctx.bot.user.name,
                        icon_url=ctx.bot.user.avatar_url,
                    )
                    emb.set_footer(
                        text=FOOTER, icon_url=ctx.bot.user.avatar_url
                    )
                    await ctx.send(embed=emb)
                    await ctx.message.add_reaction("❌")
                    return
            else:
                emb = discord.Embed(
                    title="Ошибка!",
                    description=f"**Укажите роль правильно, такой роли нету в списке продаваемых ролей!**",
                    colour=discord.Color.green(),
                )
                emb.set_author(
                    name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url
                )
                emb.set_footer(
                    text=FOOTER, icon_url=ctx.bot.user.avatar_url
                )
                await ctx.send(embed=emb)
                await ctx.message.add_reaction("❌")
                return

        elif item == "метла" or item == "broom" or item == "metla":
            if data["coins"] >= 500:
                if member_items is not None and not isinstance(member_items, int):
                    if "broom" not in member_items:
                        await buy_coins_func("broom", 500)
                        emb = discord.Embed(
                            description=f"**Вы успешно приобрели - {item}**",
                            colour=discord.Color.green(),
                        )
                        emb.set_author(
                            name=ctx.bot.user.name,
                            icon_url=ctx.bot.user.avatar_url,
                        )
                        emb.set_footer(
                            text=FOOTER, icon_url=ctx.bot.user.avatar_url
                        )
                        await ctx.send(embed=emb)
                    else:
                        emb = discord.Embed(
                            description="**Вы уже имеете этот товар!**",
                            colour=discord.Color.green(),
                        )
                        emb.set_author(
                            name=ctx.bot.user.name,
                            icon_url=ctx.bot.user.avatar_url,
                        )
                        emb.set_footer(
                            text=FOOTER, icon_url=ctx.bot.user.avatar_url
                        )
                        await ctx.send(embed=emb)
                        return
                else:
                    await buy_coins_func("broom", 500)
                    emb = discord.Embed(
                        description=f"**Вы успешно приобрели - {item}**",
                        colour=discord.Color.green(),
                    )
                    emb.set_author(
                        name=ctx.bot.user.name,
                        icon_url=ctx.bot.user.avatar_url,
                    )
                    emb.set_footer(
                        text=FOOTER, icon_url=ctx.bot.user.avatar_url
                    )
                    await ctx.send(embed=emb)
            else:
                emb = discord.Embed(
                    title="Ошибка!",
                    description=f"**У вас недостаточно коинов!**",
                    colour=discord.Color.green(),
                )
                emb.set_author(
                    name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url
                )
                emb.set_footer(
                    text=FOOTER, icon_url=ctx.bot.user.avatar_url
                )
                await ctx.send(embed=emb)
                await ctx.message.add_reaction("❌")
                return
        elif item == "швабра" or item == "mop":
            if data["coins"] >= 500:
                if "mop" not in member_items:
                    await buy_coins_func("mop", 2000)
                    emb = discord.Embed(
                        description=f"**Вы успешно приобрели - {item}**",
                        colour=discord.Color.green(),
                    )
                    emb.set_author(
                        name=ctx.bot.user.name,
                        icon_url=ctx.bot.user.avatar_url,
                    )
                    emb.set_footer(
                        text=FOOTER, icon_url=ctx.bot.user.avatar_url
                    )
                    await ctx.send(embed=emb)
                else:
                    emb = discord.Embed(
                        description="**Вы уже имеете этот товар!**",
                        colour=discord.Color.green(),
                    )
                    emb.set_author(
                        name=ctx.bot.user.name,
                        icon_url=ctx.bot.user.avatar_url,
                    )
                    emb.set_footer(
                        text=FOOTER, icon_url=ctx.bot.user.avatar_url
                    )
                    await ctx.send(embed=emb)
                    return
            else:
                await ctx.message.add_reaction("❌")
                emb = discord.Embed(
                    title="Ошибка!",
                    description=f"**У вас недостаточно коинов!**",
                    colour=discord.Color.green(),
                )
                emb.set_author(
                    name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url
                )
                emb.set_footer(
                    text=FOOTER, icon_url=ctx.bot.user.avatar_url
                )
                await ctx.send(embed=emb)
                return

        elif item == "перчатки" or item == "gloves":
            embeds = await buy_item("gloves", costs[5])
            if embeds[0]:
                await ctx.send(embed=embeds[0])
            elif embeds[1]:
                await member.send(embed=embeds[1])
            elif embeds[2]:
                await ctx.send(embed=embeds[2])

        elif (
                item == "бокс-обычный"
                or item == "box-c"
                or item == "box-C"
                or item == "box-common"
                or item == "box-Common"
        ):
            embeds = await buy_item(["box-C", 1], costs[6], True)
            if embeds[0]:
                await ctx.send(embed=embeds[0])
            elif embeds[1]:
                await member.send(embed=embeds[1])
            elif embeds[2]:
                await ctx.send(embed=embeds[2])

        elif (
                item == "бокс-редкий"
                or item == "box-r"
                or item == "box-R"
                or item == "box-rare"
                or item == "box-Rare"
        ):
            embeds = await buy_item(["box-R", 1], costs[7], True)
            if embeds[0]:
                await ctx.send(embed=embeds[0])
            elif embeds[1]:
                await member.send(embed=embeds[1])
            elif embeds[2]:
                await ctx.send(embed=embeds[2])

        elif (
                item == "бокс-эпик"
                or item == "box-e"
                or item == "box-E"
                or item == "box-epic"
                or item == "box-Epic"
        ):
            embeds = await buy_item(["box-E", 1], costs[8], True)
            if embeds[0]:
                await ctx.send(embed=embeds[0])
            elif embeds[1]:
                await member.send(embed=embeds[1])
            elif embeds[2]:
                await ctx.send(embed=embeds[2])

        elif (
                item == "бокс-легенда"
                or item == "box-l"
                or item == "box-L"
                or item == "box-legendary"
                or item == "box-Legendary"
        ):
            embeds = await buy_item(["box-L", 1], costs[9], True)
            if embeds[0]:
                await ctx.send(embed=embeds[0])
            elif embeds[1]:
                await member.send(embed=embeds[1])
            elif embeds[2]:
                await ctx.send(embed=embeds[2])

        elif (
                item == "бокс-невероятный"
                or item == "box-i"
                or item == "box-I"
                or item == "box-imposible"
                or item == "box-Imposible"
        ):
            embeds = await buy_item(["box-I", 1], costs[10], True)
            if embeds[0]:
                await ctx.send(embed=embeds[0])
            elif embeds[1]:
                await member.send(embed=embeds[1])
            elif embeds[2]:
                await ctx.send(embed=embeds[2])

        elif (
                item == "текст_канал"
                or item == "текстовый-канал"
                or item == "text-channel"
                or item == "text_channel"
        ):
            if num is not None:
                if num <= 0:
                    emb = await ctx.bot.utils.create_error_embed(
                        ctx,
                        "Укажите число покупаемых каналов больше 0!"
                    )
                    await ctx.send(embed=emb)
                    return

                state = await buy_text_channel(costs[4], num)
                if state:
                    emb = discord.Embed(
                        description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**",
                        colour=discord.Color.green(),
                    )
                    emb.set_author(
                        name=ctx.bot.user.name,
                        icon_url=ctx.bot.user.avatar_url,
                    )
                    emb.set_footer(
                        text=FOOTER, icon_url=ctx.bot.user.avatar_url
                    )
                    await member.send(embed=emb)
                    return

                emb = discord.Embed(
                    description=f"**Вы успешно приобрели текстовые каналы - {num}шт**",
                    colour=discord.Color.green(),
                )
                emb.set_author(
                    name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url
                )
                emb.set_footer(
                    text=FOOTER, icon_url=ctx.bot.user.avatar_url
                )
                await ctx.send(embed=emb)
            elif num is None:
                await ctx.message.add_reaction("❌")
                emb = discord.Embed(
                    title="Ошибка!",
                    description=f"**Вы не указали число покупаемых каналов!**",
                    colour=discord.Color.green(),
                )
                emb.set_author(
                    name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url
                )
                emb.set_footer(
                    text=FOOTER, icon_url=ctx.bot.user.avatar_url
                )
                await ctx.send(embed=emb)
                return

    elif cur_state_prison:
        await ctx.message.add_reaction("❌")
        emb = discord.Embed(
            title="Ошибка!",
            description="**У вас заблокирование транзакции, так как вы в тюрме!**",
            colour=discord.Color.green(),
        )
        emb.set_author(
            name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url
        )
        emb.set_footer(text=FOOTER, icon_url=ctx.bot.user.avatar_url)
        await ctx.send(embed=emb)
        return
