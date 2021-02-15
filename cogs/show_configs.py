import discord
import json
from tools.paginator import Paginator
from discord.utils import get
from discord.ext import commands


async def check_role(ctx):
    data = json.loads(await ctx.bot.database.get_moder_roles(guild=ctx.guild))
    roles = ctx.guild.roles[::-1]
    data.append(roles[0].id)

    if data != []:
        for role_id in data:
            role = get(ctx.guild.roles, id=role_id)
            if role in ctx.author.roles:
                return True
        return ctx.author.guild_permissions.administrator
    else:
        return ctx.author.guild_permissions.administrator


class ShowConfigs(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.FOOTER = self.client.config.FOOTER_TEXT
        self.commands = [
            command.name
            for cog in self.client.cogs
            for command in self.client.get_cog(cog).get_commands()
            if cog.lower() not in ("help", "owner", "jishaku")
        ]

    @commands.group(
        name="show-config",
        help="**Команды групы:** server-stats, ignored-channels, auto-moderate, auto-reactions, audit",
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def show_config(self, ctx):
        if ctx.invoked_subcommand is None:
            data = await self.client.database.sel_guild(guild=ctx.guild)
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
    Категория приватных текстовых каналов - `{category}`
    Максимальное количество предупрежденний - `{data['warns_settings']["max"]}`
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
        name="server-stats",
        usage="show-config server-stats",
        description="**Покажет настройки статистики сервера**",
    )
    @commands.check(check_role)
    async def server_stats(self, ctx):
        data = (await self.client.database.sel_guild(guild=ctx.guild))["server_stats"]
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
        name="ignored-channels",
        usage="show-config ignored-channels",
        description="**Покажет игнорируемые каналы**",
    )
    @commands.check(check_role)
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
        name="auto-moderate",
        usage="show-config auto-moderate",
        description="**Покажет настройки авто-модерации**",
    )
    @commands.check(check_role)
    async def auto_moderate(self, ctx):
        data = (await self.client.database.sel_guild(guild=ctx.guild))["auto_mod"]
        categories = {
            "anti_invite": "Анти-приглашения",
            "anti_flud": "Анти-флуд",
            "react_commands": "Команды по реакциям",
            "captcha": "Каптча",
            "anti_caps": "Анти-капс"
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
            if key == "react_commands" or key == "captcha":
                if setting:
                    settings.append(
                        f"**{categories[key]}** - `Включено`"
                    )
                else:
                    settings.append(
                        f"**{categories[key]}** - `Выключено`"
                    )
            else:
                if setting["state"]:
                    message = ("выключено"
                               if "message" not in data[key].keys()
                               else f"отправляеться в `{message_types[data[key]['message']['type']]}`, сообщения - `{data[key]['message']['text'][:30]}...`")
                    punishment_time = ((f", время наказания - `{data[key]['punishment']['time']}`" if data[key]['punishment']['time'] is not None else "")
                                       if "punishment" in data[key].keys()
                                       else "")
                    punishment = (f"""тип наказания `{punishment_types[data[key]['punishment']['type']]}`{punishment_time}"""
                                  if "punishment" in data[key].keys()
                                  else "не установлено")
                    target_roles = ("не настроено"
                                    if "target_roles" not in data[key].keys()
                                    else f"установлено {len(data[key]['target_roles'])} ролей")
                    target_channels = ("не настроено"
                                    if "target_channels" not in data[key].keys()
                                    else f"установлено {len(data[key]['target_channels'])} каналов")
                    ignore_channels = ("не настроено"
                                    if "ignore_channels" not in data[key].keys()
                                    else f"установлено {len(data[key]['ignore_channels'])} каналов")
                    ignore_roles = ("не настроено"
                                    if "ignore_roles" not in data[key].keys()
                                    else f"установлено {len(data[key]['ignore_roles'])} ролей")
                    info = f"**{categories[key]}**:\n1. Сообщения - {message}\n2. Наказания - {punishment}\n3. Целевые каналы - {target_channels}\n4. Игнорируемые каналы - {ignore_channels}\n5. Целевые роли - {target_roles}\n6. Игнорируемые роли - {ignore_roles}"
                    if key == "anti_invite" or key == "anti_caps":
                        delete_message = ("выключено"
                                   if "delete_message" not in data[key].keys()
                                   else f"включено")
                        info += f"\n7. Удаления сообщений - {delete_message}"
                    settings.append(info)
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
        name="auto-reactions",
        usage="show-config auto-reactions",
        description="**Покажет настройки авто-реакций**",
    )
    @commands.check(check_role)
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

    @show_config.command(
        usage="show-config audit",
        description="**Покажет настройки аудита**",
    )
    @commands.check(check_role)
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

    @commands.command(
        aliases=["commandssettings", "commandsettings", "cs"],
        name="commands-settings",
        usage="commands-settings |Названия команды|",
        help="**Примеры использования:**\n1. {Prefix}commands-settings\n2. {Prefix}commands-settings crime\n\n**Пример 1:** Покажет настройки всех команд\n**Пример 2:** Покажет настройки указаной команды",
    )
    async def commands_settings(self, ctx, command_name: str = None):
        commands_settings = (await self.client.database.sel_guild(guild=ctx.guild))["commands_settings"]
        if command_name is None:
            pages = []
            prefix = str(await self.client.database.get_prefix(guild=ctx.guild))
            start_embed = discord.Embed(
                title="Справка по настройкам команд",
                description=f"Для навигации используйте реакции ниже или\n`{prefix}commands-settings [Названия команды]`",
                colour=discord.Color.green()
            )
            start_embed.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
            start_embed.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)

            pages.append(start_embed)
            for command_name, command_setting in commands_settings.items():
                description = f"""
Состояния: `{"Включена" if command_setting["state"] else "Выключена"}`
Целевые роли: `{str(len(command_setting["target_roles"]))+" ролей" if command_setting["target_roles"] else "Не настроено"}` 
Целевые каналы: `{str(len(command_setting["target_channels"]))+" каналов" if command_setting["target_channels"] else "Не настроено"}`
Игнорируемые роли: `{str(len(command_setting["ignore_roles"]))+" ролей" if command_setting["ignore_roles"] else "Не настроено"}`
Игнорируемые каналы: `{str(len(command_setting["ignore_channels"]))+" каналов" if command_setting["ignore_channels"] else "Не настроено"}`
                """
                emb = discord.Embed(
                    title="Команда - "+command_name,
                    description=description,
                    colour=discord.Color.green()
                )
                emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
                emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
                pages.append(emb)

            start_message = await ctx.send(embed=start_embed)
            paginator = Paginator(
                ctx=ctx,
                message=start_message,
                embeds=pages,
                timeout=350,
                footer=True
            )
            await paginator.start()
        else:
            if command_name.lower() in ("help", "setting"):
                emb = await self.client.utils.create_error_embed(
                    ctx, "Вы не можете просмотреть настройки этой команды!"
                )
                await ctx.send(embed=emb)
                return

            if command_name.lower() not in self.commands:
                emb = await self.client.utils.create_error_embed(
                    ctx, "Такой команды не существует!"
                )
                await ctx.send(embed=emb)
                return

            command_setting = commands_settings[command_name]
            description = f"""
Состояния: `{"Включена" if command_setting["state"] else "Выключена"}`
Целевые роли: `{str(len(command_setting["target_roles"])) + " ролей" if command_setting["target_roles"] else "Не настроено"}` 
Целевые каналы: `{str(len(command_setting["target_channels"])) + " каналов" if command_setting["target_channels"] else "Не настроено"}`
Игнорируемые роли: `{str(len(command_setting["ignore_roles"])) + " ролей" if command_setting["ignore_roles"] else "Не настроено"}`
Игнорируемые каналы: `{str(len(command_setting["ignore_channels"])) + " каналов" if command_setting["ignore_channels"] else "Не настроено"}`
            """
            emb = discord.Embed(
                title="Команда - " + command_name,
                description=description,
                colour=discord.Color.green()
            )
            emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)


def setup(client):
    client.add_cog(ShowConfigs(client))
