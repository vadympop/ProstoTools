import discord
import random

from core.bases.cog_base import BaseCog
from string import ascii_letters
from discord.utils import get
from discord.ext import commands


class CogName(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.CAPTCHA_ROLE = self.client.config.CAPTCHA_ROLE

    @commands.Cog.listener()
    async def on_member_join(self, member):
        captcha_setting = (await self.client.database.sel_guild(guild=member.guild)).auto_mod["captcha"]
        if captcha_setting["state"]:
            overwrite = discord.PermissionOverwrite(
                connect=False, view_channel=False, send_messages=False
            )
            role = get(member.guild.roles, name=self.CAPTCHA_ROLE)
            if role is None:
                role = await member.guild.create_role(name=self.CAPTCHA_ROLE)

            await member.edit(voice_channel=None)
            for channel in member.guild.channels:
                await channel.set_permissions(role, overwrite=overwrite)

            try:
                await member.add_roles(role)
            except discord.errors.Forbidden:
                return

            attempt_num = 0
            while attempt_num < 3:
                captcha_text = "".join(random.choice(ascii_letters) for _ in range(6))
                emb = discord.Embed(
                    description="Пройдите каптчу",
                    colour=discord.Color.green()
                )
                emb.set_image(
                    url=f"https://useless-api--vierofernando.repl.co/captcha?text={captcha_text}"
                )
                try:
                    await member.send(embed=emb)
                except discord.errors.Forbidden:
                    break

                answer = await self.client.wait_for(
                    "message",
                    check=lambda m: m.author == member and m.guild is None,
                )
                if answer.content.lower() == captcha_text.lower():
                    await member.send("Вы успешно прошли каптчу!")
                    await member.remove_roles(role)
                    break
                else:
                    attempt_num += 1
                    if attempt_num >= 3:
                        await member.send("Каптча не пройдена, вы были кикнуты с сервера!")
                        try:
                            await member.kick()
                        except discord.errors.Forbidden:
                            pass
                    else:
                        await member.send(f"Ответ неправильный, осталось {3-attempt_num} попытки")
                        continue


def setup(client):
    client.add_cog(CogName(client))
