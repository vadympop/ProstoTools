import discord
import random
import aiohttp
from bs4 import BeautifulSoup as bs
from discord.ext import commands


class FunRandomImage(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.FOOTER = self.client.config.FOOTER_TEXT

    @commands.command(
        description="Рандомная картинка собаки",
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
        description="Рандомная картинка кошки",
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
        description="Рандомная картинка лисы",
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
        description="Рандомная картинка птички",
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
        description="Рандомная картинка коалы",
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
        description="Рандомный мем",
        usage="meme",
        help="**Примеры использования:**\n1. {Prefix}meme\n\n**Пример 1:** Покажет рандомный мем :3",
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def meme(self, ctx):
        url = "https://pda.anekdot.ru/random/mem/"
        headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"
        }
        async with ctx.typing():
            async with self.client.session.request("GET", url=url, headers=headers) as response:
                html = await response.text()

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
    client.add_cog(FunRandomImage(client))
