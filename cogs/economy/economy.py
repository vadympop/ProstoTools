import datetime
import json
import random
import math
import io
import uuid
import time
import discord

from discord.ext import commands
from discord.utils import get
from PIL import Image, ImageFont, ImageDraw, ImageOps
from random import randint


class Economy(commands.Cog):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT
		self.BACKGROUND = self.client.config.DEF_PROFILE_BG
		self.FONT = self.client.config.FONT
		self.SAVE = self.client.config.SAVE_IMG

	@commands.command(
		description="**Показывает лидеров по разных валютах**",
		usage="top",
		help="**Примеры использования:**\n1. {Prefix}top\n\n**Пример 1:** Покажет таблицу лидеров сервера",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def top(self, ctx):
		sql = """SELECT user_id, exp, level, money, reputation FROM users WHERE guild_id = %s AND guild_id = %s ORDER BY exp DESC LIMIT 15"""
		val = (ctx.guild.id, ctx.guild.id)

		data = await self.client.database.execute(sql, val)

		emb = discord.Embed(title="Лидеры сервера", colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)

		num = 1
		for user in data:
			member = get(ctx.guild.members, id=user[0])
			if member is not None:
				if not member.bot:
					if num == 1:
						emb.add_field(
							name=f"**[{num}]** <:gold_star:732490991302606868> Участник - {member.name}, Опыта - {user[1]}",
							value=f"Уровень: **{user[2]}**\nРепутации: **{user[4]}**\nДенег: **{user[3]}**",
							inline=False,
						)
					elif num == 2:
						emb.add_field(
							name=f"**[{num}]** <:silver_star:732490991378104390> Участник - {member.name}, Опыта - {user[1]}",
							value=f"Уровень: **{user[2]}**\nРепутации: **{user[4]}**\nДенег: **{user[3]}**",
							inline=False,
						)
					elif num == 3:
						emb.add_field(
							name=f"**[{num}]** <:bronce_star:732490990924988418> Участник - {member.name}, Опыта - {user[1]}",
							value=f"Уровень: **{user[2]}**\nРепутации: **{user[4]}**\nДенег: **{user[3]}**",
							inline=False,
						)
					else:
						emb.add_field(
							name=f"[{num}] Участник - {member.name}, Опыта - {user[1]}",
							value=f"Уровень: **{user[2]}**\nРепутации: **{user[4]}**\nДенег: **{user[3]}**",
							inline=False,
						)
					num += 1

		await ctx.send(embed=emb)

	@commands.command(
		name="+rep",
		aliases=["+reputation", "repp"],
		description="**Добавления репутации(от 1 до 5) указаному пользователю(Cooldown 1 час)**",
		usage="+rep [@Участник] [Число репутации]",
		help="**Примеры использования:**\n1. {Prefix}+rep @Участник 1\n2. {Prefix}+rep 660110922865704980 1\n\n**Пример 1:** Даст упомянутому участнику одну репутацию\n**Пример 2:** Даст участнику с указаным id одну репутацию",
	)
	@commands.cooldown(1, 3600, commands.BucketType.member)
	async def repp(self, ctx, member: discord.Member, num: int):
		if member == ctx.author:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вы не можете изменять свою репутацию!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.repp.reset_cooldown(ctx)
			return
		elif num < 1 or num > 5:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вы указали число добавляемой репутацию в неправильном диапазоне!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.repp.reset_cooldown(ctx)
			return
		elif member.bot:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вы не можете менять репутацию бота**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.repp.reset_cooldown(ctx)
			return

		await self.client.database.sel_user(target=member)

		sql = """UPDATE users SET reputation = reputation + %s WHERE user_id = %s AND guild_id = %s"""
		val = (num, member.id, ctx.guild.id)

		await self.client.database.execute(sql, val)

		emb = discord.Embed(
			description="**Вы успешно добавили репутация к указаному пользователю!**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		name="-rep",
		aliases=["-reputation", "repm"],
		description="**Отнимает репутацию(от 1 до 3) указаному пользователю(Cooldown 1 час)**",
		usage="-rep [@Участник] [Число репутации]",
		help="**Примеры использования:**\n1. {Prefix}-rep @Участник 1\n2. {Prefix}-rep 660110922865704980 1\n\n**Пример 1:** Отнимет упомянутому участнику одну репутацию\n**Пример 2:** Отнимет участнику с указаным id одну репутацию",
	)
	@commands.cooldown(1, 3600, commands.BucketType.member)
	async def repm(self, ctx, member: discord.Member, num: int):
		if member == ctx.author:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вы не можете изменять свою репутацию!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.repm.reset_cooldown(ctx)
			return
		elif num < 1 or num > 3:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вы указали число убаляемой репутацию в неправильном диапазоне!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.repm.reset_cooldown(ctx)
			return
		elif member.bot:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вы не можете менять репутацию бота**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.repm.reset_cooldown(ctx)
			return

		await self.client.database.sel_user(target=member)

		sql = """UPDATE users SET reputation = reputation - %s WHERE user_id = %s AND guild_id = %s"""
		val = (num, member.id, ctx.guild.id)

		await self.client.database.execute(sql, val)

		emb = discord.Embed(
			description="**Вы успешно убавили репутация к указаному пользователю!**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Ежедневная награда**",
		usage="daily",
		help="**Примеры использования:**\n1. {Prefix}daily\n\n**Пример 1:** Выдаст вам рандомное количество денег от 50$ до 1000$",
	)
	@commands.cooldown(1, 86400, commands.BucketType.member)
	async def daily(self, ctx):
		nums = [100, 250, 1000, 500, 50]
		rand_num = random.choice(nums)

		await self.client.database.sel_user(target=ctx.author)
		sql = """UPDATE users SET money = money + %s WHERE user_id = %s AND guild_id = %s"""
		val = (rand_num, ctx.author.id, ctx.guild.id)

		await self.client.database.execute(sql, val)

		emb = discord.Embed(
			description=f"**Вы получили ежедневну награду! В размере - {rand_num}$**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		aliases=["textchannel"],
		name="text-channel",
		description="**Создает приватный текстовый канал. По умолчанию у вас есть 20 каналов(Их можно купить в магазине), создавать их можно только в определлёной категории. Он автоматически удаляеться через 30мин!(Cooldown - 3 мин)**",
		usage="text-channel [Имя канала]",
		help="**Примеры использования:**\n1. {Prefix}text-channel Name\n\n**Пример 1:** Создаёт временный текстовый канал с названиям `Name`",
	)
	@commands.cooldown(1, 240, commands.BucketType.member)
	async def textchannel(self, ctx, *, name: str):
		data = await self.client.database.sel_user(target=ctx.author)
		sql = """UPDATE users SET text_channel = text_channel - 1 WHERE user_id = %s AND guild_id = %s"""
		val = (ctx.author.id, ctx.guild.id)

		guild_data = await self.client.database.sel_guild(guild=ctx.guild)
		category_id = guild_data["textchannels_category"]
		time_channel = guild_data["timedelete_textchannel"]
		num_textchannels = data["text_channels"]

		if len(name) > 32:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Укажите названия канала меньше 32 символов!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.textchannel.reset_cooldown(ctx)
			return

		if category_id == 0:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Не указана категория создания приватных текстовых каналов. Обратитесь к администации сервера**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.textchannel.reset_cooldown(ctx)
			return
		elif category_id != 0:
			if num_textchannels >= 0:
				overwrites = {
					ctx.guild.default_role: discord.PermissionOverwrite(
						read_messages=False, send_messages=False
					),
					ctx.author: discord.PermissionOverwrite(
						read_messages=True,
						send_messages=True,
						manage_permissions=True,
						manage_channels=True,
					),
				}
				category = discord.utils.get(ctx.guild.categories, id=category_id)
				text_channel = await ctx.guild.create_text_channel(
					name, category=category, overwrites=overwrites
				)

				emb = discord.Embed(
					description=f"`{str(ctx.author)}` Создал текстовый канал `#{text_channel}`",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)

				await self.client.database.execute(sql, val)

				await self.client.database.set_punishment(
					type_punishment="text_channel",
					time=float(time.time() + 60 * time_channel),
					member=ctx.author,
					role_id=text_channel.id,
				)
			elif num_textchannels <= 0:
				emb = discord.Embed(
					title=f"**У вас не достаточно каналов!**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction("❌")
				self.textchannel.reset_cooldown(ctx)
				return

	@commands.command(
		aliases=["shoplist"],
		name="shop-list",
		description="**Показывает список покупаемых предметов**",
		usage="shop-list",
		help="**Примеры использования:**\n1. {Prefix}shop-list\n\n**Пример 1:** Показывает шоп-лист сервера",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def shoplist(self, ctx):
		data = await self.client.database.sel_guild(guild=ctx.guild)
		shoplist = data["shop_list"]
		content = ""

		if shoplist != []:
			for shop_role in shoplist:
				role = get(ctx.guild.roles, id=shop_role[0])
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
		elif shoplist == []:
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
		description="**Этой командой можно оправить свои деньги другому пользователю(Cooldown - 30 мин)**",
		usage="send-money [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}send-money @Участник 1000\n2. {Prefix}send-money 660110922865704980 1000\n\n**Пример 1:** Отправляет 1000$ упомянутому участнику\n**Пример 2:** Отправляет 1000$ участнику с указаным id",
	)
	@commands.cooldown(1, 1800, commands.BucketType.member)
	async def sendmoney(self, ctx, member: discord.Member, num: int):
		if member.bot:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не можете передавать деньги боту!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		if num <= 0:
			emb = await self.client.create_error_embed(ctx, "Укажите число пересылаемых денег больше 0!")
			await ctx.send(embed=emb)
			return

		data1 = await self.client.database.sel_user(target=ctx.author)
		data2 = await self.client.database.sel_user(target=member)

		cur_state_pr1 = data1["prison"]
		cur_state_pr2 = data2["prison"]
		cur_money1 = data1["money"]
		cur_transantions1 = data1["transantions"]
		cur_transantions2 = data2["transantions"]

		if not cur_state_pr1 and not cur_state_pr2 and cur_money1 > num:
			info_transantion_1 = {
				"to": member.id,
				"from": ctx.author.id,
				"cash": num,
				"time": str(datetime.datetime.today()),
				"id": str(uuid.uuid4),
				"guild_id": ctx.guild.id,
			}
			info_transantion_2 = {
				"to": member.id,
				"from": ctx.author.id,
				"cash": num,
				"time": str(datetime.datetime.today()),
				"id": str(uuid.uuid4),
				"guild_id": ctx.guild.id,
			}

			cur_transantions1.append(info_transantion_1)
			cur_transantions2.append(info_transantion_2)

			sql_1 = """UPDATE users SET money = money - %s, transantions = %s WHERE user_id = %s AND guild_id = %s"""
			sql_2 = """UPDATE users SET money = money + %s, transantions = %s WHERE user_id = %s AND guild_id = %s"""
			val_1 = (num, json.dumps(cur_transantions1), ctx.author.id, ctx.guild.id)
			val_2 = (num, json.dumps(cur_transantions2), member.id, member.guild.id)

			await self.client.database.execute(sql_1, val_1)
			await self.client.database.execute(sql_2, val_2)

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
		elif cur_state_pr1:
			emb = discord.Embed(
				title="Ошибка!",
				description="**У вас заблокирование транзакции, так как вы в тюрме!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.sendmoney.reset_cooldown(ctx)
			return
		elif cur_state_pr2:
			emb = discord.Embed(
				title="Ошибка!",
				description="**В указаного пользователя заблокирование транзакции, так как он в тюрме!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.sendmoney.reset_cooldown(ctx)
			return
		elif cur_money1 < num:
			emb = discord.Embed(
				title="Ошибка!",
				description="**У вас недостаточно средств для транзакции!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.sendmoney.reset_cooldown(ctx)
			return

	@commands.command(
		aliases=["trans", "transactions"],
		name="my-transactions",
		description="**Показывает всё ваши транзакции на текущем сервере**",
		usage="my-transactions",
		help="**Примеры использования:**\n1. {Prefix}my-transactions\n\n**Пример 1:** Показывает список ваших транзакций",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def trans(self, ctx):
		data = await self.client.database.sel_user(target=ctx.author)
		transantions = data["transantions"]

		if transantions == []:
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

		for transantion in transantions:
			transantion_id = transantion["id"]
			transantion_time = transantion["time"]
			transantion_to = get(ctx.guild.members, id=transantion["to"])
			if not transantion_to:
				transantion_to = transantion["to"]
			transantion_from = get(ctx.guild.members, id=transantion["from"])
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
		description="**Открывает указаный лут бокс**",
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
		items = data["items"]
		pets = data["pets"]
		money = data["money"]
		coins = data["coins"]

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

		for item in items:
			if isinstance(item, list):
				if item[0] == box:
					state = True
					if item[1] <= 1:
						items.remove(item)
					elif item[1] > 1:
						item[1] -= 1

		if state:
			if box == boxes[0]:
				if rand_num_1 <= 5:
					pet = [all_pets[2], boxes[0]]
					msg_content = "С обычного бокса вам выпал питомец - Каска(Увеличивает стоимость клада)"
					# Каска

				elif rand_num_1 > 5 and rand_num_1 <= 25:
					pet = [all_pets[1], boxes[0]]
					msg_content = (
						"С обычного бокса вам выпал питомец - Собачка(Обычный питомец)"
					)
					# Собачка

				elif rand_num_1 > 25 and rand_num_1 <= 50:
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

				elif rand_num_1 > 1 and rand_num_1 <= 7:
					pet = [all_pets[2], boxes[1]]
					msg_content = "С редкого бокса вам выпал питомец - Каска(Увеличивает стоимость клада)"
					# Каска

				elif rand_num_1 > 7 and rand_num_1 <= 30:
					pet = [all_pets[1], boxes[1]]
					msg_content = (
						"С редкого бокса вам выпал питомец - Собачка(Обычный питомец)"
					)
					# Собачка

				elif rand_num_1 > 30 and rand_num_1 <= 60:
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

				elif rand_num_1 > 4 and rand_num_1 <= 10:
					pet = [all_pets[2], boxes[2]]
					msg_content = "С эпического бокса вам выпал питомец - Каска(Увеличивает стоимость клада)"
					# Каска

				elif rand_num_1 > 10 and rand_num_1 <= 33:
					pet = [all_pets[1], boxes[2]]
					msg_content = "С эпического бокса вам выпал питомец - Собачка(Обычный питомец)"
					# Собачка

				elif rand_num_1 > 33 and rand_num_1 <= 63:
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
						if choice in items:
							rand_money_2 = randint(1000, 2000)
							msg_content = f"Вам не очень повезло и с эпического бокса выпали деньги в размере - {rand_money_2}"
						else:
							items.append(choice)
							msg_content = f"С эпического бокса выпал предмет - {dict_items[choice]}"

					elif rand_num_2 == 4:
						choice = random.choice(rand_items_2)
						if choice in items:
							rand_money_2 = randint(1000, 2000)
							msg_content = f"Вам не очень повезло и с эпического бокса выпали деньги в размере - {rand_money_2}"
						else:
							items.append(choice)
							msg_content = f"С эпического бокса выпал предмет - {dict_items[choice]}"

			elif box == boxes[3]:
				if rand_num_1 <= 10:
					pet = [all_pets[5], boxes[3]]
					msg_content = "С легендарного бокса вам выпал питомец - Хомяк(Увеличивает выпадения коинов)"
					# Хомяк

				elif rand_num_1 > 10 and rand_num_1 <= 30:
					pet = [all_pets[2], boxes[3]]
					msg_content = "С легендарного бокса вам выпал питомец - Каска(Увеличивает стоимость клада)"
					# Каска

				elif rand_num_1 > 30 and rand_num_1 <= 33:
					pet = [all_pets[3], boxes[3]]
					msg_content = "С легендарного бокса вам выпал питомец - Лупа(Увеличивает шанс найти клад)"
					# Лупа

				elif rand_num_1 > 33 and rand_num_1 <= 63:
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
						if choice in items:
							rand_money_2 = randint(6000, 8000)
							msg_content = f"Вам не очень повезло и с легендарного бокса выпали деньги в размере - {rand_money_2}"
						else:
							items.append(choice)
							msg_content = f"С легендарного бокса выпал предмет - {dict_items[choice]}"

					elif rand_num_2 == 4:
						choice = random.choice(rand_items_2)
						if choice in items:
							rand_money_2 = randint(6000, 8000)
							msg_content = f"Вам не очень повезло и с легендарного бокса выпали деньги в размере - {rand_money_2}"
						else:
							items.append(choice)
							msg_content = f"С легендарного бокса выпал предмет - {dict_items[choice]}"

			elif box == boxes[4]:
				if rand_num_1 <= 25:
					pet = [all_pets[5], boxes[4]]
					msg_content = "С невероятного бокса вам выпал питомец - Хомяк(Увеличивает выпадения коинов)"
					# Хомяк

				elif rand_num_1 > 25 and rand_num_1 <= 50:
					pet = [all_pets[2], boxes[4]]
					msg_content = "С невероятного бокса вам выпал питомец - Каска(Увеличивает стоимость клада)"
					# Каска

				elif rand_num_1 > 50 and rand_num_1 <= 65:
					pet = [all_pets[3], boxes[4]]
					msg_content = "С невероятного бокса вам выпал питомец - Лупа(Увеличивает шанс найти клад)"
					# Лупа

				elif rand_num_1 > 65 and rand_num_1 <= 70:
					pet = [all_pets[4], boxes[4]]
					msg_content = "С невероятного бокса вам выпал питомец - Попугай(Уменьшает шанс быть пойманым)"
					# Попугай

				elif rand_num_1 > 70:
					rand_num_2 = randint(1, 5)

					if rand_num_2 == 1:
						rand_num_3 = randint(1, 3)

						if rand_num_3 >= 1 and rand_num_3 <= 2:
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
						if choice in items:
							rand_money_2 = randint(18000, 20000)
							msg_content = f"Вам не очень повезло и с невероятного бокса выпали деньги в размере - {rand_money_2}"
						else:
							items.append(choice)
							msg_content = f"С невероятного бокса выпал предмет - {dict_items[choice]}"

					elif rand_num_2 == 4:
						choice = random.choice(rand_items_2)
						if choice in items:
							rand_money_2 = randint(18000, 20000)
							msg_content = f"Вам не очень повезло и с невероятного бокса выпали деньги в размере - {rand_money_2}"
						else:
							items.append(choice)
							msg_content = f"С невероятного бокса выпал предмет - {dict_items[choice]}"

			money += rand_money
			if pet is not None:
				if pet[0] in pets:
					coins += dict_boxes[pet[1]][1]
					msg_content = f"К сожалению выйграный питомец уже есть в вашем инвертаре, по этому вам выпали коины в размере - {dict_boxes[pet[1]][1]}"
				else:
					pets.append(pet[0])

			emb = discord.Embed(
				title=f"Бокс - {dict_boxes[box][0]}",
				description=f"**{msg_content}**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			sql = """UPDATE users SET items = %s, pets = %s, money = %s WHERE user_id = %s AND guild_id = %s"""
			val = (
				json.dumps(items),
				json.dumps(pets),
				money,
				ctx.author.id,
				ctx.guild.id,
			)

			await self.client.database.execute(sql, val)
		elif not state:
			emb = discord.Embed(
				title=f"Ошибка!",
				description=f"**В вашем инвертаре нет такого лут-бокса!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")

	@commands.command(
		aliases=["removerole"],
		hidden=True,
		name="remove-role",
		description="**Удаляет указаную роль из профиля пользователя(Объязательно используйте эту команду для снятия роли, а не простое удаление роли через сам дискорд!, Cooldown - 3 часа)",
		usage="remove-role [@Участник] [@Роль]",
		help="**Примеры использования:**\n1. {Prefix}remove-role @Участник @Роль\n2. {Prefix}remove-role 660110922865704980 717776604461531146\n\n**Пример 1:** Удаляет упомянутую роль в упомянутого участника\n**Пример 2:** Удаляет роль с указаным id в участника с указаным id",
	)
	@commands.cooldown(1, 14400, commands.BucketType.member)
	@commands.has_permissions(administrator=True)
	async def remove_role(self, ctx, member: discord.Member, role: discord.Role):
		audit = await self.client.database.sel_guild(guild=ctx.guild)["audit"]

		if member.bot:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не можете снимать роль боту!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		if member in ctx.guild.members:
			data = await self.client.database.sel_user(target=member)
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**На сервере не существует такого пользователя!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.remove_role.reset_cooldown(ctx)
			return

		items = data["items"]
		if role.id in items:
			items.remove(role.id)

			try:
				await member.remove_roles(role)
			except:
				pass

			sql = """UPDATE users SET items = %s WHERE user_id = %s AND guild_id = %s"""
			val = (json.dumps(items), member.id, ctx.guild.id)

			await self.client.database.execute(sql, val)

			emb = discord.Embed(
				title="Успех!",
				description=f"**Снятия роли прошло успешно, роль - {role.mention} была удаленна из эго профиля!**",
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
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow(),
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
		aliases=["addcash"],
		hidden=True,
		name="add-cash",
		description="**Добавляет указаний тип валюты в профиль**",
		usage="add-cash [@Участник] [Название валюты] [Количество]",
		help="**Примеры использования:**\n1. {Prefix}add-cash @Участник coins 1000\n2. {Prefix}add-cash 660110922865704980 coins 1000\n\n**Пример 1:** Добавляет 1000 коинов упомянутому участнику\n**Пример 2:** Добавляет 1000 коинов участнику с указаным id",
	)
	@commands.has_permissions(administrator=True)
	@commands.cooldown(1, 14400, commands.BucketType.member)
	async def add_cash(self, ctx, member: discord.Member, typem: str, num: int):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if member.bot:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не можете добавлять деньги боту!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		if num <= 0:
			emb = await self.client.create_error_embed(ctx, "Укажите число добавляемых денег больше 0!")
			await ctx.send(embed=emb)
			return

		if num >= 1000000000:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Указано слишком большое значения!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.add_cash.reset_cooldown(ctx)
			return

		data = await self.client.database.sel_user(target=member)
		coins_member = data["coins"]
		cur_money = data["money"]

		if typem == "money":
			cur_money += num
		elif typem == "coins":
			coins_member += num
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Укажите правильную единицу!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.add_cash.reset_cooldown(ctx)
			return

		emb = discord.Embed(
			description=f"**Вы успешно добавили значений в профиль {member.name}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		sql = """UPDATE users SET money = %s, coins = %s WHERE user_id = %s AND guild_id = %s"""
		val = (cur_money, coins_member, member.id, ctx.guild.id)

		await self.client.database.execute(sql, val)

		if "economy" in audit.keys():
			e = discord.Embed(
				description=f"Пользователю `{str(member)}` были добавлены средства",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name="Модератором",
				value=str(ctx.author),
				inline=False,
			)
			e.add_field(
				name="Тип средств",
				value=typem,
				inline=False,
			)
			e.add_field(
				name="Количество",
				value=num,
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
		aliases=["removecash"],
		hidden=True,
		name="remove-cash",
		description="**Удаляет указаний тип валюты из профиля**",
		usage="remove-cash [@Участник] [Название валюты] [Количество]",
		help="**Примеры использования:**\n1. {Prefix}remove-cash @Участник coins 1000\n2. {Prefix}remove-cash 660110922865704980 coins 1000\n\n**Пример 1:** Отнимает 1000 коинов упомянутому участнику\n**Пример 2:** Отнимает 1000 коинов участнику с указаным id",
	)
	@commands.has_permissions(administrator=True)
	@commands.cooldown(1, 14400, commands.BucketType.member)
	async def remove_cash(self, ctx, member: discord.Member, typem: str, num: int):
		audit = (await self.client.database.sel_guild(guild=ctx.guild))["audit"]

		if member.bot:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не можете снимать деньги боту!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		if num <= 0:
			emb = await self.client.create_error_embed(ctx, "Укажите число отнимаемых денег больше 0!")
			await ctx.send(embed=emb)
			return

		data = await self.client.database.sel_user(target=member)
		coins_member = data["coins"]
		cur_money = data["money"]

		if typem == "money":
			cur_money -= num
		elif typem == "coins":
			coins_member -= num
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Укажите правильную единицу!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.remove_cash.reset_cooldown(ctx)
			return

		emb = discord.Embed(
			description=f"**Вы успешно отняли значений из профиля {member.name}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		sql = """UPDATE users SET money = %s, coins = %s WHERE user_id = %s AND guild_id = %s"""
		val = (cur_money, coins_member, member.id, ctx.guild.id)

		await self.client.database.execute(sql, val)

		if "economy" in audit:
			e = discord.Embed(
				description=f"Пользователю `{str(member)}` были отняты средства",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow(),
			)
			e.add_field(
				name="Модератором",
				value=str(ctx.author),
				inline=False,
			)
			e.add_field(
				name="Тип средств",
				value=typem,
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
		description="**Этой командой можно ограбить пользователя(Cooldown 24 часа)**",
		usage="rob [@Участник]",
		help="**Примеры использования:**\n1. {Prefix}rob @Участник\n2. {Prefix}rob 660110922865704980\n\n**Пример 1:** Грабит упомянутому участника\n**Пример 2:** Грабит участника с указаным id",
	)
	@commands.cooldown(1, 86400, commands.BucketType.member)
	async def rob(self, ctx, member: discord.Member):
		data1 = await self.client.database.sel_user(target=ctx.author)
		cur_state_pr = data1["prison"]

		if member.bot:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не можете красть деньги у бота!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		if not cur_state_pr:
			data2 = await self.client.database.sel_user(target=member)
			rand_num = randint(1, 100)
			cur_pets = data1["pets"]
			crimed_member_money = data2["money"]
			rob_shans = 80
			if "parrot" in cur_pets:
				rob_shans -= 10

			async def rob_func(num, member):
				data = await self.client.database.sel_user(target=member)
				cur_money = data["money"] + num
				prison = data["prison"]
				items = data["items"]
				state = False

				if member == ctx.author:
					if cur_money <= -5000:
						items = []
						prison = True
						state = True

				sql = """UPDATE users SET money = %s, items = %s, prison = %s WHERE user_id = %s AND guild_id = %s"""
				val = (
					cur_money,
					json.dumps(items),
					str(prison),
					member.id,
					member.guild.id,
				)

				await self.client.database.execute(sql, val)
				return [state, data["money"]]

			if rand_num <= 40:
				state = await rob_func(-10000, ctx.author)
				if state[0] == True:
					emb = discord.Embed(
						description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Ваш текущий баланс: {state[1]}**",
						colour=discord.Color.green(),
					)
					emb.set_author(
						name=self.client.user.name, icon_url=self.client.user.avatar_url
					)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.author.send(embed=emb)
					return
				else:
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
			elif rand_num > 40 and rand_num <= 80:
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
				cr_money = crimed_member_money // 4 * rand_num_1

				await rob_func(cr_money, ctx.author)
				await rob_func(int(cr_money * -1), member)

				emb = discord.Embed(
					description=f"**Вы смогли ограбить пользователя на суму {cr_money}**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
		elif cur_state_pr == True:
			emb = discord.Embed(
				description=f"**Вы не забыли? Вы сейчас в тюрме!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.rob.reset_cooldown(ctx)
			return

	@commands.command(
		description="**Незаконная добыча денег(Cooldown - 12 часов)**",
		usage="crime",
		help="**Примеры использования:**\n1. {Prefix}crime\n\n**Пример 1:** Незаконно добывает деньги",
	)
	@commands.cooldown(1, 43200, commands.BucketType.member)
	async def crime(self, ctx):
		data = await self.client.database.sel_user(target=ctx.author)
		cur_state_pr = data["prison"]

		if cur_state_pr == False:
			rand_num = randint(1, 100)
			cur_pets = data["pets"]
			crime_shans = 80
			if "parrot" in cur_pets:
				crime_shans -= 10

			async def crime_func(num, member):
				data = await self.client.database.sel_user(target=member)
				cur_money = data["money"] + num
				prison = data["prison"]
				items = data["items"]

				sql = """UPDATE users SET money = %s, prison = %s, items = %s WHERE user_id = %s AND guild_id = %s"""
				val = (
					cur_money,
					str(prison),
					json.dumps(items),
					member.id,
					member.guild.id,
				)

				await self.client.database.execute(sql, val)
				if cur_money <= -5000:
					prison = True
					items = []
					return [True, data["money"]]

			if rand_num <= 40:
				state = await crime_func(-5000, ctx.author)
				if state[0]:
					emb = discord.Embed(
						description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Ваш текущий баланс: {state[1]}**",
						colour=discord.Color.green(),
					)
					emb.set_author(
						name=self.client.user.name, icon_url=self.client.user.avatar_url
					)
					emb.set_footer(
						text=self.FOOTER, icon_url=self.client.user.avatar_url
					)
					await ctx.author.send(embed=emb)
					return
				else:
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
			elif rand_num > 40 and rand_num <= 80:
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
				await crime_func(rand_money, ctx.author)
				emb = discord.Embed(
					description=f"**Вы смогли заработать на незаконной работе - {rand_money}$**",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
		elif cur_state_pr:
			emb = discord.Embed(
				description=f"**Вы не забыли? Вы сейчас в тюрме!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			self.crime.reset_cooldown(ctx)
			return

	@commands.command(
		description="**Показывает ваш инвертарь**",
		usage="invertory",
		aliases=["inv"],
		help="**Примеры использования:**\n1. {Prefix}invertory\n\n**Пример 1:** Показывает ваш инвертарь",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def invertory(self, ctx):
		data = await self.client.database.sel_user(target=ctx.author)
		Prefix = self.client.database.get_prefix(guild=ctx.guild)
		number = data["text_channels"]

		def func_inv():
			items = data["items"]
			pets = data["pets"]
			roles_content = " "
			items_content = " "
			box_content = " "
			pets_content = " "
			check_state = True
			names_of_items = {
				"sim": "Сим-карта",
				"tel": "Телефон",
				"metal_1": "Металоискатель 1-го уровня",
				"metal_2": "Металоискатель 2-го уровня",
				"mop": "Швабра",
				"broom": "Метла",
				"gloves": "Перчатки",
			}
			boxes = {
				"box-I": "Невероятный бокс",
				"box-L": "Легендарный бокс",
				"box-E": "Эпический бокс",
				"box-R": "Редкий бокс",
				"box-C": "Обычный бокс",
			}
			dict_pets = {
				"cat": "Кошка",
				"dog": "Собачка",
				"helmet": "Каска",
				"loupe": "Лупа",
				"parrot": "Попугай",
				"hamster": "Хомяк",
			}

			if items == []:
				items_content = f"Ваш инвертарь пуст. Купите что-нибудь с помощью команды - {Prefix}buy\n"
				check_state = False
			elif items != []:
				for i in items:
					if isinstance(i, list):
						box_content = box_content + f"{boxes[i[0]]} - {i[1]}шт \n"
					else:
						if isinstance(i, str):
							items_content = items_content + f"{names_of_items[i]}\n "
						elif isinstance(i, int):
							role = get(ctx.guild.roles, id=i)
							roles_content = roles_content + f"{role.mention}\n "

				for pet in pets:
					pets_content += f"{dict_pets[pet]}\n "

			if check_state:
				if items_content != " ":
					items_content = f"**Ваши предметы:**\n{items_content}\n"

			if roles_content != " ":
				roles_content = f"**Ваши роли:**\n{roles_content}\n"

			if box_content != " ":
				box_content = f"**Ваши лут-боксы:**\n{box_content}\n"

			if pets_content != " ":
				pets_content = f"**Ваши питомцы:**\n{pets_content}\n"

			return [items_content, roles_content, box_content, pets_content]

		emb = discord.Embed(
			title="Ваш инвертарь",
			description=f"{func_inv()[0]}{func_inv()[1]}{func_inv()[2]}{func_inv()[3]}**Текстовые каналы:** {number}",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		aliases=["profile-color", "profilecolor"],
		name="set-profile-color",
		description="**Ставит новый цвет для вашего профиля**",
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
		}

		if color is None:
			emb = discord.Embed(
				description=f"**Выберите цвет профиля среди этих: зелёный, лаймовый, оранжевый, фиолетовый, розовый, красный. Стандартный цвет - лаймовый.**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return
		elif color.lower() not in colors:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Такого цвета нет! Выберите среди этих: зелёный, лаймовый, оранжевый, фиолетовый, розовый, красный. Стандартный цвет - лаймовый.**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return

		await self.client.database.sel_user(target=ctx.author)
		sql = """UPDATE users SET profile = %s WHERE user_id = %s AND guild_id = %s"""
		val = (colour[color.lower()], ctx.author.id, ctx.guild.id)

		await self.client.database.execute(sql, val)

		emb = discord.Embed(
			description=f"**Вы успешно поменяли цвет своего профиля на {color}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Показывает профиль указаного пользователя, без упоминания ваш профиль**",
		usage="profile |@Участник|",
		help="**Примеры использования:**\n1. {Prefix}profile @Участник\n2. {Prefix}profile 660110922865704980\n3. {Prefix}profile\n\n**Пример 1:** Показывает профиль упомянутого участника\n**Пример 2:** Показывает профиль участника с указаным id\n**Пример 3:** Показывает ваш профиль",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def profile(self, ctx, member: discord.Member = None):
		if member is None:
			member = ctx.author

		if member.bot:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Вы не можете просмотреть профиль бота!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
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
			"green": ["#b8f9ff", "#b8f9ff"],
			"lime": ["#787878", "#787878"],
			"orange": ["#595959", "#595959"],
			"purple": ["#a6de6f", "#595959"],
			"pink": ["#cadedb", "#cadedb"],
			"red": ["#f3f598", "#595959"],
			None: ["#787878", "#787878"],
		}
		statuses = {
			"dnd": "dnd",
			"online": "online",
			"offline": "offline",
			"idle": "sleep",
		}
		async with ctx.typing():
			users_rank = await self.client.database.execute(
				query="""SELECT user_id FROM users WHERE guild_id = %s AND guild_id = %s ORDER BY exp DESC""",
				val=(ctx.guild.id, ctx.guild.id),
			)
			for user in users_rank:
				if user[0] == member.id:
					user_rank = users_rank.index(user) + 1
					break

			user_data = await self.client.database.sel_user(target=member)
			multi = (await self.client.database.sel_guild(guild=ctx.guild))["exp_multi"]
			user = str(member.name)
			user_exp = int(user_data["exp"])
			user_level = int(user_data["lvl"])
			user_warns = len(user_data["warns"])
			user_coins = int(user_data["coins"])
			user_money = int(user_data["money"])
			user_reputation = int(user_data["reputation"])
			user_state_prison = user_data["prison"]
			user_profile = user_data["profile"]
			level_exp = math.floor(9 * (user_level ** 2) + 50 * user_level + 125 * multi)
			previus_level_exp = math.floor(
				9 * ((user_level - 1) ** 2) + 50 * (user_level - 1) + 125 * multi
			)
			progress_bar_percent = round(
				((level_exp - user_exp) / (level_exp - previus_level_exp)) * 100
			)
			user_image_status = Image.open(
				self.BACKGROUND[:-8] + statuses[member.status.name] + ".png"
			).convert("RGBA")

			if user_state_prison:
				user_state_prison = "Сейчас в тюрме"
			elif not user_state_prison:
				user_state_prison = "На свободе"

			if user_profile is None:
				img = Image.open(self.BACKGROUND)
			elif user_profile is not None:
				img = Image.open(self.BACKGROUND[:-8] + f"{user_profile}.png")

			user_image_status.thumbnail((40, 40), Image.ANTIALIAS)
			responce = (
				Image.open(io.BytesIO(await member.avatar_url.read()))
				.convert("RGBA")
				.resize((160, 160), Image.ANTIALIAS)
			)
			responce = ImageOps.expand(responce, border=10, fill="white")
			img.paste(responce, (10, 10))
			img.paste(user_image_status, (160, 160), user_image_status)
			idraw = ImageDraw.Draw(img)
			bigtext = ImageFont.truetype(self.FONT, size=56)
			midletext = ImageFont.truetype(self.FONT, size=40)
			smalltext = ImageFont.truetype(self.FONT, size=32)

			idraw.text((230, 10), "Профиль {}".format(user), font=bigtext, fill="#606060")
			idraw.text(
				(230, 60), f"Репутация: {user_reputation}", font=bigtext, fill="#606060"
			)
			idraw.text(
				(10, 200), f"Exp: {user_exp}", font=midletext, fill=colours[user_profile][0]
			)
			idraw.text(
				(10, 230),
				f"Уровень: {user_level}",
				font=midletext,
				fill=colours[user_profile][0],
			)
			idraw.text(
				(230, 113),
				f"Предупрежденний: {user_warns}",
				font=midletext,
				fill=colours[user_profile][0],
			)
			idraw.text(
				(230, 147),
				f"Тюрьма: {user_state_prison}",
				font=midletext,
				fill=colours[user_profile][0],
			)
			idraw.text(
				(230, 181),
				f"Монет: {user_coins}",
				font=midletext,
				fill=colours[user_profile][0],
			)
			idraw.text(
				(230, 215),
				f"Денег: {user_money}$",
				font=midletext,
				fill=colours[user_profile][0],
			)
			idraw.rectangle((230, 285, 855, 340), fill="#909090")
			draw_progress(img, progress_bar_percent)
			idraw.text(
				(get_width_info_exp(round(level_exp - previus_level_exp)), 250),
				f"{round(level_exp - previus_level_exp)}/{round(level_exp - user_exp)} exp",
				font=midletext,
				fill="#444",
			)
			fill_percent = 100 - progress_bar_percent
			idraw.text(
				(get_width_progress_bar(fill_percent if fill_percent > 0 else 0), 300),
				f"{fill_percent if fill_percent > 0 else 0}%",
				font=midletext,
				fill="#444",
			)
			idraw.text((230, 258), f"#{user_rank}", font=smalltext, fill="#444")
			idraw.text((15, 355), self.FOOTER, font=midletext)

			img.save(self.SAVE)
			await ctx.send(file=discord.File(fp=self.SAVE))


def setup(client):
	client.add_cog(Economy(client))
