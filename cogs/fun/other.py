import discord
import qrcode
import wikipedia
import cv2
import random
import aiohttp
from aiohttp import client_exceptions
from pyzbar import pyzbar
from discord.ext import commands


class FunOther(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.FOOTER = self.client.config.FOOTER_TEXT

    @commands.command(
        aliases=["cr-qr", "cr_qr", "create-qr", "create_qrcode"],
        name="create-qrcode",
        description="Закодирует указаный текст в qr-код",
        usage="create-qrcode [Ваш текст]",
        help="**Примеры использования:**\n1. {Prefix}create-qrcode My text\n\n**Пример 1:** Создаёт QR-код с указаным текстом",
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def cr_qr(self, ctx, *, code_text: str):
        if len(code_text) > 6000:
            emb = await self.client.utils.create_error_embed(
                ctx, "Используйте текст меньше 6000 символов!"
            )
            await ctx.send(embed=emb)
            return

        img = qrcode.make(code_text)
        img.save("././data/images/myqr.jpg")

        emb = discord.Embed(
            title="Функция создания qr-кодов",
            description=f"**Кодируемый текст:**\n```{code_text}```",
            colour=discord.Color.green(),
        )
        emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(
            embed=emb,
            content="**Ваш qr-код**",
            file=discord.File("././data/images/myqr.jpg"),
        )

    @commands.command(
        aliases=["dcode_qr", "d_qr", "d-qr"],
        name="dcode-qrcode",
        description="Разкодирует qr-код",
        usage="dcode-qrcode [Ссылка на изображения]",
        help="**Примеры использования:**\n1. {Prefix}dcode-qrcode https://media.discordapp.net/attachments/717776571406090313/775762508211945482/myqr.jpg\n\n**Пример 1:** Раскодирует QR-код в указаном изображении",
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def scan_url(self, ctx, url: str):
        try:
            async with aiohttp.ClientSession().request("GET", url=url) as response:
                raw = await response.read()

        except client_exceptions.InvalidURL:
            emb = await self.client.utils.create_error_embed(ctx, "Указан неверный формат ссылки!")
            await ctx.send(embed=emb)
            return

        img_file = open("././data/images/qr_url.png", "wb")
        img_file.write(raw)
        img_file.close()

        img = cv2.imread("././data/images/qr_url.png")
        try:
            bs = pyzbar.decode(img)
        except TypeError:
            emb = await self.client.utils.create_error_embed(ctx, "Указана неверная ссылка!")
            await ctx.send(embed=emb)
            return

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
            break

    @commands.command(
        description="Википедия, расказывает о вашем запросе",
        usage="wiki [Ваш запрос]",
        help="**Примеры использования:**\n1. {Prefix}wiki Bot\n\n**Пример 1:** Покажет информацию по запросе `Bot` на википедии",
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def wiki(self, ctx, *, text: str):
        try:
            async with ctx.typing():
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
        description="Магический шар предсказаний",
        usage="8ball [Ваш вопрос]",
        help="**Примеры использования:**\n1. {Prefix}8ball My owner is nice programmer?\n\n**Пример 1:** Ответит на ваш вопрос магическим образом =)",
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def magic_ball(self, ctx, *, msg: str):
        rand_num = random.randint(1, 3)

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


def setup(client):
    client.add_cog(FunOther(client))
