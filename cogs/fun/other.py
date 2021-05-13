import discord
import random

from core.bases.cog_base import BaseCog
from discord.ext import commands


class FunOther(BaseCog):
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
