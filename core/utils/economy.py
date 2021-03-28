import discord

from discord.ext import commands
from core.services.database.models import User


def parse_inventory(ctx: commands.Context, data: User) -> tuple:
    roles_content = ""
    items_content = ""
    box_content = ""
    pets_content = ""
    check_state = True
    names_of_items = {
        "sim": "Сим-карта",
        "tel": "Телефон",
        "metal_1": "Металоискатель 1-го уровня",
        "metal_2": "Металоискатель 2-го уровня",
        "mop": "Швабра",
        "broom": "Метла",
        "gloves": "Перчатки",
    }
    boxes = {
        "box-I": "Невероятный бокс",
        "box-L": "Легендарный бокс",
        "box-E": "Эпический бокс",
        "box-R": "Редкий бокс",
        "box-C": "Обычный бокс",
    }
    dict_pets = {
        "cat": "Кошка",
        "dog": "Собачка",
        "helmet": "Каска",
        "loupe": "Лупа",
        "parrot": "Попугай",
        "hamster": "Хомяк",
    }

    if not data.items:
        items_content = f"Ваш инвертарь пуст. Купите что-нибудь с помощью команды - {await ctx.bot.database.get_prefix(guild=ctx.guild)}buy\n"
        check_state = False
    elif data.items:
        for item in data.items:
            if isinstance(item, list):
                box_content = box_content + f"{boxes[item[0]]} - {item[1]}шт \n"
            else:
                if isinstance(item, str):
                    items_content = items_content + f"{names_of_items[item]}\n "
                elif isinstance(item, int):
                    roles_content = roles_content + f"{ctx.guild.get_role(item).mention}\n "

        for pet in data.pets:
            pets_content += f"{dict_pets[pet]}\n "

    if check_state:
        items_content = f"**Ваши предметы:**\n{items_content}\n" if items_content else ""

    roles_content = f"**Ваши роли:**\n{roles_content}\n" if roles_content else ""
    box_content = f"**Ваши лут-боксы:**\n{box_content}\n" if box_content else ""
    pets_content = f"**Ваши питомцы:**\n{pets_content}\n" if pets_content else ""

    return items_content, roles_content, box_content, pets_content


async def crime_member(ctx: commands.Context, num: int, member: discord.Member):
    data = await ctx.bot.database.sel_user(target=member)
    data.money += num

    if data.money <= -5000:
        data.prison = True
        data.items = []

    await ctx.bot.database.update(
        "users",
        where={"user_id": member.id, "guild_id": member.guild.id},
        money=data.money,
        items=data.items,
        prison=data.prison
    )
    return data.prison, data.money


async def rob_func(ctx, num: int, member: discord.Member):
    data = await ctx.bot.database.sel_user(target=member)
    data.money += num

    if member == ctx.author:
        if data.money <= -5000:
            data.items = []
            data.prison = True

    await ctx.bot.database.update(
        "users",
        where={"user_id": member.id, "guild_id": ctx.guild.id},
        money=data.money,
        items=data.items,
        prison=data.prison
    )
    return data.prison, data.money