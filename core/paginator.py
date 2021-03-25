import discord
import asyncio
from discord.ext import commands


class Paginator:
    def __init__(
            self,
            ctx: commands.Context,
            message: discord.Message,
            embeds: list,
            timeout: int = 60,
            footer_icon_url: str = None,
            footer: bool = False,
    ):
        self.ctx = ctx
        self.message = message
        self.timeout = timeout
        self.reactions = ["⬅", "➡"]
        self.index = 0
        self.embeds = embeds
        self.footer = footer
        self.footer_icon_url = footer_icon_url

    def emoji_checker(self, payload):
        if payload.message_id != self.message.id:
            return False

        if payload.user_id != self.ctx.author.id:
            return False

        return True

    async def add_reactions(self):
        for emoji in self.reactions:
            await self.message.add_reaction(emoji)
        return True

    async def start(self):
        await self.add_reactions()
        while True:
            try:
                add_reaction = asyncio.ensure_future(
                    self.ctx.bot.wait_for(
                        "raw_reaction_add", check=self.emoji_checker
                    )
                )
                remove_reaction = asyncio.ensure_future(
                    self.ctx.bot.wait_for(
                        "raw_reaction_remove", check=self.emoji_checker
                    )
                )
                done, pending = await asyncio.wait(
                    (add_reaction, remove_reaction),
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=self.timeout,
                )

                for i in pending:
                    i.cancel()

                if len(done) == 0:
                    raise asyncio.TimeoutError()

                payload = done.pop().result()
                user = self.ctx.guild.get_member(payload.user_id)
                if user is not None:
                    try:
                        await self.message.remove_reaction(
                            payload.emoji, user
                        )
                    except discord.Forbidden:
                        pass
                await self.pagination(payload.emoji)
            except asyncio.TimeoutError:
                if self.message.guild:
                    try:
                        await self.message.clear_reactions()
                    except discord.Forbidden:
                        pass
                else:
                    pass
                break

    async def pagination(self, emoji):
        if str(emoji) == str(self.reactions[0]):
            await self.previous_page()
        elif str(emoji) == str(self.reactions[1]):
            await self.next_page()

    async def previous_page(self):
        if self.index != 0:
            self.index -= 1
        else:
            self.index = len(self.embeds)-1
        await self.update_message()

    async def next_page(self):
        if self.index != len(self.embeds) - 1:
            self.index += 1
        else:
            self.index = 0
        await self.update_message()

    async def update_message(self):
        if self.footer:
            self.embeds[self.index].set_footer(
                text=f'Страница: {1 + self.index}/{len(self.embeds)}',
                icon_url=self.footer_icon_url if self.footer_icon_url is not None else ''
            )
        return await self.message.edit(embed=self.embeds[self.index])