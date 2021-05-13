import discord

from core.utils.other import is_moderator
from core.bases.cog_base import BaseCog
from discord.ext import commands


class ShowConfigs(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.commands = [
            command.name
            for cog in self.client.cogs
            for command in self.client.get_cog(cog).get_commands()
            if cog.lower() not in ("help", "owner", "jishaku")
        ]

    @commands.group(
        name="show-config",
        usage="show-config |Команда|",
        description="Категория команд - конфиг",
        help="**Команды групы:** server-stats, ignored-channels, auto-moderate, auto-reactions, audit",
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def show_config(self, ctx):
        if ctx.invoked_subcommand is None:
            data = await self.client.database.sel_guild(guild=ctx.guild)

            if not data.rank_message["state"]:
                rank_message = "Стандартное"
            else:
                rank_message = "Включено"

            if "channel_id" not in data.voice_channel.keys():
                voice_channel = "Выключены"
            else:
                channel = ctx.guild.get_channel(data.voice_channel["channel_id"])
                voice_channel = f"Включены({channel.name})" if channel is not None else f"Включены"

            main_settings = f"""Префикс - `{data.prefix}`
    Максимальное количество предупрежденний - `{data.warns_settings["max"]}`
    Множитель опыта - `{data.exp_multi * 100}%`
    Сообщения о повышении уровня - `{rank_message}`
    Приватные голосовые комнаты - `{voice_channel}`
    """

            emb = discord.Embed(title="Настройки бота на сервере", colour=discord.Color.green())
            emb.add_field(name="Основные настройки", value=main_settings)
            emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

    @show_config.command(
        name="server-stats",
        usage="show-config server-stats",
        description="Покажет настройки статистики сервера",
    )
    @commands.check(is_moderator)
    async def server_stats(self, ctx):
        data = (await self.client.database.sel_guild(guild=ctx.guild)).server_stats
        if data == {}:
            server_stats = "Не настроено"
        else:
            server_stats = "\n".join([
                f"`{category}` - `{ctx.guild.get_channel(channel).name}`"
                for category, channel in data.items()
                if category != "message" and ctx.guild.get_channel(channel) is not None
            ])

        if "message" in data.keys():
            channel = ctx.guild.get_channel(data["message"][1])
            if channel is not None:
                try:
                    message = await channel.fetch_message(data["message"][0])
                except discord.errors.NotFound:
                    pass
                else:
                    server_stats += f"\n`message` - `#{channel.name}`, [сообщения]({message.jump_url})"

        if server_stats == "":
            server_stats = "Не настроено"

        emb = discord.Embed(title="Настройки бота на сервере", colour=discord.Color.green())
        emb.add_field(name="Статистика сервера", value=server_stats)
        emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)

    @show_config.command(
        name="auto-reactions",
        usage="show-config auto-reactions",
        description="Покажет настройки авто-реакций",
    )
    @commands.check(is_moderator)
    async def auto_reactions(self, ctx):
        data = (await self.client.database.sel_guild(guild=ctx.guild)).auto_reactions
        if data == {}:
            auto_reactions = "Не настроено"
        else:
            auto_reactions = "\n".join([
                f"`#{ctx.guild.get_channel(int(channel)).name}` - `{', '.join(emojis)}`"
                for channel, emojis in data.items()
                if ctx.guild.get_channel(int(channel)) is not None
            ])

        if auto_reactions == "":
            auto_reactions = "Не настроено"

        emb = discord.Embed(title="Настройки бота на сервере", colour=discord.Color.green())
        emb.add_field(name="Настройки авто-реакций", value=auto_reactions)
        emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)


def setup(client):
    client.add_cog(ShowConfigs(client))
