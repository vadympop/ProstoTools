import discord
import json
import random
import qrcode
import wikipedia
import requests
import cv2
import asyncio

from pyzbar import pyzbar
from discord.ext import commands
from random import randint
from bs4 import BeautifulSoup as bs


class Games(commands.Cog, name="Games"):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT

	@commands.command(
		aliases=["cr-qr", "cr_qr", "create-qr", "create_qrcode"],
		name="create-qrcode",
		description="**Закодирует указаный текст в qr-код**",
		usage="create-qrcode [Ваш текст]",
		help="**Примеры использования:**\n1. {Prefix}create-qrcode My text\n\n**Пример 1:** Создаёт QR-код с указаным текстом",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def cr_qr(self, ctx, *, code_text: str):
		purge = await self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if len(code_text) > 6000:
			emb = discord.Embed(
				title="Ошибка!",
				description="**Используйте текст меньше 6000 символов!**",
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return

		img = qrcode.make(code_text)
		img.save("./Data/Img/myqr.jpg")
		code_text = f"*{code_text}*"

		emb = discord.Embed(
			title="Функция создания qr-кодов",
			description=f"**Кодируемый текст:\n{code_text}**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(
			embed=emb,
			content="**Ваш qr-код**",
			file=discord.File("./Data/Img/myqr.jpg"),
		)

	@commands.command(
		aliases=["dcode_qr", "d_qr", "d-qr"],
		name="dcode-qrcode",
		description="**Разкодирует qr-код**",
		usage="dcode-qrcode [Ссылка на изображения]",
		help="**Примеры использования:**\n1. {Prefix}dcode-qrcode https://media.discordapp.net/attachments/717776571406090313/775762508211945482/myqr.jpg\n\n**Пример 1:** Раскодирует QR-код в указаном изображении",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def scan_url(self, ctx, url: str):
		purge = await self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		ddd = requests.get(url)
		img_file = open("./Data/Img/qr_url.png", "wb")
		img_file.write(ddd.content)
		img_file.close()

		img = cv2.imread("./Data/Img/qr_url.png")
		bs = pyzbar.decode(img)
		for barcode in bs:
			bd = barcode.data.decode("utf-8")
			emb = discord.Embed(
				title=f"Результат разкодировки",
				description=bd,
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

	@commands.command(
		description="**Википедия, расказывает о вашем запросе**",
		usage="wiki [Ваш запрос]",
		help="**Примеры использования:**\n1. {Prefix}wiki Bot\n\n**Пример 1:** Покажет информацию по запросе `Bot` на википедии",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def wiki(self, ctx, *, text: str):
		purge = await self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		try:
			wikipedia.set_lang("ru")
			new_page = wikipedia.page(text)
			summ = wikipedia.summary(text)

			emb = discord.Embed(
				title=new_page.title, description=summ, color=discord.Color.green()
			)
			emb.set_author(
				name="Больше информации тут! Кликай!",
				url=new_page.url,
				icon_url=ctx.author.avatar_url,
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		except:
			emb = discord.Embed(
				description="**О вашем запросе ничего не нашлось**",
				color=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

	@commands.command(
		name="8ball",
		description="**Магический шар предсказаний**",
		usage="8ball [Ваш вопрос]",
		help="**Примеры использования:**\n1. {Prefix}8ball My owner is nice programmer?\n\n**Пример 1:** Ответит на ваш вопрос магическим образом =)",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def magic_ball(self, ctx, *, msg: str):
		purge = await self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		rand_num = randint(1, 3)

		phrases_1 = [
			"Я думай - ДА",
			"Конечно да",
			"Я в этом уверен!",
			"100% - Да",
			"Буду рад",
		]
		phrases_2 = [
			"Точно - НЕТ!",
			"Тебе не подходит",
			"Хм... Нет",
			"Я уверен что нет",
		]
		phrases_3 = [
			"Спроси позже",
			"Я не уверен в этом",
			"Я занят!",
			"Спроси ещё разок",
			"Не знаю...",
		]

		if rand_num == 1:
			choice = random.choice(phrases_1)
		elif rand_num == 2:
			choice = random.choice(phrases_2)
		elif rand_num == 3:
			choice = random.choice(phrases_3)

		emb = discord.Embed(
			title="Мой ответ на ваш вопрос",
			description=f"**{choice}**",
			color=discord.Color.green(),
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Рандомная картинка собаки**",
		usage="dog",
		help="**Примеры использования:**\n1. {Prefix}dog\n\n**Пример 1:** Покажет рандомную картинку собаки",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def dog(self, ctx):
		emb = discord.Embed(color=discord.Color.green())
		emb.set_image(url=(await self.client.random_api.get_dog()))
		emb.set_author(name="Собачка", icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Рандомная картинка кошки**",
		usage="cat",
		help="**Примеры использования:**\n1. {Prefix}cat\n\n**Пример 1:** Покажет рандомную картинку кошки",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def cat(self, ctx):
		emb = discord.Embed(color=discord.Color.green())
		emb.set_image(url=(await self.client.random_api.get_cat()))
		emb.set_author(name="Кошечка :3", icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Рандомная картинка лисы**",
		usage="fox",
		help="**Примеры использования:**\n1. {Prefix}fox\n\n**Пример 1:** Покажет рандомную картинку лисы",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def fox(self, ctx):
		emb = discord.Embed(color=discord.Color.green())
		emb.set_image(url=(await self.client.random_api.get_fox()))
		emb.set_author(name="Лиса", icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Рандомная картинка птички**",
		usage="bird",
		help="**Примеры использования:**\n1. {Prefix}dog\n\n**Пример 1:** Покажет рандомную картинку птички",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def bird(self, ctx):
		emb = discord.Embed(color=discord.Color.green())
		emb.set_image(url=(await self.client.random_api.get_bird()))
		emb.set_author(name="Птичка", icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Рандомная картинка коалы**",
		usage="koala",
		help="**Примеры использования:**\n1. {Prefix}koala\n\n**Пример 1:** Покажет рандомную картинку коалы",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def koala(self, ctx):
		emb = discord.Embed(color=discord.Color.green())
		emb.set_image(url=(await self.client.random_api.get_koala()))
		emb.set_author(name="Коала", icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Рандомный мем**",
		usage="meme",
		help="**Примеры использования:**\n1. {Prefix}meme\n\n**Пример 1:** Покажет рандомный мем :3",
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def meme(self, ctx):
		url = "https://pda.anekdot.ru/random/mem/"
		headers = {
			"User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"
		}
		html = requests.get(url, headers=headers).text
		soup = bs(html, "lxml")
		data = soup.find_all("div", {"class": "topicbox"})
		images = []

		for i in data:
			if str(i.img) != "None":
				try:
					images.append(i.img.attrs["src"])
				except:
					images.append(i.img.attrs["data-src"])

		emb = discord.Embed(color=discord.Color.green())
		emb.set_image(url=random.choice(images))
		emb.set_author(name="Мем года", icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		name="color-view",
		aliases=["colorview"],
		usage="color-view [Цвет]",
		description="**Цвет в изображении**",
		help="**Примеры использования:**\n1. {Prefix}color-view #444444\n\n**Пример 1:** Покажет изображении в указаном цвете"
	)
	@commands.cooldown(1, 30, commands.BucketType.member)
	async def colorview(self, ctx, color: str):
		if color.startswith("#"):
			hex = color[1:]
			if len(hex) == 6:
				emb = discord.Embed(
					description=f"Цвет `{color}` в изображении",
					colour=discord.Color.green()
				)
				emb.set_image(url=f"https://some-random-api.ml/canvas/colorviewer?hex={hex}")
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
			else:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**Указан не правильный формат цвета!**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction("❌")
				return
		else:
			emb = discord.Embed(
				title="Ошибка!",
				description=f"**Указан не правильный формат цвета!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction("❌")
			return


def setup(client):
	client.add_cog(Games(client))
