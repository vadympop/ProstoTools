import discord
from discord.ext import commands


class Context(commands.Context):
    async def send(self, content: any = None, **kwargs):
        if not (perms := self.channel.permissions_for(self.me)).send_messages:
            try:
                await self.author.send("Я не могу отправлять сообщения в этот канал")
            except discord.Forbidden:
                pass
            return

        if kwargs.get('embed') is not None and not perms.embed_links:
            kwargs = {}
            content = f"Для работы этой команды нужно разрешение **{self.bot.config.PERMISSIONS_DICT['embed_links']}**"

        if isinstance(content, discord.Embed):
            kwargs['embed'] = content
            content = None

        if isinstance(content, discord.File):
            kwargs['file'] = content
            content = None

        return await super().send(content, **kwargs)