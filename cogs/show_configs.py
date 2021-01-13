import discord
from discord.ext import commands


class ShowConfigs(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.FOOTER = self.client.config.FOOTER_TEXT

    @commands.group(
        name="show-config",
        help="**Команды групы:** server-stats, ignored-channels, auto-moderate, auto-reactions, audit",
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def show_config(self, ctx):
        if ctx.invoked_subcommand is None:
            data = await self.client.database.sel_guild(guild=ctx.guild)
            idea_channel_obj = ctx.guild.get_channel(data['idea_channel'])
            if idea_channel_obj is None:
                idea_channel = "Не указан"
            else:
                idea_channel = "#"+idea_channel_obj.name

            category_obj = ctx.guild.get_channel(data["textchannels_category"])
            if category_obj is None:
                category = "Не указана"
            else:
                category = category_obj.name

            if not data["rank_message"]["state"]:
                rank_message = "Стандартное"
            else:
                rank_message = "Включено"

            if "channel_id" not in data["voice_channel"].keys():
                voice_channel = "Выключены"
            else:
                channel = ctx.guild.get_channel(data["voice_channel"]["channel_id"])
                voice_channel = f"Включены({channel.name})" if channel is not None else f"Включены"

            main_settings = f"""Префикс - `{data['prefix']}`
    Канал идей - `{idea_channel}`
    Категория приватных текстовых каналов - `{category}`
    Максимальное количество предупрежденний - `{data['max_warns']}`
    Множитель опыта - `{data['exp_multi'] * 100}%`
    Время удаления приватного текстового канала - `{data['timedelete_textchannel']}мин`
    Сообщения о повышении уровня - `{rank_message}`
    Приватные голосовые комнаты - `{voice_channel}`
    """

            emb = discord.Embed(title="Настройки бота на сервере", colour=discord.Color.green())
            emb.add_field(name="Основные настройки", value=main_settings)
            emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

    @show_config.command(
        name="server-stats"
    )
    async def server_stats(self, ctx):
        data = (await self.client.database.sel_guild(guild=ctx.guild))["server_stats"]
        if data == {}:
            server_stats = "Не настроено"
        else:
            server_stats = "\n".join([
                f"`{category}` - `#{ctx.guild.get_channel(channel).name}`"
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
        name="ignored-channels"
    )
    async def ignored_channels(self, ctx):
        data = (await self.client.database.sel_guild(guild=ctx.guild))["ignored_channels"]
        if data == []:
            ignored_channels = "Не указаны"
        else:
            ignored_channels = "\n".join([
                f"`#{ctx.guild.get_channel(channel).name}`"
                for channel in data
                if ctx.guild.get_channel(channel) is not None
            ])

        if ignored_channels == "":
            ignored_channels = "Не указаны"

        emb = discord.Embed(title="Настройки бота на сервере", colour=discord.Color.green())
        emb.add_field(name="Игнорируемые каналы", value=ignored_channels)
        emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)

    @show_config.command(
        name="auto-moderate"
    )
    async def auto_moderate(self, ctx):
        data = (await self.client.database.sel_guild(guild=ctx.guild))["auto_mod"]
        categories = {
            "anti_invite": "Анти-приглашения",
            "anti_flud": "Анти-флуд",
            "react_commands": "Команды по реакциям"
        }
        message_types = {
            "dm": "лс",
            "channel": "канал"
        }
        punishment_types = {
            "mute": "мьют",
            "ban": "бан",
            "soft-ban": "апаратный бан",
            "warn": "предупреждения",
            "kick": "кик"
        }
        settings = []
        for key, setting in data.items():
            if key == "react_commands":
                if setting:
                    settings.append(
                        f"**{categories[key]}** - Включено"
                    )
                else:
                    settings.append(
                        f"**{categories[key]}** - `Выключено`"
                    )
            else:
                if setting["state"]:
                    message = ("Выключено"
                               if "message" not in data[key].keys()
                               else f"отправляеться в `{message_types[data[key]['message']['type']]}`, сообщения - `{data[key]['message']['text'][:30]}...`")
                    punishment = f"тип наказания `{punishment_types[data[key]['punishment']['type']]}`, время наказания - `{data[key]['punishment']['time']}`"
                    settings.append(
                        f"**{categories[key]}**:\n1. Сообщения - {message}\n2. Наказания - {punishment}"
                    )
                else:
                    settings.append(
                        f"**{categories[key]}** - `Выключено`"
                    )

        emb = discord.Embed(title="Настройки бота на сервере", colour=discord.Color.green())
        emb.add_field(name="Настройки авто-модерации", value="\n\n".join(settings))
        emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)

    @show_config.command(
        name="auto-reactions"
    )
    async def auto_reactions(self, ctx):
        data = (await self.client.database.sel_guild(guild=ctx.guild))["auto_reactions"]
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

    @show_config.command()
    async def audit(self, ctx):
        data = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]
        convert_categories = {
            "moderate": "модерация",
            "economy": "экономика",
            "clans": "кланы",
            "member_update": "учасник_обновился",
            "member_unban": "участник_разбанен",
            "member_ban": "участник_забанен",
            "message_edit": "сообщения_изменено",
            "message_delete": "сообщения_удалено"
        }

        if data == {}:
            audit = "Не настроено"
        else:
            audit = "\n".join([
                f"`{convert_categories[category]}` - `#{ctx.guild.get_channel(channel).name}`"
                if ctx.guild.get_channel(channel) is not None
                else f"`{convert_categories[category]}` - `?`"
                for category, channel in data.items()
            ])

        if audit == "":
            audit = "Не настроено"

        emb = discord.Embed(title="Настройки бота на сервере", colour=discord.Color.green())
        emb.add_field(name="Настройки аудита", value=audit)
        emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)


def setup(client):
    client.add_cog(ShowConfigs(client))
