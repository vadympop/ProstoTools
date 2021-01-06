import uuid
import datetime
import json
import typing
import time
import discord
import aiomysql
import mysql.connector


class DB:
	def __init__(self, client):
		self.client = client
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
					("""SELECT id FROM reminders WHERE user_id = %s AND user_id = %s"""),
					(member.id, member.id),
				)
				data = await cur.fetchall()
				limit_data = len(data) + 1
				if limit_data >= 25:
					return False
				await cur.execute(
					("""SELECT id FROM reminders WHERE guild_id = %s AND guild_id = %s"""),
					(member.guild.id, member.guild.id),
				)
				db_ids = await cur.fetchall()
				ids = [str(reminder[0]) for reminder in db_ids]
				ids.reverse()
				try:
					new_id = int(ids[0]) + 1
				except:
					new_id = 1

				sql = """INSERT INTO reminders VALUES (%s, %s, %s, %s, %s, %s)"""
				val = (new_id, member.id, member.guild.id, channel.id, time, text)

				await cur.execute(sql, val)
				await conn.commit()
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

	async def del_reminder(self, member: discord.Member, reminder_id: int) -> bool:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					f"""SELECT * FROM reminders WHERE guild_id = {member.guild.id}"""
				)
				reminders = await cur.fetchall()
				state = False
				for reminder in reminders:
					if reminder[0] == reminder_id:
						if reminder[1] == member.id:
							await cur.execute(
								("""DELETE FROM reminders WHERE id = %s AND guild_id = %s"""),
								(reminder_id, member.guild.id),
							)
							await conn.commit()
							state = True
							break
		return state

	async def set_warn(self, **kwargs) -> int:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					("""SELECT id FROM warns WHERE guild_id = %s AND guild_id = %s"""),
					(kwargs["target"].guild.id, kwargs["target"].guild.id),
				)
				db_ids = await cur.fetchall()
				ids = [warn[0] for warn in db_ids]
				ids.reverse()
				try:
					new_id = int(ids[0]) + 1
				except:
					new_id = 1

				await cur.execute(
					("""SELECT num FROM warns WHERE user_id = %s AND guild_id = %s"""),
					(kwargs["target"].id, kwargs["target"].guild.id),
				)
				db_nums = await cur.fetchall()
				nums = [num[0] for num in db_nums]
				nums.reverse()
				try:
					new_num = nums[0] + 1
				except:
					new_num = 1

				sql = """INSERT INTO warns VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
				val = (
					new_id,
					kwargs["target"].id,
					kwargs["target"].guild.id,
					kwargs["reason"],
					"True",
					str(datetime.datetime.today()),
					kwargs["author"],
					new_num,
				)

				await cur.execute(sql, val)
				await conn.commit()
		return new_id

	async def del_warn(self, guild_id: int, warn_id: int) -> typing.Union[bool, tuple]:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					("""UPDATE warns SET state = %s WHERE id = %s"""), ("False", warn_id)
				)
				await conn.commit()

				await cur.execute(
					("""SELECT user_id FROM warns WHERE id = %s AND id = %s"""),
					(warn_id, warn_id),
				)
				data = await cur.fetchone()
		return data

	async def set_mute(self, **kwargs) -> None:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					("""SELECT id FROM mutes WHERE guild_id = %s AND guild_id = %s"""),
					(kwargs["target"].guild.id, kwargs["target"].guild.id),
				)
				db_ids = await cur.fetchall()
				ids = [mute[0] for mute in db_ids]
				ids.reverse()
				try:
					new_id = int(ids[0]) + 1
				except:
					new_id = 1

				sql = """INSERT INTO mutes VALUES (%s, %s, %s, %s, %s, %s, %s)"""
				val = (
					new_id,
					kwargs["target"].id,
					kwargs["target"].guild.id,
					kwargs["reason"],
					str(datetime.datetime.fromtimestamp(kwargs["timestamp"])),
					str(datetime.datetime.today()),
					kwargs["author"],
				)

				await cur.execute(sql, val)
				await conn.commit()

	async def del_mute(self, member_id: int, guild_id: int) -> bool:
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				try:
					await cur.execute(
						("""DELETE FROM mutes WHERE user_id = %s AND guild_id = %s"""),
						(member_id, guild_id),
					)
					await conn.commit()

					state = True
				except:
					state = False
		return state

	async def get_mutes(self, guild_id):
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(
					("""SELECT * FROM mutes WHERE guild_id = %s AND guild_id = %s"""),
					(guild_id, guild_id),
				)
				data = await cur.fetchall()
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
						f"""SELECT * FROM punishments WHERE time < {float(time.time())}"""
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
					(
						"""DELETE FROM punishments WHERE member_id = %s AND guild_id = %s AND type = %s"""
					),
					(member.id, guild_id, type_punishment),
				)
				await conn.commit()

	async def sel_user(self, target, check=True) -> dict:
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
			prison = data[9]
			if prison == "True":
				prison = True
			elif prison == "False":
				prison = False

			warns = []
			for warn in db_warns:
				if warn[4] == "True":
					state = True
				elif warn[4] == "False":
					state = False
				warns.append(
					{
						"id": warn[0],
						"time": warn[5],
						"reason": warn[3],
						"author": warn[6],
						"num_warn": warn[7],
						"state": state,
						"guild_id": warn[2],
					}
				)

			dict_data = {
				"user_id": int(data[0]),
				"guild_id": int(data[1]),
				"lvl": int(data[2]),
				"exp": int(data[3]),
				"money": int(data[4]),
				"coins": int(data[5]),
				"text_channels": int(data[6]),
				"reputation": int(data[7]),
				"num_commands": int(data[8]),
				"prison": prison,
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
		sql_2 = """INSERT INTO guilds (guild_id, donate, prefix, api_key, shop_list, ignored_channels, auto_mod, clans, server_stats, voice_channel, moderators, auto_reactions, welcome, auto_roles, custom_commands, autoresponders) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
		val_2 = (
			guild.id,
			"False",
			"p.",
			str(uuid.uuid4()),
			json.dumps([]),
			json.dumps([]),
			json.dumps(
				{
					"anti_flud": False,
					"react_commands": False,
				}
			),
			json.dumps([]),
			json.dumps({}),
			json.dumps({}),
			json.dumps([]),
			json.dumps({}),
			json.dumps({}),
			json.dumps({}),
			json.dumps({}),
			json.dumps({}),
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

		donate = data[9]
		if donate == "True":
			donate = True
		elif donate == "False":
			donate = False

		dict_data = {
			"guild_id": int(data[0]),
			"purge": int(data[1]),
			"log_channel": int(data[2]),
			"all_message": int(data[3]),
			"textchannels_category": int(data[4]),
			"max_warns": int(data[5]),
			"exp_multi": float(data[6]),
			"idea_channel": int(data[7]),
			"timedelete_textchannel": int(data[8]),
			"donate": donate,
			"prefix": str(data[10]),
			"api_key": data[11],
			"server_stats": json.loads(data[12]),
			"voice_channel": json.loads(data[13]),
			"shop_list": json.loads(data[14]),
			"ignored_channels": json.loads(data[15]),
			"auto_mod": json.loads(data[16]),
			"clans": json.loads(data[17]),
			"moder_roles": json.loads(data[18]),
			"auto_reactions": json.loads(data[19]),
			"welcome": json.loads(data[20]),
			"auto_roles": json.loads(data[21]),
			"custom_commands": json.loads(data[22]),
			"autoresponders": json.loads(data[23]),
		}

		return dict_data

	def get_prefix(self, guild: discord.Guild):
		conn = mysql.connector.connect(
			user=self.DB_USER,
			password=self.DB_PASSWORD,
			host=self.DB_HOST,
			database=self.DB_DATABASE,
			port=3306
		)
		cursor = conn.cursor(buffered=True)

		cursor.execute(f"""SELECT prefix FROM guilds WHERE guild_id = {guild.id}""")
		data = cursor.fetchone()[0]
		cursor.close()
		return data

	def get_moder_roles(self, guild: discord.Guild):
		conn = mysql.connector.connect(
			user=self.DB_USER,
			password=self.DB_PASSWORD,
			host=self.DB_HOST,
			database=self.DB_DATABASE,
			port=3306
		)
		cursor = conn.cursor(buffered=True)

		cursor.execute(f"""SELECT moderators FROM guilds WHERE guild_id = {guild.id}""")
		data = cursor.fetchone()[0]
		cursor.close()
		return data

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
				await cur.execute(f"""SELECT id FROM bot_stats ORDER BY id DESC""")
				last_id = (await cur.fetchall())[0][0]
				try:
					new_id = int(last_id) + 1
				except:
					new_id = 0

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
					sql = """INSERT INTO bot_stats(id, count, timestamp, entity) VALUES(%s, %s, %s, %s)"""
					val = (new_id, new_main_count, datetime.datetime.now(), "all commands")

					await cur.execute(sql, val)
					await conn.commit()

				sql = """INSERT INTO bot_stats(id, count, timestamp, entity) VALUES(%s, %s, %s, %s)"""
				val = (new_id+1, new_count, datetime.datetime.now(), entity)

				await cur.execute(sql, val)
				await conn.commit()

	async def set_error(self, error_id: str, traceback: str, command: str):
		async with self.pool.acquire() as conn:
			async with conn.cursor() as cur:
				sql = """INSERT INTO errors(error_id, traceback, command) VALUES(%s, %s, %s)"""
				val = (error_id, traceback, command)
				await cur.execute(sql, val)
				await conn.commit()
