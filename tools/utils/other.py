import typing
from discord.ext import commands


async def process_converters(ctx: commands.Context, converters: typing.Iterable, argument: typing.Any) -> typing.Any:
    for conv in converters:
        try:
            result = await conv().convert(
                ctx, argument
            )
        except commands.BadArgument:
            pass
        else:
            return result