import discord
import json
import random
import qrcode
import wikipedia
import requests
import cv2
import asyncio
from googletrans import Translator
from pyzbar import pyzbar
from discord.ext import commands
from discord.utils import get
from discord.voice_client import VoiceClient
from discord.ext.commands import Bot
from random import randint
from configs import configs
from bs4 import BeautifulSoup as bs
from Tools.database import DB


class Games(commands.Cog, name="Games"):
	def __init__(self, client):
		self.client = client
		self.FOOTER = configs["FOOTER_TEXT"]

	@commands.command(
		aliases=['cr-qr', 'cr_qr', 'create-qr', 'create_qrcode'],
		name="create-qrcode",
		description="**Закодирует указаный текст в qr-код**",
		usage="create-qrcode [Ваш текст]",
		help='**Примеры использования:**\n1. {Prefix}create-qrcode My text\n\n**Пример 1:** Создаёт QR-код с указаным текстом',
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def cr_qr(self, ctx, *, code_text:str):
		purge = self.client.clear_commands(ctx.guild)
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
		aliases=['dcode_qr', 'd_qr', 'd-qr'],
		name="dcode-qrcode",
		description="**Разкодирует qr-код**",
		usage="dcode-qrcode [Ссылка на изображения]",
		help='**Примеры использования:**\n1. {Prefix}dcode-qrcode https://media.discordapp.net/attachments/717776571406090313/775762508211945482/myqr.jpg\n\n**Пример 1:** Раскодирует QR-код в указаном изображении'
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def scan_url(self, ctx, url:str):
		purge = self.client.clear_commands(ctx.guild)
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
		description="**Мини ивент, состоящий из угадываний флагов разных стран, количество раундов 7, для игры нужно как минимум два человека**",
		usage="flags",
		help='**Примеры использования:**\n1. {Prefix}flags\n\n**Пример 1:** Запускает игру флаги'
	)
	@commands.cooldown(1, 43200, commands.BucketType.member)
	async def flags(self, ctx):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		filename = "./Data/TempFiles/flags.json"
		members = "./Data/TempFiles/event.json"
		dump(members)
		flags = load(filename)
		count = 1

		emb = discord.Embed(
			title=f"Правила игры",
			description="**1. Нельзя читерить!\n2. Ответ должен быть в течении 4мин, если никто не успел ответить ивент заканчиваеться\n\nЖдем игроков(2мин)...**",
			colour=discord.Color.green(),
		)
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		embed = await ctx.send(embed=emb)
		await embed.add_reaction("✅")

		try:
			reaction, user = await self.client.wait_for(
				"reaction_add",
				check=lambda reaction, user: reaction.emoji == "✅",
				timeout=240.0,
			)
		except asyncio.TimeoutError:
			emb = discord.Embed(
				description="**Жаль, но ивент отменяеться, так как никто не пришёл...**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			embed = await ctx.send(embed=emb)
		else:
			while reaction.count <= 3:
				reaction, user = await self.client.wait_for(
					"reaction_add",
					check=lambda reaction, user: reaction.emoji == "✅"
					and reaction.count >= 3,
				)

				if reaction.emoji == "✅" and reaction.count >= 3:
					await asyncio.sleep(5)
					while count <= 6:
						otvet = random.choice(flags["Флаги"])
						emb = discord.Embed(
							title=f"Флаг {count}", colour=discord.Color.green()
						)
						emb.set_image(url=otvet["url"])
						emb.set_author(
							name=ctx.author.name, icon_url=ctx.author.avatar_url
						)
						emb.set_footer(
							text=self.FOOTER, icon_url=self.client.user.avatar_url
						)
						await ctx.send(embed=emb)

						def check(m):
							return (
								m.content == otvet["answer"]
								and ctx.channel == ctx.channel
							)

						try:
							msg = await self.client.wait_for(
								"message", check=check, timeout=120.0
							)
						except asyncio.TimeoutError:
							emb = discord.Embed(
								description="**Никто не успел ответить... Ивент закончен прежде временно**",
								colour=discord.Color.green(),
							)
							emb.set_author(
								name=ctx.author.name, icon_url=ctx.author.avatar_url
							)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await ctx.send(embed=emb)
							break
						else:
							emb = discord.Embed(
								title="Правильный ответ!", colour=discord.Color.green()
							)
							emb.add_field(
								name="Ответил:", value=f"{msg.author.mention}"
							)
							emb.add_field(
								name="Правильный ответ:", value=f"{otvet['answer']}"
							)
							emb.set_author(
								name=self.client.user.name,
								icon_url=self.client.user.avatar_url,
							)
							emb.set_footer(
								text=self.FOOTER, icon_url=self.client.user.avatar_url
							)
							await ctx.send(embed=emb)

							count = count + 1
							await asyncio.sleep(1)
							if count == 7:
								emb = discord.Embed(
									title="Конец игры!",
									description=f"Ивент был проведён {ctx.author.mention}, и мы всем желаем удачи! Спасибо за участие!",
									colour=discord.Color.green(),
								)
								emb.set_author(
									name=self.client.user.name,
									icon_url=self.client.user.avatar_url,
								)
								emb.set_footer(
									text=self.FOOTER,
									icon_url=self.client.user.avatar_url,
								)
								await ctx.send(embed=emb)
				else:
					print(f"Else\nReaction - {reaction}")

	@commands.command(
		description="**Википедия, расказывает о вашем запросе**",
		usage="wiki [Ваш запрос]",
		help='**Примеры использования:**\n1. {Prefix}wiki Bot\n\n**Пример 1:** Покажет информацию по запросе `Bot` на википедии'
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def wiki(self, ctx, *, text:str):
		purge = self.client.clear_commands(ctx.guild)
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
		help='**Примеры использования:**\n1. {Prefix}8ball My owner is nice programmer?\n\n**Пример 1:** Ответит на ваш вопрос магическим образом =)'
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def magic_ball(self, ctx, *, msg:str):
		purge = self.client.clear_commands(ctx.guild)
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
		help='**Примеры использования:**\n1. {Prefix}dog\n\n**Пример 1:** Покажет рандомную картинку собаки'
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def dog(self, ctx):
		response = requests.get("https://some-random-api.ml/img/dog")
		json_data = json.loads(response.text)
		url = json_data["link"]

		emb = discord.Embed(color=discord.Color.green())
		emb.set_image(url=url)
		emb.set_author(name="Собачка", icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Рандомная картинка кошки**", 
		usage="cat",
		help='**Примеры использования:**\n1. {Prefix}cat\n\n**Пример 1:** Покажет рандомную картинку кошки'
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def cat(self, ctx):
		response = requests.get("https://some-random-api.ml/img/cat")
		json_data = json.loads(response.text)
		url = json_data["link"]

		emb = discord.Embed(color=discord.Color.green())
		emb.set_image(url=url)
		emb.set_author(name="Кошечка :3", icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Рандомная картинка лисы**", 
		usage="fox",
		help='**Примеры использования:**\n1. {Prefix}fox\n\n**Пример 1:** Покажет рандомную картинку лисы'
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def fox(self, ctx):
		response = requests.get("https://some-random-api.ml/img/fox")
		json_data = json.loads(response.text)
		url = json_data["link"]

		emb = discord.Embed(color=discord.Color.green())
		emb.set_image(url=url)
		emb.set_author(name="Лиса", icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Рандомная картинка птички**", 
		usage="bird",
		help='**Примеры использования:**\n1. {Prefix}dog\n\n**Пример 1:** Покажет рандомную картинку птички'
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def bird(self, ctx):
		response = requests.get("https://some-random-api.ml/img/birb")
		json_data = json.loads(response.text)
		url = json_data["link"]

		emb = discord.Embed(color=discord.Color.green())
		emb.set_image(url=url)
		emb.set_author(name="Птичка", icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Рандомная картинка коалы**", 
		usage="koala",
		help='**Примеры использования:**\n1. {Prefix}koala\n\n**Пример 1:** Покажет рандомную картинку коалы'
	)
	@commands.cooldown(2, 10, commands.BucketType.member)
	async def koala(self, ctx):
		response = requests.get("https://some-random-api.ml/img/koala")
		json_data = json.loads(response.text)
		url = json_data["link"]

		emb = discord.Embed(color=discord.Color.green())
		emb.set_image(url=url)
		emb.set_author(name="Коала", icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(
		description="**Рандомный мем**", 
		usage="meme",
		help='**Примеры использования:**\n1. {Prefix}meme\n\n**Пример 1:** Покажет рандомный мем :3'
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


def setup(client):
	client.add_cog(Games(client))
