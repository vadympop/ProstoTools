import datetime
import random
import math
import io
import uuid
import discord

from core import Paginator
from core.utils.economy import parse_inventory, crime_member, rob_func
from core.services.database.models import User
from core.bases.cog_base import BaseCog
from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw, ImageOps
from random import randint


class Economy(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.IMAGES_PATH = self.client.config.IMAGES_PATH
		self.FONT = self.client.config.FONT
		self.SAVE = self.client.config.SAVE_IMG

	@commands.command(
		description="Показывает лидеров сервера",
		usage="top",
		help="**Примеры использования:**\n1. {Prefix}top\n\n**Пример 1:** Покажет таблицу лидеров сервера",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def top(self, ctx):
		emb = discord.Embed(title="Лидеры сервера", colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)

		embeds = [emb]
		num_to_medal = {
			1: ' :first_place:',
			2: " :second_place:",
			3: " :third_place:"
		}
		num = 1
		for user in User.objects.filter(
				guild_id=ctx.guild.id
		).exclude(exp__lte=0).order_by("-exp"):
			member = ctx.guild.get_member(user.user_id)
			if member is not None and not member.bot:
				users_per_page = 20*len(embeds)
				if num > users_per_page:
					if users_per_page > 20:
						embeds.append(emb)

					emb = discord.Embed(title=f"Лидеры сервера", colour=discord.Color.green())
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)

				field_name = f"#{num}"
				if 1 <= num <= 3:
					field_name += num_to_medal[num]

				emb.add_field(
					name=f"{field_name} {member}",
					value=f"Уровень: `{user.level}` **|** Опыт: `{user.exp}` **|** Репутация: `{user.reputation}` **|** Деньги: `{user.money}`",
					inline=False,
				)
				num += 1

		message = await ctx.send(embed=embeds[0])
		if len(embeds) > 1:
			paginator = Paginator(ctx, message, embeds, footer=True)
			await paginator.start()

	@commands.command(
		aliases=["reputation"],
		description="Добавления репутации указаному пользователю",
		usage="rep [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}rep @Участник\n2. {Prefix}rep 660110922865704980\n\n**Пример 1:** Добавит репутацию упомянутому участнику\n**Пример 2:** Добавит репутацию участнику с указаным id",
	)
	@commands.cooldown(1, 3600, commands.BucketType.member)
	async def rep(self, ctx, member: discord.Member):
		if member == ctx.author:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете изменять свою репутацию!"
			)
			await ctx.send(embed=emb)
			self.rep.reset_cooldown(ctx)
			return

		if member.bot:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете менять репутацию бота!"
			)
			await ctx.send(embed=emb)
			self.rep.reset_cooldown(ctx)
			return

		await self.client.database.update(
			"users",
			where={"user_id": member.id, "guild_id": ctx.guild.id},
			reputation=(await self.client.database.sel_user(target=member)).reputation+1
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass

	@commands.command(
		description="Ежедневная награда",
		usage="daily",
		help="**Примеры использования:**\n1. {Prefix}daily\n\n**Пример 1:** Выдаст вам рандомное количество денег от 50$ до 1000$",
	)
	@commands.cooldown(1, 86400, commands.BucketType.member)
	async def daily(self, ctx):
		nums = [100, 250, 1000, 500, 50]
		rand_num = random.choice(nums)

		await self.client.database.update(
			"users",
			where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
			money=(await self.client.database.sel_user(target=ctx.author)).money+rand_num
		)

		emb = discord.Embed(
			description=f"**Вы получили ежедневну награду! В размере - {rand_num}$**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		aliases=["shoplist"],
		name="shop-list",
		description="Показывает список покупаемых предметов",
		usage="shop-list",
		help="**Примеры использования:**\n1. {Prefix}shop-list\n\n**Пример 1:** Показывает шоп-лист сервера",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def shoplist(self, ctx):
		data = await self.client.database.sel_guild(guild=ctx.guild)
		shoplist = data.shop_list
		content = ""

		if shoplist:
			for shop_role in shoplist:
				role = ctx.guild.get_role(shop_role[0])
				content += f"{role.mention} - {shop_role[1]}\n"

			emb = discord.Embed(
				title="Список товаров",
				description=f"**Роли:**\n{content}\n**Товары:**\nМеталоискатель 1-го уровня - 500$\nМеталоискатель 2-го уровня 1000$\nСим-карта - 100$\nТелефон - 1100$\nМетла - 500 коинов\nШвабра - 2000 коинов\nТекстовый канал - 100$\nПерчатки - 600$\n\n**Лут боксы:**\nЛут бокс Common - 800$\nЛут бокс Rare - 1800$\nЛут бокс Epic - 4600$\nЛут бокс Legendary - 9800$\nЛут бокс Imposible - 19600$",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif not shoplist:
			emb = discord.Embed(
				title="Список товаров",
				description=f"**Товары:**\nМеталоискатель 1-го уровня - 500$\nМеталоискатель 2-го уровня 1000$\nСим-карта - 100$\nТелефон - 1100$\nМетла - 500 коинов\nШвабра - 2000 коинов\nТекстовый канал - 100$\nПерчатки - 600$\n\n**Лут боксы:**\nЛут бокс Common - 800$\nЛут бокс Rare - 1800$\nЛут бокс Epic - 4600$\nЛут бокс Legendary - 9800$\nЛут бокс Imposible - 19600$",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

	@commands.command(
		aliases=["sendmoney"],
		name="send-money",
		description="Этой командой можно отправить свои деньги другому пользователю",
		usage="send-money [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}send-money @Участник 1000\n2. {Prefix}send-money 660110922865704980 1000\n\n**Пример 1:** Отправляет 1000$ упомянутому участнику\n**Пример 2:** Отправляет 1000$ участнику с указаным id",
	)
	@commands.cooldown(1, 1800, commands.BucketType.member)
	async def sendmoney(self, ctx, member: discord.Member, num: int):
		if member.bot:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете передавать деньги боту!"
			)
			await ctx.send(embed=emb)
			return

		if num <= 0:
			emb = await self.client.utils.create_error_embed(ctx, "Укажите число пересылаемых денег больше 0!")
			await ctx.send(embed=emb)
			return

		data1 = await self.client.database.sel_user(target=ctx.author)
		data2 = await self.client.database.sel_user(target=member)

		if data1.prison:
			emb = await self.client.utils.create_error_embed(
				ctx, "У вас заблокирование транзакции, так как вы в тюрьме!"
			)
			await ctx.send(embed=emb)
			self.sendmoney.reset_cooldown(ctx)
			return

		if data2.prison:
			emb = await self.client.utils.create_error_embed(
				ctx, "В указаного пользователя заблокирование транзакции, так как он в тюрме!"
			)
			await ctx.send(embed=emb)
			self.sendmoney.reset_cooldown(ctx)
			return

		if data1.money < num:
			emb = await self.client.utils.create_error_embed(
				ctx, "У вас недостаточно средств для транзакции!"
			)
			await ctx.send(embed=emb)
			self.sendmoney.reset_cooldown(ctx)
			return

		info_transantion_1 = {
			"to": member.id,
			"from": ctx.author.id,
			"cash": num,
			"time": str(await self.client.utils.get_guild_time(ctx.guild)),
			"id": str(uuid.uuid4),
			"guild_id": ctx.guild.id,
		}
		info_transantion_2 = {
			"to": member.id,
			"from": ctx.author.id,
			"cash": num,
			"time": str(await self.client.utils.get_guild_time(ctx.guild)),
			"id": str(uuid.uuid4),
			"guild_id": ctx.guild.id,
		}

		data1.transactions.append(info_transantion_1)
		data2.transactions.append(info_transantion_2)

		await self.client.database.update(
			"users",
			where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
			transactions=data1.transactions,
			money=data1.money-num
		)
		await self.client.database.update(
			"users",
			where={"user_id": member.id, "guild_id": ctx.guild.id},
			transactions=data2.transactions,
			money=data2.money+num
		)

		emb = discord.Embed(
			description=f"**Вы успешно совершили транзакцию `{member.mention}` на суму `{num}$`**",
			colour=discord.Color.green(),
		)
		emb.set_author(
			name=self.client.user.name, icon_url=self.client.user.avatar_url
		)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(
			description=f"**Вам {ctx.author.mention} перевел деньги на суму `{num}$`, сервер `{ctx.guild.name}`**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await member.send(embed=emb)

	@commands.command(
		aliases=["trans", "transactions"],
		name="my-transactions",
		description="Показывает все ваши транзакции на текущем сервере",
		usage="my-transactions",
		help="**Примеры использования:**\n1. {Prefix}my-transactions\n\n**Пример 1:** Показывает список ваших транзакций",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def trans(self, ctx):
		transactions = (await self.client.database.sel_user(target=ctx.author)).transactions

		if not transactions:
			emb = discord.Embed(
				title=f"Транзакции пользователя - `{ctx.author}`",
				description="Пользователь не совершал транзакций",
				colour=discord.Color.green(),
			)
		else:
			emb = discord.Embed(
				title=f"Транзакции пользователя - `{ctx.author}`",
				colour=discord.Color.green(),
			)

		for transantion in transactions:
			transantion_id = transantion["id"]
			transantion_time = transantion["time"]
			transantion_to = ctx.guild.get_member(transantion["to"])
			if transantion_to is None:
				transantion_to = transantion["to"]
			transantion_from = ctx.guild.get_member(transantion["from"])
			transantion_cash = transantion["cash"]

			emb.add_field(
				value=f"Время - {transantion_time}, Id - {transantion_id}",
				name=f"Сумма - {transantion_cash}, кому - `{transantion_to}`, от кого - `{transantion_from}`",
				inline=False,
			)

		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="Открывает указаный лут бокс",
		usage="open [Лут бокс]",
		help="**Примеры использования:**\n1. {Prefix}open box-E\n\n**Пример 1:** Открывает указаный лут-бокс",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def open(self, ctx, box: str = None):
		if box is not None:
			boxes = ["box-C", "box-R", "box-E", "box-L", "box-I"]
			box = box[:-2].lower() + f"-{box[-1:].upper()}"

		if box is None:
			emb = discord.Embed(
				title="Укажите пожалуйста бокс!",
				description=f"**Обычный бокс - box-C\nРедкий бокс - box-R\nЭпический бокс - box-E\nЛегендарный бокс - box-L\nНевероятный бокс - box-I**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return
		elif box not in boxes:
			emb = discord.Embed(
				title="Укажите пожалуйста бокс правильно!",
				description=f"**Обычный бокс - box-C\nРедкий бокс - box-R\nЭпический бокс - box-E\nЛегендарный бокс - box-L\nНевероятный бокс - box-I**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return

		dict_boxes = {
			"box-C": ["Обычный бокс", 4000],
			"box-R": ["Редкий бокс", 6000],
			"box-E": ["Эпический бокс", 9000],
			"box-L": ["Легендарный бокс", 12000],
			"box-I": ["Невероятный бокс", 16000],
		}
		data = await self.client.database.sel_user(target=ctx.author)
		rand_num_1 = randint(1, 100)
		rand_items_1 = ["mop", "broom", "sim", "metal_1"]
		rand_items_2 = ["gloves", "tel", "metal_2"]
		rand_money = 0
		msg_content = ""
		state = False
		pet = None
		all_pets = ["cat", "dog", "helmet", "loupe", "parrot", "hamster"]
		dict_items = {
			"mop": "Швабра",
			"broom": "Метла",
			"sim": "Сим-карта",
			"metal_1": "Металоискатель 1-го уровня",
			"gloves": "Перчатки",
			"tel": "Телефон",
			"metal_2": "Металоискатель 2-го уровня",
		}

		for item in data.items:
			if isinstance(item, list):
				if item[0] == box:
					state = True
					if item[1] <= 1:
						data.items.remove(item)
					elif item[1] > 1:
						item[1] -= 1

		if state:
			if box == boxes[0]:
				if rand_num_1 <= 5:
					pet = [all_pets[2], boxes[0]]
					msg_content = "С обычного бокса вам выпал питомец - Каска(Увеличивает стоимость клада)"
					# Каска

				elif 5 < rand_num_1 <= 25:
					pet = [all_pets[1], boxes[0]]
					msg_content = (
						"С обычного бокса вам выпал питомец - Собачка(Обычный питомец)"
					)
					# Собачка

				elif 25 < rand_num_1 <= 50:
					pet = [all_pets[0], boxes[0]]
					msg_content = (
						"С обычного бокса вам выпал питомец - Кошка(Обычный питомец)"
					)
					# Кошка

				elif rand_num_1 > 50:
					rand_num_2 = randint(1, 2)

					if rand_num_2 == 1:
						rand_money = randint(10, 600)
					elif rand_num_2 == 2:
						rand_money = randint(400, 1000)
					msg_content = f"Вам не очень повезло и с обычного бокса выпали деньги в размере - {rand_money}"

			elif box == boxes[1]:
				if rand_num_1 <= 1:
					pet = [all_pets[5], boxes[1]]
					msg_content = "С редкого бокса вам выпал питомец - Хомяк(Увеличивает выпадения коинов)"
					# Хомяк

				elif 1 < rand_num_1 <= 7:
					pet = [all_pets[2], boxes[1]]
					msg_content = "С редкого бокса вам выпал питомец - Каска(Увеличивает стоимость клада)"
					# Каска

				elif 7 < rand_num_1 <= 30:
					pet = [all_pets[1], boxes[1]]
					msg_content = (
						"С редкого бокса вам выпал питомец - Собачка(Обычный питомец)"
					)
					# Собачка

				elif 30 < rand_num_1 <= 60:
					pet = [all_pets[0], boxes[1]]
					msg_content = (
						"С редкого бокса вам выпал питомец - Кошка(Обычный питомец)"
					)
					# Кошка

				elif rand_num_1 > 60:
					rand_num_2 = randint(1, 2)

					if rand_num_2 == 1:
						rand_money = randint(100, 1000)
					elif rand_num_2 == 2:
						rand_money = randint(600, 2000)
					msg_content = f"Вам не очень повезло и с редкого бокса выпали деньги в размере - {rand_money}"

			elif box == boxes[2]:
				if rand_num_1 <= 4:
					pet = [all_pets[5], boxes[2]]
					msg_content = "С эпического бокса вам выпал питомец - Хомяк(Увеличивает выпадения коинов)"
					# Хомяк

				elif 4 < rand_num_1 <= 10:
					pet = [all_pets[2], boxes[2]]
					msg_content = "С эпического бокса вам выпал питомец - Каска(Увеличивает стоимость клада)"
					# Каска

				elif 10 < rand_num_1 <= 33:
					pet = [all_pets[1], boxes[2]]
					msg_content = "С эпического бокса вам выпал питомец - Собачка(Обычный питомец)"
					# Собачка

				elif 33 < rand_num_1 <= 63:
					pet = [all_pets[0], boxes[2]]
					msg_content = (
						"С эпического бокса вам выпал питомец - Кошка(Обычный питомец)"
					)
					# Кошка

				elif rand_num_1 > 63:
					rand_num_2 = randint(1, 4)

					if rand_num_2 == 1:
						rand_money = randint(1000, 3000)
						msg_content = f"Вам не очень повезло и с эпического бокса выпали деньги в размере - {rand_money}"

					elif rand_num_2 == 2:
						rand_money = randint(1800, 4900)
						msg_content = f"Вам не очень повезло и с эпического бокса выпали деньги в размере - {rand_money}"

					elif rand_num_2 == 3:
						choice = random.choice(rand_items_1)
						if choice in data.items:
							rand_money_2 = randint(1000, 2000)
							msg_content = f"Вам не очень повезло и с эпического бокса выпали деньги в размере - {rand_money_2}"
						else:
							data.items.append(choice)
							msg_content = f"С эпического бокса выпал предмет - {dict_items[choice]}"

					elif rand_num_2 == 4:
						choice = random.choice(rand_items_2)
						if choice in data.items:
							rand_money_2 = randint(1000, 2000)
							msg_content = f"Вам не очень повезло и с эпического бокса выпали деньги в размере - {rand_money_2}"
						else:
							data.items.append(choice)
							msg_content = f"С эпического бокса выпал предмет - {dict_items[choice]}"

			elif box == boxes[3]:
				if rand_num_1 <= 10:
					pet = [all_pets[5], boxes[3]]
					msg_content = "С легендарного бокса вам выпал питомец - Хомяк(Увеличивает выпадения коинов)"
					# Хомяк

				elif 10 < rand_num_1 <= 30:
					pet = [all_pets[2], boxes[3]]
					msg_content = "С легендарного бокса вам выпал питомец - Каска(Увеличивает стоимость клада)"
					# Каска

				elif 30 < rand_num_1 <= 33:
					pet = [all_pets[3], boxes[3]]
					msg_content = "С легендарного бокса вам выпал питомец - Лупа(Увеличивает шанс найти клад)"
					# Лупа

				elif 33 < rand_num_1 <= 63:
					pet = [all_pets[0], boxes[3]]
					msg_content = "С легендарного бокса вам выпал питомец - Кошка(Обычный питомец)"
					# Кошка

				elif rand_num_1 > 63:
					rand_num_2 = randint(1, 4)

					if rand_num_2 == 1:
						rand_money = randint(5000, 11000)
						msg_content = f"Вам не очень повезло и с легендарного бокса выпали деньги в размере - {rand_money}"

					elif rand_num_2 == 2:
						rand_money = randint(7000, 15000)
						msg_content = f"Вам не очень повезло и с легендарного бокса выпали деньги в размере - {rand_money}"

					elif rand_num_2 == 3:
						choice = random.choice(rand_items_1)
						if choice in data.items:
							rand_money_2 = randint(6000, 8000)
							msg_content = f"Вам не очень повезло и с легендарного бокса выпали деньги в размере - {rand_money_2}"
						else:
							data.items.append(choice)
							msg_content = f"С легендарного бокса выпал предмет - {dict_items[choice]}"

					elif rand_num_2 == 4:
						choice = random.choice(rand_items_2)
						if choice in data.items:
							rand_money_2 = randint(6000, 8000)
							msg_content = f"Вам не очень повезло и с легендарного бокса выпали деньги в размере - {rand_money_2}"
						else:
							data.items.append(choice)
							msg_content = f"С легендарного бокса выпал предмет - {dict_items[choice]}"

			elif box == boxes[4]:
				if rand_num_1 <= 25:
					pet = [all_pets[5], boxes[4]]
					msg_content = "С невероятного бокса вам выпал питомец - Хомяк(Увеличивает выпадения коинов)"
					# Хомяк

				elif 25 < rand_num_1 <= 50:
					pet = [all_pets[2], boxes[4]]
					msg_content = "С невероятного бокса вам выпал питомец - Каска(Увеличивает стоимость клада)"
					# Каска

				elif 50 < rand_num_1 <= 65:
					pet = [all_pets[3], boxes[4]]
					msg_content = "С невероятного бокса вам выпал питомец - Лупа(Увеличивает шанс найти клад)"
					# Лупа

				elif 65 < rand_num_1 <= 70:
					pet = [all_pets[4], boxes[4]]
					msg_content = "С невероятного бокса вам выпал питомец - Попугай(Уменьшает шанс быть пойманым)"
					# Попугай

				elif rand_num_1 > 70:
					rand_num_2 = randint(1, 5)

					if rand_num_2 == 1:
						rand_num_3 = randint(1, 3)

						if 1 <= rand_num_3 <= 2:
							rand_money = randint(5000, 12000)
							msg_content = f"Вам не очень повезло и с невероятного бокса выпали деньги в размере - {rand_money}"

						elif rand_num_3 > 2:
							rand_money = randint(50000, 120000)
							msg_content = f"С невероятного бокса вы сорвали джек-пот в размере - {rand_money}!"

					elif rand_num_2 == 2:
						rand_money = randint(19000, 25000)
						msg_content = f"Вам не очень повезло и с невероятного бокса выпали деньги в размере - {rand_money}"

					elif rand_num_2 == 3:
						choice = random.choice(rand_items_1)
						if choice in data.items:
							rand_money_2 = randint(18000, 20000)
							msg_content = f"Вам не очень повезло и с невероятного бокса выпали деньги в размере - {rand_money_2}"
						else:
							data.items.append(choice)
							msg_content = f"С невероятного бокса выпал предмет - {dict_items[choice]}"

					elif rand_num_2 == 4:
						choice = random.choice(rand_items_2)
						if choice in data.items:
							rand_money_2 = randint(18000, 20000)
							msg_content = f"Вам не очень повезло и с невероятного бокса выпали деньги в размере - {rand_money_2}"
						else:
							data.items.append(choice)
							msg_content = f"С невероятного бокса выпал предмет - {dict_items[choice]}"

			data.money += rand_money
			if pet is not None:
				if pet[0] in data.pets:
					data.coins += dict_boxes[pet[1]][1]
					msg_content = f"К сожалению выйграный питомец уже есть в вашем инвертаре, по этому вам выпали коины в размере - {dict_boxes[pet[1]][1]}"
				else:
					data.pets.append(pet[0])

			emb = discord.Embed(
				title=f"Бокс - {dict_boxes[box][0]}",
				description=f"**{msg_content}**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			await self.client.database.update(
				"users",
				where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
				items=data.items,
				pets=data.pets,
				money=data.money,
				coins=data.coins
			)
		elif not state:
			emb = await self.client.utils.create_error_embed(
				ctx, "В вашем инвертаре нет такого лут-бокса!"
			)
			await ctx.send(embed=emb)

	@commands.command(
		aliases=["removerole"],
		name="remove-role",
		description="Удаляет указанную роль из профиля пользователя",
		usage="remove-role [@Участник] [@Роль]",
		help="**Примеры использования:**\n1. {Prefix}remove-role @Участник @Роль\n2. {Prefix}remove-role 660110922865704980 717776604461531146\n\n**Пример 1:** Удаляет упомянутую роль в упомянутого участника\n**Пример 2:** Удаляет роль с указаным id в участника с указаным id",
	)
	@commands.cooldown(1, 14400, commands.BucketType.member)
	@commands.has_permissions(administrator=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def remove_role(self, ctx, member: discord.Member, role: discord.Role):
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit

		if member.bot:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете снимать роль боту!"
			)
			await ctx.send(embed=emb)
			return

		if role.is_integration():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль управляется интеграцией!")
			await ctx.send(embed=emb)
			return

		if role.is_bot_managed():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль управляется ботом!")
			await ctx.send(embed=emb)
			return

		if role.is_premium_subscriber():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль используеться для бустером сервера!")
			await ctx.send(embed=emb)
			return

		data = await self.client.database.sel_user(target=member)
		items = data.items
		if role.id in items:
			items.remove(role.id)

			try:
				await member.remove_roles(role)
			except:
				pass

			await self.client.database.update(
				"users",
				where={"user_id": member.id, "guild_id": ctx.guild.id},
				items=items,
			)

			emb = discord.Embed(
				title="Успех!",
				description=f"**Снятия роли прошло успешно, роль - {role.mention} была удаленна из его профиля!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

		if "economy" in audit.keys():
			e = discord.Embed(
				description=f"У пользователя `{str(member)}` была убрана роль",
				colour=discord.Color.orange(),
				timestamp=await self.client.utils.get_guild_time(ctx.guild),
			)
			e.add_field(
				name="Модератором",
				value=str(ctx.author),
				inline=False,
			)
			e.add_field(
				name="Роль",
				value=role.name,
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Удаления роли пользователя",
				icon_url=ctx.author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["economy"])
			if channel is not None:
				await channel.send(embed=e)

	@commands.command(
		aliases=["addmoney"],
		name="add-money",
		description="Добавляет деньги указанному участнику",
		usage="add-money [@Участник] [Количество]",
		help="**Примеры использования:**\n1. {Prefix}add-money @Участник 1000\n2. {Prefix}add-money 660110922865704980 1000\n\n**Пример 1:** Добавляет 1000 денег упомянутому участнику\n**Пример 2:** Добавляет 1000 денег участнику с указанным id",
	)
	@commands.has_permissions(administrator=True)
	@commands.cooldown(1, 14400, commands.BucketType.member)
	async def add_money(self, ctx, member: discord.Member, num: int):
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit

		if member.bot:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете изменять профиль бота!"
			)
			await ctx.send(embed=emb)
			return

		if member == ctx.author:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return

		if num <= 0:
			emb = await self.client.utils.create_error_embed(ctx, "Укажите добавляемое значения больше 0!")
			await ctx.send(embed=emb)
			return

		if num >= 1000000000:
			emb = await self.client.utils.create_error_embed(
				ctx, "Указано слишком большое значения!"
			)
			await ctx.send(embed=emb)
			self.add_money.reset_cooldown(ctx)
			return

		emb = discord.Embed(
			description=f"**Вы успешно добавили срадства в профиль {member.name}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		await self.client.database.update(
			"users",
			where={"user_id": member.id, "guild_id": ctx.guild.id},
			money=(await self.client.database.sel_user(target=member)).money+num,
		)

		if "economy" in audit.keys():
			e = discord.Embed(
				description=f"Пользователю `{str(member)}` были добавлены деньги",
				colour=discord.Color.blurple(),
				timestamp=await self.client.utils.get_guild_time(ctx.guild),
			)
			e.add_field(
				name="Модератор",
				value=str(ctx.author),
				inline=False,
			)
			e.add_field(
				name="Количество",
				value=str(num),
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Изменения средств пользователя",
				icon_url=ctx.author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["economy"])
			if channel is not None:
				await channel.send(embed=e)

	@commands.command(
		aliases=["removemoney"],
		name="remove-money",
		description="Отнимает деньги указанного участника",
		usage="remove-money [@Участник] [Количество]",
		help="**Примеры использования:**\n1. {Prefix}remove-money @Участник 1000\n2. {Prefix}remove-money 660110922865704980 1000\n\n**Пример 1:** Отнимает 1000 денег с упомянутого участника\n**Пример 2:** Отнимает 1000 денег с участника с указанным id",
	)
	@commands.has_permissions(administrator=True)
	@commands.cooldown(1, 14400, commands.BucketType.member)
	async def remove_money(self, ctx, member: discord.Member, num: int):
		audit = (await self.client.database.sel_guild(guild=ctx.guild)).audit

		if member.bot:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете изменять профиль бота!"
			)
			await ctx.send(embed=emb)
			return

		if member == ctx.author:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе"
			)
			await ctx.send(embed=emb)
			return

		if num <= 0:
			emb = await self.client.utils.create_error_embed(ctx, "Укажите отнимаемое значения больше 0!")
			await ctx.send(embed=emb)
			return

		emb = discord.Embed(
			description=f"**Вы успешно отняли деньги из профиля {member.name}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		await self.client.database.update(
			"users",
			where={"user_id": member.id, "guild_id": ctx.guild.id},
			money=(await self.client.database.sel_user(target=member)).money-num,
		)

		if "economy" in audit:
			e = discord.Embed(
				description=f"У пользователя `{str(member)}` были отняты деньги",
				colour=discord.Color.green(),
				timestamp=await self.client.utils.get_guild_time(ctx.guild),
			)
			e.add_field(
				name="Модератор",
				value=str(ctx.author),
				inline=False,
			)
			e.add_field(
				name="Количество",
				value="-" + str(num),
				inline=False,
			)
			e.add_field(name="Id Участника", value=f"`{member.id}`", inline=False)
			e.set_author(
				name="Журнал аудита | Изменения средств пользователя",
				icon_url=ctx.author.avatar_url,
			)
			e.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			channel = ctx.guild.get_channel(audit["economy"])
			if channel is not None:
				await channel.send(embed=e)

	@commands.command(
		description="Этой командой можно ограбить пользователя",
		usage="rob [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}rob @Участник\n2. {Prefix}rob 660110922865704980\n\n**Пример 1:** Грабит упомянутому участника\n**Пример 2:** Грабит участника с указаным id",
	)
	@commands.cooldown(1, 86400, commands.BucketType.member)
	async def rob(self, ctx, member: discord.Member):
		data1 = await self.client.database.sel_user(target=ctx.author)

		if member.bot:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете красть деньги у бота!"
			)
			await ctx.send(embed=emb)
			return

		if data1.prison:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не забыли? Вы сейчас в тюрме!"
			)
			await ctx.send(embed=emb)
			self.rob.reset_cooldown(ctx)
			return

		data2 = await self.client.database.sel_user(target=member)
		rand_num = randint(1, 100)
		rob_shans = 80
		if "parrot" in data1.pets:
			rob_shans -= 10

		if rand_num <= 40:
			state = await rob_func(ctx, -10000, ctx.author)
			emb = discord.Embed(
				description=f"**Вас задержала полиция. Вы откупились потеряв 10000$**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(
				text=self.FOOTER, icon_url=self.client.user.avatar_url
			)
			await ctx.send(embed=emb)

			if state[0]:
				emb = discord.Embed(
					description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Текущий баланс - `{state[1]}`**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=ctx.bot.user.name,
					icon_url=ctx.bot.user.avatar_url,
				)
				emb.set_footer(
					text=self.FOOTER,
					icon_url=self.client.user.avatar_url,
				)
				await ctx.author.send(embed=emb)

		elif 40 < rand_num <= 80:
			emb = discord.Embed(
				description=f"**Вы не смогли ограбить указаного пользователя**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif rand_num > rob_shans:
			rand_num_1 = randint(1, 2)
			cr_money = data2.money // 4 * rand_num_1

			await rob_func(ctx, cr_money, ctx.author)
			await rob_func(ctx, int(cr_money * -1), member)

			emb = discord.Embed(
				description=f"**Вы смогли ограбить пользователя на суму {cr_money}**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

	@commands.command(
		description="Незаконная добыча денег",
		usage="crime",
		help="**Примеры использования:**\n1. {Prefix}crime\n\n**Пример 1:** Незаконно добывает деньги",
	)
	@commands.cooldown(1, 43200, commands.BucketType.member)
	async def crime(self, ctx):
		data = await self.client.database.sel_user(target=ctx.author)

		if data.prison:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не забыли? Вы сейчас в тюрме!"
			)
			await ctx.send(embed=emb)
			self.crime.reset_cooldown(ctx)
			return

		rand_num = randint(1, 100)
		crime_shans = 80
		if "parrot" in data.pets:
			crime_shans -= 10

		if rand_num <= 40:
			state = await crime_member(ctx, -5000, ctx.author)
			emb = discord.Embed(
				description=f"**Вас задержала полиция. Вы откупились потеряв 5000$**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			if state[0]:
				emb = discord.Embed(
					description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Текущий баланс - `{state[1]}`**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=ctx.bot.user.name,
					icon_url=ctx.bot.user.avatar_url,
				)
				emb.set_footer(
					text=self.FOOTER,
					icon_url=self.client.user.avatar_url,
				)
				await ctx.author.send(embed=emb)

		elif 40 < rand_num <= 80:
			emb = discord.Embed(
				description=f"**Вы не смогли совершить идею заработка денег**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif rand_num > crime_shans:
			rand_money = randint(20, 1000)
			await crime_member(ctx, rand_money, ctx.author)
			emb = discord.Embed(
				description=f"**Вы смогли заработать на незаконной работе - {rand_money}$**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

	@commands.command(
		description="Показывает ваш инвертарь",
		usage="inventory",
		aliases=["inv"],
		help="**Примеры использования:**\n1. {Prefix}inventory\n\n**Пример 1:** Показывает ваш инвертарь",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def inventory(self, ctx):
		parsed_inventory = await parse_inventory(ctx)
		emb = discord.Embed(
			title="Ваш инвертарь",
			description=f"{parsed_inventory[0]}{parsed_inventory[1]}{parsed_inventory[2]}{parsed_inventory[3]}",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		aliases=["profile-color", "profilecolor", "spc", "pcl"],
		name="set-profile-color",
		description="Ставит новый цвет для вашего профиля",
		usage="set-profile-color [Цвет]",
		help="**Примеры использования:**\n1. {Prefix}set-profile-color orange\n\n**Пример 1:** Ставит оранжевый цвет профиля",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def profile_color(self, ctx, color: str = None):
		colors = [
			"green",
			"lime",
			"orange",
			"purple",
			"pink",
			"red",
			"зелёный",
			"лаймовый",
			"оранжевый",
			"фиолетовый",
			"розовый",
			"красный",
			"default",
			"стандартный"
		]
		colour = {
			"green": "green",
			"lime": "lime",
			"orange": "orange",
			"purple": "purple",
			"pink": "pink",
			"red": "red",
			"зелёный": "green",
			"лаймовый": "lime",
			"оранжевый": "orange",
			"фиолетовый": "purple",
			"розовый": "pink",
			"красный": "red",
			"стандартный": "default",
			"default": "default"
		}

		if color is None:
			emb = discord.Embed(
				description=f"**Выберите цвет профиля среди этих: зелёный, лаймовый, оранжевый, фиолетовый, розовый, красный, стандартный.**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return
		elif color.lower() not in colors:
			emb = await self.client.utils.create_error_embed(
				ctx, "**Такого цвета нет! Выберите среди этих: зелёный, лаймовый, оранжевый, фиолетовый, розовый, красный, стандартный**"
			)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"users",
			where={"user_id": ctx.author.id, "guild_id": ctx.guild.id},
			profile=colour[color.lower()]
		)

		emb = discord.Embed(
			description=f"**Вы успешно поменяли цвет своего профиля на {color}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		aliases=["p"],
		description="Показывает профиль указанного пользователя",
		usage="profile |@Участник|",
		help="**Примеры использования:**\n1. {Prefix}profile @Участник\n2. {Prefix}profile 660110922865704980\n3. {Prefix}profile\n\n**Пример 1:** Показывает профиль упомянутого участника\n**Пример 2:** Показывает профиль участника с указаным id\n**Пример 3:** Показывает ваш профиль",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def profile(self, ctx, member: discord.Member = None):
		if member is None:
			member = ctx.author

		if member.bot:
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете просмотреть профиль бота!"
			)
			await ctx.send(embed=emb)
			return

		def draw_progress(image: Image, percent: int):
			if percent < 0:
				return image

			if percent > 100:
				percent = 100

			percent = 100 - percent
			progress_width = 525 * (percent / 100)
			progress_height = 55

			x0 = 230
			y0 = 285
			x1 = x0 + progress_width
			y1 = y0 + progress_height

			drawer = ImageDraw.Draw(image)
			drawer.rectangle(xy=[x0, y0, x1, y1], fill="#f3f598")
			drawer.ellipse(xy=[x0 + 40, y0 + 40, x0 + 40, y0 + 40], fill="#f3f598")

			return image

		def get_width_progress_bar(percent):
			if len(str(percent)) == 1:
				width = 800
			elif len(str(percent)) == 2:
				width = 785
			elif len(str(percent)) == 3:
				width = 770
			else:
				width = 750

			return width

		def get_width_info_exp(data):
			if len(str(data)) == 1:
				width = 720
			elif len(str(data)) == 2:
				width = 690
			elif len(str(data)) == 3:
				width = 650
			elif len(str(data)) == 4:
				width = 610
			else:
				width = 580

			return width

		colours = {
			"green": ("#b8f9ff", "#b8f9ff", "#606060", "#444444"),
			"lime": ("#787878", "#787878", "#606060", "#444444"),
			"orange": ("#595959", "#595959", "#606060", "#444444"),
			"purple": ("#a6de6f", "#595959", "#444444", "#444444"),
			"pink": ("#cadedb", "#cadedb", "#606060", "#444444"),
			"red": ("#f3f598", "#595959", "#606060", "#444444"),
			"default": ("#cccccc", "#cccccc", "#222222", "#242424"),
			None: ("#cccccc", "#cccccc", "#222222", "#242424"),
		}
		statuses = {
			"dnd": "dnd",
			"online": "online",
			"offline": "offline",
			"idle": "sleep",
		}
		async with ctx.typing():
			user_rank = "---"
			users_rank = list(User.objects.filter(guild_id=ctx.guild.id).exclude(exp__lte=0).order_by("-exp"))
			for user in users_rank:
				user_obj = ctx.guild.get_member(user.user_id)
				if user_obj is not None and not user_obj.bot and user.user_id == member.id:
					user_rank = users_rank.index(user) + 1
					break

			user_data = await self.client.database.sel_user(target=member)
			multi = (await self.client.database.sel_guild(guild=ctx.guild)).exp_multi
			user_warns = len(await self.client.database.get_warns(user_id=member.id, guild_id=ctx.guild.id))
			level_exp = math.floor(9 * (user_data.level ** 2) + 50 * user_data.level + 125 * (multi/100))
			previous_level_exp = math.floor(
				9 * ((user_data.level - 1) ** 2) + 50 * (user_data.level - 1) + 125 * (multi/100)
			)
			progress_bar_percent = round(
				((level_exp - user_data.exp) / (level_exp - previous_level_exp)) * 100
			)
			user_image_status = Image.open(
				self.IMAGES_PATH + statuses[member.status.name] + ".png"
			).convert("RGBA")
			user_state_prison = "На свободе" if user_data.prison else "Сейчас в тюрме"
			if user_data.profile is None:
				img = Image.open(self.IMAGES_PATH+"default.png")
			elif user_data.profile is not None:
				img = Image.open(self.IMAGES_PATH + f"{user_data.profile}.png")

			user_image_status.thumbnail((40, 40), Image.ANTIALIAS)
			response = (
				Image.open(io.BytesIO(await member.avatar_url.read()))
				.convert("RGBA")
				.resize((160, 160), Image.ANTIALIAS)
			)
			response = ImageOps.expand(response, border=10, fill="white")
			img.paste(response, (10, 10))
			img.paste(user_image_status, (160, 160), user_image_status)
			idraw = ImageDraw.Draw(img)
			bigtext = ImageFont.truetype(self.FONT, size=56)
			midletext = ImageFont.truetype(self.FONT, size=40)
			smalltext = ImageFont.truetype(self.FONT, size=32)

			idraw.text((230, 10), "Профиль {}".format(member), font=bigtext, fill=colours[user_data.profile][2])
			idraw.text(
				(230, 60), f"Репутация: {user_data.reputation}", font=bigtext, fill=colours[user_data.profile][2]
			)
			idraw.text(
				(10, 200), f"Опыт: {user_data.exp}", font=midletext, fill=colours[user_data.profile][0]
			)
			idraw.text(
				(10, 230),
				f"Уровень: {user_data.level}",
				font=midletext,
				fill=colours[user_data.profile][0],
			)
			idraw.text(
				(230, 113),
				f"Предупрежденний: {user_warns}",
				font=midletext,
				fill=colours[user_data.profile][0],
			)
			idraw.text(
				(230, 147),
				f"Тюрьма: {user_state_prison}",
				font=midletext,
				fill=colours[user_data.profile][0],
			)
			idraw.text(
				(230, 181),
				f"Монет: {user_data.coins}",
				font=midletext,
				fill=colours[user_data.profile][0],
			)
			idraw.text(
				(230, 215),
				f"Денег: {user_data.money}$",
				font=midletext,
				fill=colours[user_data.profile][0],
			)
			idraw.rectangle((230, 285, 855, 340), fill="#909090")
			draw_progress(img, progress_bar_percent)

			exp_string = f"{user_data.exp}/{level_exp} exp"
			idraw.text(
				(get_width_info_exp(level_exp), 250),
				f"{user_data.exp}/{level_exp} exp",
				font=midletext,
				fill=colours[user_data.profile][3],
			)
			fill_percent = 100 - progress_bar_percent
			idraw.text(
				(get_width_progress_bar(fill_percent if fill_percent > 0 else 0), 300),
				f"{fill_percent if fill_percent > 0 else 0}%",
				font=midletext,
				fill=colours[user_data.profile][3],
			)
			idraw.text((230, 258), f"#{user_rank}", font=smalltext, fill=colours[user_data.profile][3])
			idraw.text((15, 355), self.FOOTER, font=midletext)

			img.save(self.SAVE)
			await ctx.send(file=discord.File(fp=self.SAVE))


def setup(client):
	client.add_cog(Economy(client))
