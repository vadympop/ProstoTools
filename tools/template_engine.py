import discord
import math
import random
import typing
from jinja2 import Template
from asyncinit import asyncinit

client = None


async def render(
		message: typing.Union[discord.Message, None],
		member: discord.Member,
		data: dict,
		render_text: str
):
	template = Template(render_text, autoescape=False)
	context = {
		"member": Member(member, data),
		"guild": await Guild(member.guild),
		"bot": User(client.user),
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
	if message is not None:
		context.update({
			"message": await Message(message),
			"channel": Channel(message.channel),
		})
	result = template.render(context)
	return result


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

	def __init__(self, data):
		self._id = data["user_id"]
		self.exp = data["exp"]
		self.lvl = data["level"]
		self.level_exp = math.floor(
			9 * (self.lvl ** 2) + 50 * self.lvl + 125 * data["multi"]
		)
		self.remaining_exp = self.level_exp - self.exp
		self.money = data["money"]
		self.coins = data["coins"]
		self.bio = data["bio"]
		self.reputation = data["reputation"]

	def __str__(self):
		return client.get_user(self._id).name + client.get_user(self._id).discriminator


class Channel:
	__slots__ = "id", "name", "position", "mention", "created_at", "topic"

	def __init__(self, data):
		self.id = data.id
		self.name = data.name
		self.position = data.position
		self.created_at = data.created_at

		if isinstance(data, discord.TextChannel):
			self.mention = data.mention
			self.topic = data.topic

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

	def __init__(self, data):
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

	def __init__(self, data):
		self.id = data.id
		self.name = data.name
		self.position = data.position
		self.permissions = data.permissions
		self.color = data.color
		self.created_at = data.created_at
		self.mention = data.mention

	def __str__(self):
		return self.name


class User:
	__slots__ = "id", "name", "bot", "avatar_url", "tag", "created_at", "discriminator"

	def __init__(self, data):
		self.id = data.id
		self.name = data.name
		self.bot = data.bot
		self.avatar_url = data.avatar_url
		self.discriminator = data.discriminator
		self.created_at = data.created_at

	def __str__(self):
		return self.name + "#" + self.discriminator


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
		"discrininator",
		"created_at",
		"_member_statuses",
		"status",
	)

	def __init__(self, data, db_data):
		super().__init__(data)
		self._member_statuses = {
			"dnd": "<:dnd:730391353929760870> - Не беспокоить",
			"online": "<:online:730393440046809108> - В сети",
			"offline": "<:offline:730392846573633626> - Не в сети",
			"idle": "<:sleep:730390502972850256> - Отошёл",
		}

		self.guild_id = data.guild.id
		self.joined_at = data.joined_at
		self.nick = data.display_name
		self.mention = data.mention
		self.voice = VoiceState(data.voice)
		self.status = self._member_statuses[data.status.name]
		self.rank = Rank(db_data)
		self.roles = [Role(role) for role in data.roles]
		self.permissions = [perm[0] for perm in data.guild_permissions if perm[1]]

	def __str__(self):
		return self.name + "#" + self.discriminator

	def has_role(self, id: int) -> bool:
		if Role(client.get_guild(self.guild_id).get_role(id)) in self.roles:
			return True
		else:
			return False

	def has_permission(self, permission: str) -> bool:
		if permission.lower() in self.permissions:
			return True
		else:
			return False


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
		"_region_emojis",
		"__databasedataofmember",
	)

	async def __init__(self, data):
		self.exp_multiplier = (await client.database.sel_guild(data))["exp_multi"]
		self.__databasedataofmember = await client.database.sel_user(data.owner)
		self.__databasedataofmember.update({"multi": self.exp_multiplier})
		self._region_emojis = {
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

		self.id = data.id
		self.name = data.name
		self.icon_url = data.icon_url
		self.owner = Member(data.owner, self.__databasedataofmember)
		self.created_at = data.created_at
		self.member_count = data.member_count
		self.region = data.region
		self.region_emoji = self._region_emojis[self.region.name]

	def __str__(self):
		return self.name

	def get_channel(self, id: int) -> Channel:
		return Channel(client.get_channel(id))

	async def get_member(self, id: int) -> Member:
		member = client.get_guild(self.id).get_member(id)
		db_member = await client.database.sel_user(member)
		db_member.update({"multi": self.exp_multiplier})
		return Member(member, db_member)

	def get_role(self, id: int) -> Role:
		return Role(client.get_guild(self.id).get_role(id))


@asyncinit
class Message:
	__slots__ = (
		"id",
		"content",
		"author",
		"created_at",
		"exp_multipier",
		"__databasedataofmember",
		"guild",
		"jump_url",
	)

	async def __init__(self, data):
		self.guild = await Guild(data.guild)
		self.__databasedataofmember = await client.database.sel_user(data.author)
		self.__databasedataofmember.update({"multi": self.guild.exp_multiplier})

		self.id = data.id
		self.content = data.content
		self.author = Member(data.author, self.__databasedataofmember)
		self.created_at = data.created_at
		self.jump_url = data.jump_url

	def __str__(self):
		return self.content
