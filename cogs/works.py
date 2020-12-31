import discord

from discord.ext import commands
from random import randint


class Works(commands.Cog, name="Works"):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT

	@commands.group(
		help=f"""**Команды групы:** barman, treasurehunter, cleaner, windowasher, loader\n\n"""
	)
	@commands.cooldown(2, 7200, commands.BucketType.member)
	async def work(self, ctx):
		if ctx.invoked_subcommand is None:
			self.work.reset_cooldown(ctx)
			emb = discord.Embed(
				title="Список работ",
				description=f"**Грузчик - {self.client.database.get_prefix(ctx.guild)}work loader**\nДля работы нужно иметь более 3-го уровня и перчатки, кулдавн 3 часа после двух попыток, зарабатывает от 80$ до 100$\n\n**Охотник за кладом - {self.client.database.get_prefix(ctx.guild)}work treasure-hunter**\nДля работы нужен металоискатель(любого уровня), кулдавн 5 часов, может ничего не найти(0$, металоискатель 2-го уровня повышает шанс найти клад на 30%), если найдёт от 1$ до 500$\n\n**Барман - {self.client.database.get_prefix(ctx.guild)}work barman**\nДля работы нужно иметь более 4-го уровня, кулдавн 3 часа, зарабатывает от 150 до 200\n\n**Уборщик - {self.client.database.get_prefix(ctx.guild)}work cleaner**\nДля повышения эфективности работы нужно иметь веник или швабру, кулдавн 2 часа после 3 попыток\n\n**Мойщик окон - {self.client.database.get_prefix(ctx.guild)}work window-washer**\nДля работы нужно иметь более 5-го уровня, кулдавн 5 часов, от 250$ до 300$, может упасть и потерять 300$",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

	@work.command(
		usage="loader",
		description="**Робота грузчик**"
	)
	@commands.cooldown(2, 10800, commands.BucketType.member)
	async def loader(self, ctx):
		data = await self.client.database.sel_user(target=ctx.author)
		lvl_member = data["lvl"]
		rand_num = randint(80, 100)
		cur_state_pr = data["prison"]
		cur_items = data["items"]

		if not cur_state_pr:
			if lvl_member >= 3:
				if "gloves" in cur_items:
					sql = """UPDATE users SET money = money + %s WHERE user_id = %s AND guild_id = %s"""
					val = (rand_num, ctx.author.id, ctx.guild.id)

					await self.client.database.execute(sql, val)

					emb = discord.Embed(
						description=f"**За работу вы получили: {rand_num}$. Продолжайте стараться!**",
						colour=discord.Color.green(),
					)
					emb.set_author(
						name=self.client.user.name, icon_url=self.client.user.avatar_url
					)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
				else:
					emb = discord.Embed(
						description="**У вас нет необходимых предметов!**",
						colour=discord.Color.green(),
					)
					emb.set_author(
						name=self.client.user.name, icon_url=self.client.user.avatar_url
					)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					return
			else:
				emb = discord.Embed(
					description="**У вас не достаточний уровень для этой работы!**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				return

		elif cur_state_pr:
			emb = discord.Embed(
				description="**Вы сейчас в тюрме. На эту работу нельзя выходить во время заключения!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return

	@work.command(
		aliases=["treasure-hunter"],
		usage="treasure-hunter",
		description="**Робота охотник за сокровищами**"
	)
	@commands.cooldown(1, 18000, commands.BucketType.member)
	async def treasurehunter(self, ctx):
		data = await self.client.database.sel_user(target=ctx.author)
		lvl_member = data["lvl"]
		cur_state_pr = data["prison"]
		cur_items = data["items"]
		cur_pets = data["pets"]

		async def func_trHunt(shans: int):
			rand_num_1 = randint(0, 100)
			shans_2 = 100 - shans
			if "loupe" in cur_pets:
				shans_2 += shans_2*20//100

			if rand_num_1 >= shans:
				rand_num_2 = randint(1, 500)
				if "helmet" in cur_pets:
					rand_num_2 += rand_num_2*10//100

				sql = """UPDATE users SET money = money + %s WHERE user_id = %s AND guild_id = %s"""
				val = (rand_num_2, ctx.author.id, ctx.guild.id)

				await self.client.database.execute(sql, val)

				msg_content = (
					f"**За работу вы получили: {rand_num_2}$. Продолжайте стараться!**"
				)
				return msg_content

			elif rand_num_1 <= shans_2:
				msg_content = "**Сегодня вы ничего не нашли**"
				return msg_content

		if not cur_state_pr:
			if lvl_member >= 2:
				if cur_items is not None:
					if "metal_1" in cur_items and "metal_2" in cur_items:
						msg_content = await func_trHunt(20)
						emb = discord.Embed(
							description=msg_content, colour=discord.Color.green()
						)
						emb.set_author(
							name=self.client.user.name,
							icon_url=self.client.user.avatar_url,
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
					elif "metal_1" in cur_items:
						msg_content = await func_trHunt(50)
						emb = discord.Embed(
							description=msg_content, colour=discord.Color.green()
						)
						emb.set_author(
							name=self.client.user.name,
							icon_url=self.client.user.avatar_url,
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
					elif "metal_2" in cur_items:
						msg_content = await func_trHunt(20)
						emb = discord.Embed(
							description=msg_content, colour=discord.Color.green()
						)
						emb.set_author(
							name=self.client.user.name,
							icon_url=self.client.user.avatar_url,
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)
					else:
						emb = discord.Embed(
							description="**У вас нет не обходимых предметов, метало искателей! Купите метало искатель!**",
							colour=discord.Color.green(),
						)
						emb.set_author(
							name=self.client.user.name,
							icon_url=self.client.user.avatar_url,
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)

						await ctx.send(embed=emb)
						return
				elif cur_items == []:
					emb = discord.Embed(
						description="**У вас нет не обходимых предметов, метало искателей! Купите метало искатель!**",
						colour=discord.Color.green(),
					)
					emb.set_author(
						name=self.client.user.name, icon_url=self.client.user.avatar_url
					)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
					return
			else:
				emb = discord.Embed(
					description="**У вас не достаточний уровень для этой работы!**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				return
		elif cur_state_pr:
			emb = discord.Embed(
				description="**Вы сейчас в тюрме. На эту работу нельзя выходить во время заключения!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return

	@work.command(
		usage="barman",
		description="**Робота бармэн**"
	)
	@commands.cooldown(2, 10800, commands.BucketType.member)
	async def barman(self, ctx):
		data = await self.client.database.sel_user(target=ctx.author)
		lvl_member = data["lvl"]
		rand_num = 150 + randint(0, 50)
		cur_state_pr = data["prison"]

		if not cur_state_pr:
			if lvl_member >= 4:
				sql = """UPDATE users SET money = money + %s WHERE user_id = %s AND guild_id = %s"""
				val = (rand_num, ctx.author.id, ctx.guild.id)

				await self.client.database.execute(sql, val)

				emb = discord.Embed(
					description=f"**За сегодняшнюю работу в баре: {rand_num}$. Не употребляйте много алкоголя :3**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
			else:
				emb = discord.Embed(
					description="**У вас не достаточний уровень для этой работы!**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				return
		elif cur_state_pr:
			emb = discord.Embed(
				description="**Вы сейчас в тюрме. На эту работу нельзя выходить во время заключения!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return

	@work.command(
		usage="cleaner",
		description="**Робота уборщик**"
	)
	@commands.cooldown(3, 7200, commands.BucketType.member)
	async def cleaner(self, ctx):
		data = await self.client.database.sel_user(target=ctx.author)
		cur_items = data["items"]
		cur_state_pr = data["prison"]

		async def cleaner_func(rnum1: int, rnum2: int):
			rnum = randint(rnum1, rnum2)

			sql = """UPDATE users SET money = money + %s WHERE user_id = %s AND guild_id = %s"""
			val = (rnum, ctx.author.id, ctx.guild.id)

			await self.client.database.execute(sql, val)

			msg_content = f"**За сегодняшнюю уборку вы получили: {rnum}$**"
			return msg_content

		if cur_items is not None:
			if "broom" in cur_items:
				msg = await cleaner_func(50, 60)
				emb = discord.Embed(description=msg, colour=discord.Color.green())
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
			elif "mop" in cur_items:
				msg = await cleaner_func(60, 80)
				emb = discord.Embed(description=msg, colour=discord.Color.green())
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
			elif "mop" in cur_items and "broom" in cur_items:
				msg = await cleaner_func(60, 80)
				emb = discord.Embed(description=msg, colour=discord.Color.green())
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
			else:
				msg = await cleaner_func(40, 50)
				emb = discord.Embed(description=msg, colour=discord.Color.green())
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
		elif cur_items == []:
			msg = await cleaner_func(40, 50)
			emb = discord.Embed(description=msg, colour=discord.Color.green())
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

		if cur_state_pr and data["money"] > 0:
			emb = discord.Embed(
				description="**Вы успешно погасили борг и выйшли с тюрмы!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			sql = (
				"""UPDATE users SET prison = %s WHERE user_id = %s AND guild_id = %s"""
			)
			val = ("False", ctx.author.id, ctx.guild.id)

			await self.client.database.execute(sql, val)

	@work.command(
		aliases=["window-washer"],
		usage="window-washer",
		description="**Робота мойщик окон**"
	)
	@commands.cooldown(1, 18000, commands.BucketType.member)
	async def windowasher(self, ctx):
		data = await self.client.database.sel_user(target=ctx.author)
		lvl_member = data["lvl"]
		rand_num_1 = randint(1, 2)
		cur_state_pr = data["prison"]

		if not cur_state_pr:
			if lvl_member >= 5:
				if rand_num_1 == 1:
					rand_num_2 = randint(250, 300)
					cur_money = data["money"] + rand_num_2
					emb = discord.Embed(
						description=f"**За мойку окон на высоком здании в получили {rand_num_2}$**",
						colour=discord.Color.green(),
					)
					emb.set_author(
						name=self.client.user.name, icon_url=self.client.user.avatar_url
					)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)
				elif rand_num_1 == 2:
					cur_money = data["money"] - 300
					emb = discord.Embed(
						description=f"**Вы упали и потеряли 300$**",
						colour=discord.Color.green(),
					)
					emb.set_author(
						name=self.client.user.name, icon_url=self.client.user.avatar_url
					)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.send(embed=emb)

				sql = """UPDATE users SET money = %s WHERE user_id = %s AND guild_id = %s"""
				val = (cur_money, ctx.author.id, ctx.guild.id)

				await self.client.database.execute(sql, val)

			else:
				emb = discord.Embed(
					description="**У вас не достаточний уровень для этой работы!**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				return
		elif cur_state_pr:
			emb = discord.Embed(
				description="**Вы сейчас в тюрме. На эту работу нельзя выходить во время заключения!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return


def setup(client):
	client.add_cog(Works(client))
