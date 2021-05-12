import discord
import jinja2

from core.bases.cog_base import BaseCog
from discord.ext import commands


class EventsAutoResponders(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.cd_mapping = commands.CooldownMapping.from_cooldown(2, 1, commands.BucketType.member)

    def find_autoresponder(self, name: str, autoresponders: list) -> dict:
        for autoresponder in autoresponders:
            if autoresponder["name"] == name:
                return autoresponder

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        if len(message.content) > self.client.config.MAX_LENGTH_AUTORESPONDER_NAME:
            return

        autoresponders = (await self.client.database.sel_guild(guild=message.guild)).autoresponders
        autoresponder = self.find_autoresponder(message.content, autoresponders)
        if autoresponder is not None:
            if not autoresponder['state']:
                return

            if self.cd_mapping.get_bucket(message).update_rate_limit():
                try:
                    await message.add_reaction("⏰")
                except discord.errors.Forbidden:
                    pass
                except discord.errors.HTTPException:
                    pass
                return

            ctx = await self.client.get_context(message)
            try:
                try:
                    await message.channel.send(await self.client.template_engine.render(
                        message, message.author, autoresponder["message"]
                    ))
                except discord.errors.HTTPException:
                    emb = await self.client.utils.create_error_embed(
                        ctx, "**Во время выполнения авто-ответчика пройзошла неизвестная ошибка!**"
                    )
                    await message.channel.send(embed=emb)
                    return
            except jinja2.exceptions.TemplateSyntaxError as e:
                emb = await self.client.utils.create_error_embed(
                    ctx, f"Во время выполнения авто-ответчика пройзошла ошибка:\n```{repr(e)}```"
                )
                await message.channel.send(embed=emb)
                return


def setup(client):
    client.add_cog(EventsAutoResponders(client))
