import abc
import discord
import math
import datetime
import random
import typing

from core.utils.classes import TemplateRenderingModel
from jinja2 import Template
from asyncinit import asyncinit

client = None


DEFAULT_CONTEXT = {
    "len": len,
    "math": math,
    "round": round,
    "random": random,
    "list": list,
    "int": int,
    "dict": dict,
    "str": str,
    "upper": lambda msg: msg.upper(),
    "lower": lambda msg: msg.lower(),
    "capitalize": lambda msg: msg.capitalize(),
    "format": lambda msg, **args: msg.format(args),
    "split": lambda msg, sdata: msg.split(sdata),
    "join": lambda msg, value: msg.join(value),
    "reverse": lambda msg: msg[::-1],
    "keys": lambda msg: msg.keys(),
    "items": lambda msg: msg.items(),
    "values": lambda msg: msg.values(),
    "replace": lambda msg, old, new: msg.replace(old, new),
    "contains": lambda msg, word: True if word in msg.split(" ") else False,
}
MEMBER_STATUSES_DICT = {
    "dnd": "<:dnd:730391353929760870> - Не беспокоить",
    "online": "<:online:730393440046809108> - В сети",
    "offline": "<:offline:730392846573633626> - Не в сети",
    "idle": "<:sleep:730390502972850256> - Отошёл",
}
GUILD_REGION_EMOJIS = {
    "us_west": ":flag_us: — Запад США",
    "us_east": ":flag_us: — Восток США",
    "us_central": ":flag_us: — Центральный офис США",
    "us_south": ":flag_us: — Юг США",
    "sydney": ":flag_au: — Сидней",
    "eu_west": ":flag_eu: — Западная Европа",
    "eu_east": ":flag_eu: — Восточная Европа",
    "eu_central": ":flag_eu: — Центральная Европа",
    "singapore": ":flag_sg: — Сингапур",
    "russia": ":flag_ru: — Россия",
    "southafrica": ":flag_za:  — Южная Африка",
    "japan": ":flag_jp: — Япония",
    "brazil": ":flag_br: — Бразилия",
    "india": ":flag_in: — Индия",
    "hongkong": ":flag_hk: — Гонконг",
    "europe": ":flag_eu: - Европа"
}

class Embed:
    def __init__(
            self,
            title: str = discord.Embed.Empty,
            description: str = discord.Embed.Empty,
            url: str = discord.Embed.Empty,
            timestamp: datetime.datetime = discord.Embed.Empty,
            color: str = discord.Embed.Empty
    ):
        self._embed = discord.Embed(
            title=title,
            description=description,
            url=url,
            timestamp=timestamp,
            colour=int(hex(int(color.replace("#", ""), 16)), 0)
        )

    def add_field(self, name: str, value: str, inline: bool = True):
        self._embed.add_field(name=name, value=value, inline=inline)
        return self

    def set_author(self, name: str, icon: str = discord.Embed.Empty, url: str = discord.Embed.Empty):
        self._embed.set_author(name=name, icon_url=icon, url=url)
        return self

    def set_footer(self, text: str, icon: str = discord.Embed.Empty):
        self._embed.set_footer(text=text, icon_url=icon)
        return self

    def set_image(self, url: str):
        self._embed.set_image(url=url)
        return self

    def set_thumbnail(self, url: str):
        self._embed.set_thumbnail(url=url)
        return self


async def render(
        message: typing.Optional[discord.Message],
        member: discord.Member,
        render_text: str
):
    template = Template(render_text, enable_async=True)
    context = {
        "member": await Member(member),
        "guild": await Guild(member.guild),
        "bot": User(client.user),
        "Embed": Embed
    }
    if message is not None:
        context.update({
            "message": await Message(message),
            "channel": Channel(message.channel),
        })

    context.update(DEFAULT_CONTEXT)
    result = await template.render_async(context)
    return result


class Messageable(abc.ABC):
    def _get_channel(self):
        raise NotImplementedError

    async def send(self, content: str = None, embed: Embed = None):
        try:
            await self._get_channel().send(content=content, embed=embed._embed)
        except discord.HTTPException:
            return False
        else:
            return True


class Rank:
    __slots__ = (
        "_id",
        "exp",
        "lvl",
        "remaining_exp",
        "money",
        "coins",
        "bio",
        "reputation",
        "count_messages",
        "level_exp",
    )

    def __init__(self, data: TemplateRenderingModel):
        self._id = data.user_id
        self.exp = data.exp
        self.lvl = data.level
        self.level_exp = math.floor(
            9 * (self.lvl ** 2) + 50 * self.lvl + 125 * data.multi
        )
        self.remaining_exp = self.level_exp - self.exp
        self.money = data.money
        self.coins = data.coins
        self.bio = data.bio
        self.reputation = data.reputation

    def __str__(self):
        return client.get_user(self._id).name + client.get_user(self._id).discriminator


class Channel(Messageable):
    __slots__ = "id", "name", "position", "mention", "created_at", "topic"

    def __init__(self, data: discord.TextChannel):
        self.id = data.id
        self.name = data.name
        self.position = data.position
        self.created_at = data.created_at

        if isinstance(data, discord.TextChannel):
            self.mention = data.mention
            self.topic = data.topic

    def _get_channel(self):
        return client.get_channel(self.id)

    def __str__(self):
        return self.name


class VoiceState:
    __slots__ = (
        "deaf",
        "mute",
        "self_deaf",
        "self_mute",
        "self_stream",
        "self_video",
        "afk",
        "channel",
        "state",
    )

    def __init__(self, data: discord.VoiceState):
        self.state = False
        if data:
            self.state = True
            self.deaf = data.deaf
            self.mute = data.mute
            self.self_mute = data.self_mute
            self.self_deaf = data.self_deaf
            self.self_stream = data.self_stream
            self.self_video = data.self_video
            self.afk = data.afk
            self.channel = Channel(data.channel)

    def __str__(self):
        return str(self.state)


class Role:
    __slots__ = (
        "id",
        "name",
        "position",
        "permissions",
        "color",
        "created_at",
        "mention",
    )

    def __init__(self, data: discord.Role):
        self.id = data.id
        self.name = data.name
        self.position = data.position
        self.permissions = data.permissions
        self.color = data.color
        self.created_at = data.created_at
        self.mention = data.mention

    def __str__(self):
        return self.name


class User(Messageable):
    __slots__ = "id", "name", "bot", "avatar_url", "tag", "created_at", "discriminator"

    def __init__(self, data: discord.Member):
        self.id = data.id
        self.name = data.name
        self.bot = data.bot
        self.avatar_url = data.avatar_url
        self.discriminator = data.discriminator
        self.created_at = data.created_at

    def _get_channel(self):
        return client.get_user(self.id)

    def __str__(self):
        return self.name + "#" + self.discriminator


@asyncinit
class Member(User):
    __slots__ = (
        "permissions",
        "guild_id",
        "roles",
        "id",
        "name",
        "joined_at",
        "rank",
        "bot",
        "nick",
        "mention",
        "voice",
        "avatar_url",
        "discriminator",
        "created_at",
        "status",
    )

    async def __init__(self, data: discord.Member):
        super().__init__(data)
        self.guild_id = data.guild.id
        self.joined_at = data.joined_at
        self.nick = data.display_name
        self.mention = data.mention
        self.voice = VoiceState(data.voice)
        self.status = MEMBER_STATUSES_DICT[data.status.name]
        self.rank = Rank(TemplateRenderingModel(
            model=await client.database.sel_user(target=data),
            multi=(await client.database.sel_guild(guild=data.guild)).exp_multi
        ))
        self.roles = [Role(role) for role in data.roles]
        self.permissions = [perm[0] for perm in data.guild_permissions if perm[1]]

    def has_role(self, role_id: int) -> bool:
        return Role(client.get_guild(self.guild_id).get_role(role_id)) in self.roles

    def has_permission(self, permission: str) -> bool:
        return permission.lower() in self.permissions


@asyncinit
class Guild:
    __slots__ = (
        "id",
        "name",
        "icon_url",
        "owner",
        "member_count",
        "exp_multiplier",
        "region",
        "created_at",
        "region_emoji",
    )

    async def __init__(self, data: discord.Guild):
        self.id = data.id
        self.name = data.name
        self.icon_url = data.icon_url
        self.owner = await Member(data=data.owner)
        self.created_at = data.created_at
        self.member_count = data.member_count
        self.region = data.region
        self.region_emoji = GUILD_REGION_EMOJIS[self.region.name]

    def __str__(self):
        return self.name

    def get_channel(self, channel_id: int) -> Channel:
        return Channel(client.get_channel(channel_id))

    async def get_member(self, member_id: int) -> Member:
        return await Member(data=client.get_guild(self.id).get_member(member_id))

    def get_role(self, role_id: int) -> Role:
        return Role(client.get_guild(self.id).get_role(role_id))


@asyncinit
class Message:
    __slots__ = (
        "id",
        "content",
        "author",
        "created_at",
        "guild",
        "jump_url",
    )

    async def __init__(self, data: discord.Message):
        self.id = data.id
        self.guild = await Guild(data.guild)
        self.content = data.content
        self.author = await Member(data=data.author)
        self.created_at = data.created_at
        self.jump_url = data.jump_url

    def __str__(self):
        return self.content