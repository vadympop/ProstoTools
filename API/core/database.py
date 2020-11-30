import os
import aiomysql
import asyncio


class Database:
	def __init__(self):
		pass

	async def get_users(self) -> dict:
		conn = await aiomysql.connect(
			host="localhost", user="root", password=os.environ["DB_PASSWORD"], db="data"
		)

		async with conn.cursor() as cur:
			await cur.execute("SELECT * FROM users")
			users = await cur.fetchall()

		conn.close()
		return {
			user[0]: {
				"guild_id": user[1],
				"lvl": user[2],
				"exp": user[3],
				"money": user[4],
				"coins": user[5],
				"text_channels": user[6],
				"reputation": user[7],
				"prison": user[8],
				"profile": user[9],
				"clan": user[11],
				"items": user[12],
				"pets": user[13],
				"messages": user[14],
				"transantions": user[15],
			}
			for user in users
		}

	async def get_user(self, guild_id: int, user_id: int) -> dict:
		conn = await aiomysql.connect(
			host="localhost", user="root", password=os.environ["DB_PASSWORD"], db="data"
		)

		async with conn.cursor() as cur:
			await cur.execute(
				f"SELECT * FROM users WHERE guild_id = {guild_id} AND user_id = {user_id}"
			)
			user = await cur.fetchone()

		conn.close()
		return {
			user[0]: {
				"guild_id": user[1],
				"lvl": user[2],
				"exp": user[3],
				"money": user[4],
				"coins": user[5],
				"text_channels": user[6],
				"reputation": user[7],
				"prison": user[8],
				"profile": user[9],
				"clan": user[11],
				"items": user[12],
				"pets": user[13],
				"transantions": user[15],
			}
		}

	async def get_user_bio(self, user_id: int) -> dict:
		conn = await aiomysql.connect(
			host="localhost", user="root", password=os.environ["DB_PASSWORD"], db="data"
		)

		async with conn.cursor() as cur:
			await cur.execute(f"SELECT bio FROM users WHERE user_id = {user_id}")
			bio = (await cur.fetchone())[0]

		return {"bio": bio}

	async def get_user_warns(self, user_id: int, guild_id: int) -> list:
		conn = await aiomysql.connect(
			host="localhost", user="root", password=os.environ["DB_PASSWORD"], db="data"
		)

		async with conn.cursor() as cur:
			await cur.execute(
				f"SELECT * FROM warns WHERE user_id = {user_id} AND guild_id = {guild_id}"
			)
			warns = await cur.fetchall()

		return list(warns)

	async def get_user_punishments(self, user_id: int, guild_id: int) -> list:
		conn = await aiomysql.connect(
			host="localhost", user="root", password=os.environ["DB_PASSWORD"], db="data"
		)

		async with conn.cursor() as cur:
			await cur.execute(
				f"SELECT * FROM punishments WHERE member_id = {user_id} AND guild_id = {guild_id}"
			)
			punishments = await cur.fetchall()

		return list(punishments)
