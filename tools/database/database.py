import uuid
import datetime
import json
import typing
import time as tm
import discord
import aiomysql
from tools.bases import AbcDatabase


class DB(AbcDatabase):
	def __init__(self, client):
		self.client = client
		self.cache = self.client.cache
		self.DB_HOST = self.client.config.DB_HOST
		self.DB_USER = self.client.config.DB_USER
		self.DB_PASSWORD = self.client.config.DB_PASSWORD
		self.DB_DATABASE = self.client.config.DB_DATABASE

	async def prepare(self):
		self.pool = await aiomysql.create_pool(
			host=self.DB_HOST,
			user=self.DB_USER,
			password=self.DB_PASSWORD,
			db=self.DB_DATABASE,
			port=3306,
			autocommit=True
		)

	async def close(self):
		if "pool" in self.__dict__:
			self.pool.close()
			await self.pool.wait_closed()

	async def add_giveaway(
			self,
			channel_id: int,
			message_id: int,
			creator: discord.Member,
			num_winners: int,
			time: int,
			name: str,
			prize: int
	) -> None:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				sql = """INSERT INTO giveaways(guild_id, channel_id, message_id, creator_id, num_winners, time, name, prize) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"""
				val = (creator.guild.id, channel_id, message_id, creator.id, num_winners, time, name, prize)
				await cur.execute(sql, val)
				await conn.commit()

	async def del_giveaway(self, giveaway_id: int) -> None:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					"""DELETE FROM giveaways WHERE id = %s""", (giveaway_id,)
				)
				await conn.commit()

	async def get_giveaways(self, guild_id: int) -> list:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					"""SELECT * FROM giveaways WHERE guild_id = %s""", (guild_id,)
				)
				data = await cur.fetchall()
		return data

	async def set_status_reminder(self, target_id: int, member_id: int, wait_for: str, type: str):
		if await self.get_status_reminder(
				target_id=target_id,
				member_id=member_id
		) is not None:
			return False

		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					f"""SELECT id FROM status_reminders WHERE member_id = {member_id}"""
				)
				ids = await cur.fetchall()
				if len(ids) > 20:
					return False

				await cur.execute(
					"""INSERT INTO status_reminders (target_id, member_id, wait_for, type) VALUES (%s, %s, %s, %s)""",
					(target_id, member_id, wait_for, type)
				)
				await conn.commit()
				await cur.execute("""SELECT LAST_INSERT_ID() FROM status_reminders""")
				data = (await cur.fetchone())[0]

		return data

	async def get_status_reminder(self, target_id: int = None, member_id: int = None):
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				if member_id is None and target_id is not None:
					await cur.execute(
						f"""SELECT * FROM status_reminders WHERE target_id = {target_id}""",
					)
					data = await cur.fetchall()
				elif member_id is not None and target_id is None:
					await cur.execute(
						f"""SELECT * FROM status_reminders WHERE member_id = {member_id}""",
					)
					data = await cur.fetchall()
				else:
					await cur.execute(
						"""SELECT * FROM status_reminders WHERE target_id = %s AND member_id = %s""",
						(target_id, member_id)
					)
					data = await cur.fetchone()
		return data

	async def del_status_reminder(self, status_reminder_id: int):
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					f"""SELECT id FROM status_reminders"""
				)
				reminders_ids = await cur.fetchall()
				if status_reminder_id not in [item[0] for item in reminders_ids]:
					return False
				else:
					await cur.execute(
						f"""DELETE FROM status_reminders WHERE id = {status_reminder_id}""",
					)
					await conn.commit()
					return True

	async def set_reminder(
		self,
		member: discord.Member,
		channel: discord.TextChannel,
		time: float,
		text: str,
	) -> typing.Union[int, bool]:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					f"""SELECT id FROM reminders WHERE user_id = {member.id}""",
				)
				reminders = await cur.fetchall()
				limit_data = len(reminders) + 1
				if limit_data >= 25:
					return False
				sql = """INSERT INTO reminders (user_id, guild_id, channel_id, time, text) VALUES (%s, %s, %s, %s, %s)"""
				val = (member.id, member.guild.id, channel.id, time, text)

				await cur.execute(sql, val)
				await conn.commit()

				await cur.execute("""SELECT LAST_INSERT_ID() FROM reminders""")
				new_id = (await cur.fetchone())[0]
		return new_id

	async def get_reminder(self, target: discord.Member = None) -> list:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				if target is not None:
					sql = """SELECT * FROM reminders WHERE user_id = %s AND guild_id = %s"""
					val = (target.id, target.guild.id)

					await cur.execute(sql, val)
					data = await cur.fetchall()
				elif not target:
					await cur.execute("""SELECT * FROM reminders""")
					data = await cur.fetchall()
		return data

	async def del_reminder(self, guild_id: int, reminder_id: int) -> bool:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					f"""SELECT id FROM reminders WHERE guild_id = {guild_id}"""
				)
				reminders_ids = await cur.fetchall()
				if reminder_id not in [item[0] for item in reminders_ids]:
					return False
				else:
					await cur.execute(
						("""DELETE FROM reminders WHERE id = %s AND guild_id = %s"""),
						(reminder_id, guild_id),
					)
					await conn.commit()
					return True

	async def set_warn(self, **kwargs) -> int:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					("""SELECT num FROM warns WHERE user_id = %s AND guild_id = %s"""),
					(kwargs["target"].id, kwargs["target"].guild.id),
				)
				db_nums = await cur.fetchall()
				new_num = len(db_nums)+1

				sql = """INSERT INTO warns(user_id, guild_id, reason, state, time, author, num) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
				val = (
					kwargs["target"].id,
					kwargs["target"].guild.id,
					kwargs["reason"],
					"True",
					tm.time(),
					kwargs["author"],
					new_num,
				)
				await cur.execute(sql, val)
				await conn.commit()

				await cur.execute("""SELECT LAST_INSERT_ID() FROM warns""")
				new_id = (await cur.fetchone())[0]
		return new_id

	async def del_warn(self, warn_id: int) -> tuple:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					("""UPDATE warns SET state = %s WHERE id = %s"""), ("False", warn_id)
				)
				await conn.commit()

				await cur.execute(
					f"""SELECT user_id FROM warns WHERE id = {warn_id}"""
				)
				data = await cur.fetchone()
		return data

	async def set_mute(self, **kwargs) -> int:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				sql = """INSERT INTO mutes (user_id, guild_id, reason, active_to, time, author) VALUES (%s, %s, %s, %s, %s, %s)"""
				val = (
					kwargs["target"].id,
					kwargs["target"].guild.id,
					kwargs["reason"],
					kwargs["timestamp"],
					tm.time(),
					kwargs["author"],
				)
				await cur.execute(sql, val)
				await conn.commit()

				await cur.execute("""SELECT LAST_INSERT_ID() FROM mutes""")
				new_id = (await cur.fetchone())[0]
		return new_id

	async def del_mute(self, member_id: int, guild_id: int) -> None:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					("""DELETE FROM mutes WHERE user_id = %s AND guild_id = %s"""),
					(member_id, guild_id),
				)
				await conn.commit()

	async def get_mutes(self, guild_id: int):
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					f"""SELECT * FROM mutes WHERE guild_id = {guild_id}""",
				)
				data = await cur.fetchall()
		return data

	async def get_mute(self, guild_id: int, member_id: int):
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					("""SELECT * FROM mutes WHERE guild_id = %s AND member_id = %s"""),
					(guild_id, member_id),
				)
				data = await cur.fetchone()
		return data

	async def set_punishment(
		self,
		type_punishment: str,
		time: float,
		member: discord.Member,
		role_id: int = 0,
		**kwargs,
	) -> None:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					"""SELECT * FROM punishments WHERE member_id = %s AND guild_id = %s""",
					(member.id, member.guild.id),
				)
				data = await cur.fetchone()

				if type_punishment == "mute":
					await self.set_mute(
						timestamp=time,
						target=member,
						reason=kwargs["reason"],
						author=kwargs["author"],
					)

				if data is None:
					sql = """INSERT INTO punishments VALUES (%s, %s, %s, %s, %s)"""
					val = (member.id, member.guild.id, time, type_punishment, role_id)

					await cur.execute(sql, val)
					await conn.commit()
				else:
					sql = """UPDATE punishments SET time = %s WHERE member_id = %s AND guild_id = %s"""
					val = (time, member.id, member.guild.id)

					await cur.execute(sql, val)
					await conn.commit()

	async def get_punishment(self, member: discord.Member = None) -> list:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				if member is not None:
					sql = """SELECT * FROM punishments WHERE member = %s AND member = %s"""
					val = member.id

					await cur.execute(sql, val)
					data = await cur.fetchone()
				else:
					await cur.execute(
						f"""SELECT * FROM punishments WHERE time < {float(tm.time())}"""
					)
					data = await cur.fetchall()
		return data

	async def del_punishment(
		self, member: discord.Member, guild_id: int, type_punishment: str
	) -> None:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				if type_punishment == "mute":
					await self.del_mute(member.id, member.guild.id)

				await cur.execute(
					"""DELETE FROM punishments WHERE member_id = %s AND guild_id = %s AND type = %s""",
					(member.id, guild_id, type_punishment),
				)
				await conn.commit()

	async def sel_user(self, target, check: bool = True) -> dict:
		sql_1 = """SELECT * FROM users WHERE user_id = %s AND guild_id = %s"""
		val_1 = (target.id, target.guild.id)
		sql_2 = """INSERT INTO users (user_id, guild_id, prison, profile, items, pets, clan, messages, transantions, bio) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
		val_2 = (
			target.id,
			target.guild.id,
			"False",
			"lime",
			json.dumps([]),
			json.dumps([]),
			"",
			json.dumps([0, 0, None]),
			json.dumps([]),
			"",
		)
		sql_4 = """SELECT * FROM warns WHERE user_id = %s AND guild_id = %s"""
		val_4 = (target.id, target.guild.id)

		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(sql_1, val_1)
				data = await cur.fetchone()
				await cur.execute(sql_4, val_4)
				db_warns = await cur.fetchall()

				if check:
					if data is None:
						await cur.execute(sql_2, val_2)
						await conn.commit()

						await cur.execute(sql_1, val_1)
						data = await cur.fetchone()

		if data is not None:
			warns = []
			for warn in db_warns:
				warns.append(
					{
						"id": warn[0],
						"time": warn[5],
						"reason": warn[3],
						"author": warn[6],
						"num_warn": warn[7],
						"state": warn[4] == "True",
						"guild_id": warn[2],
					}
				)

			dict_data = {
				"user_id": int(data[0]),
				"guild_id": int(data[1]),
				"level": int(data[2]),
				"exp": int(data[3]),
				"money": int(data[4]),
				"coins": int(data[5]),
				"text_channel": int(data[6]),
				"reputation": int(data[7]),
				"num_commands": int(data[8]),
				"prison": data[9] == "True",
				"profile": str(data[10]),
				"bio": str(data[11]),
				"clan": str(data[12]),
				"items": json.loads(data[13]),
				"pets": json.loads(data[14]),
				"warns": warns,
				"messages": json.loads(data[15]),
				"transantions": json.loads(data[16]),
			}
			return dict_data

	async def sel_guild(self, guild) -> dict:
		sql_1 = """SELECT * FROM guilds WHERE guild_id = %s AND guild_id = %s"""
		val_1 = (guild.id, guild.id)
		sql_2 = """INSERT INTO guilds (guild_id, donate, prefix, api_key, audit, shop_list, ignored_channels, auto_mod, clans, server_stats, voice_channel, moderators, auto_reactions, welcome, auto_roles, custom_commands, autoresponders, rank_message, commands_settings, warns_settings) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
		val_2 = (
			guild.id,
			"False",
			"p.",
			str(uuid.uuid4()),
			json.dumps({}),
			json.dumps([]),
			json.dumps([]),
			json.dumps(
				{
					"anti_flud": {"state": False},
					"anti_invite": {"state": False},
					"anti_caps": {"state": False},
					"react_commands": False,
					"captcha": {"state": False}
				}
			),
			json.dumps([]),
			json.dumps({}),
			json.dumps({}),
			json.dumps([]),
			json.dumps({}),
			json.dumps({}),
			json.dumps({}),
			json.dumps([]),
			json.dumps({}),
			json.dumps({
				"state": False
			}),
			json.dumps(
				{command: {
					"state": True,
					"ignore_channels": [],
					"ignore_roles": [],
					"target_roles": [],
					"target_channels": []
				} for command in [
					command.name
					for cog in self.client.cogs
					for command in self.client.get_cog(cog).get_commands()
					if cog.lower() not in ("owner", "help", "jishaku")
				]}
			),
			json.dumps({"max": 3, "punishment": None})
		)

		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(sql_1, val_1)
				data = await cur.fetchone()

				if data is None:
					await cur.execute(sql_2, val_2)
					await conn.commit()

					await cur.execute(sql_1, val_1)
					data = await cur.fetchone()

		dict_data = {
			"guild_id": int(data[0]),
			"purge": int(data[1]),
			"all_message": int(data[2]),
			"textchannels_category": int(data[3]),
			"exp_multi": float(data[4]),
			"idea_channel": int(data[5]),
			"timedelete_textchannel": int(data[6]),
			"donate": data[7] == "True",
			"prefix": str(data[8]),
			"api_key": data[9],
			"server_stats": json.loads(data[10]),
			"voice_channel": json.loads(data[11]),
			"shop_list": json.loads(data[12]),
			"ignored_channels": json.loads(data[13]),
			"auto_mod": json.loads(data[14]),
			"clans": json.loads(data[16]),
			"moder_roles": json.loads(data[16]),
			"auto_reactions": json.loads(data[17]),
			"welcome": json.loads(data[18]),
			"auto_roles": json.loads(data[19]),
			"custom_commands": json.loads(data[20]),
			"autoresponders": json.loads(data[21]),
			"audit": json.loads(data[22]),
			"rank_message": json.loads(data[23]),
			"commands_settings": json.loads(data[24]),
			"warns_settings": json.loads(data[25])
		}
		return dict_data

	async def get_prefix(self, guild: discord.Guild):
		cached_guild = await self.cache.get(str(guild.id))
		if await self.cache.exists(str(guild.id)):
			if cached_guild is not None:
				return cached_guild

		return (await self.execute(
			"""SELECT prefix FROM guilds WHERE guild_id = %s""",
			(guild.id),
			fetchone=True
		))[0]

	async def get_moder_roles(self, guild: discord.Guild):
		return (await self.execute(
			"""SELECT moderators FROM guilds WHERE guild_id = %s""",
			(guild.id),
			fetchone=True
		))[0]

	async def execute(
		self, query: str, val: typing.Union[tuple, list] = (), fetchone: bool = False
	) -> list:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(query, val)
				await conn.commit()
				if fetchone:
					data = await cur.fetchone()
				else:
					data = await cur.fetchall()
		return data

	async def update(self, table: str, **kwargs):
		where = kwargs.pop("where")
		columns = []
		values = []
		for key, value in kwargs.items():
			columns.append(f"{key} = %s")
			values.append(value)
		query = ", ".join(columns)
		if "prefix" in kwargs.keys():
			await self.cache.set(str(where['guild_id']), kwargs["prefix"])

		await self.execute(
			f"""UPDATE {table} SET {query} WHERE {' AND '.join([f"{key} = {value}" for key, value in where.items()])}""",
			values
		)

	async def add_amout_command(
		self, entity: str = "all commands", add_counter: typing.Union[int, float] = None
	) -> None:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				try:
					await cur.execute(
						f"""SELECT * FROM bot_stats WHERE entity = '{entity}'"""
					)
					data = await cur.fetchall()
				except:
					data = [(0, 0,)]

				await cur.execute(
					f"""SELECT * FROM bot_stats WHERE entity = 'all commands'"""
				)
				main_data = await cur.fetchall()
				counter = [str(stat[1]) for stat in data]
				counter.reverse()
				try:
					new_count = int(counter[0]) + 1
				except:
					new_count = 1

				main_counter = [str(stat[1]) for stat in main_data]
				main_counter.reverse()
				try:
					new_main_count = int(main_counter[0]) + 1
				except:
					new_main_count = 1

				if add_counter is not None:
					new_count = add_counter

				if add_counter is None:
					sql = """INSERT INTO bot_stats(count, timestamp, entity) VALUES( %s, %s, %s)"""
					val = (new_main_count, datetime.datetime.utcnow(), "all commands")

					await cur.execute(sql, val)
					await conn.commit()

				sql = """INSERT INTO bot_stats(count, timestamp, entity) VALUES( %s, %s, %s)"""
				val = (new_count, datetime.datetime.utcnow(), entity)

				await cur.execute(sql, val)
				await conn.commit()

	async def set_error(self, error_id: str, traceback: str, command: str):
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				sql = """INSERT INTO errors(error_id, traceback, command, time) VALUES(%s, %s, %s, %s)"""
				val = (error_id, traceback, command, datetime.datetime.now())
				await cur.execute(sql, val)
				await conn.commit()
