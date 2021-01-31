import discord
import asyncio
from discord.ext import commands


class Giveaways(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.FOOTER = self.client.config.FOOTER_TEXT

    @commands.group()
    async def giveaway(self, ctx):
        if ctx.invoked_subcommand is None:
            PREFIX = str(await self.client.database.get_prefix(ctx.guild))
            commands = "\n".join(
                [f"`{PREFIX}giveaway {c.name}`" for c in self.client.get_command("giveaway").commands]
            )
            emb = discord.Embed(
                title="Команды розыгрышей",
                description=commands,
                colour=discord.Color.green(),
            )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

    @giveaway.command()
    async def create(self, ctx, type_time: str, winners: int, channel: discord.TextChannel = None):
        await ctx.send("Введите названия розыгрыша")
        try:
            await self.client.wait_for(
                "message",
                check=lambda m: m.channel == ctx.channel and m.author == ctx.author,
                timeout=120
            )
        except asyncio.TimeoutError:
            await ctx.send("Время вышло!")
        else:
            await ctx.send("Введите приз розыгрыша")
            try:
                await self.client.wait_for(
                    "message",
                    check=lambda m: m.channel == ctx.channel and m.author == ctx.author,
                    timeout=120
                )
            except asyncio.TimeoutError:
                await ctx.send("Время вышло!")
            else:
                if channel is None:
                    channel = ctx.channel

                await channel.send("Yeah")
                await self.client.database.add_giveaway()


def setup(client):
    client.add_cog(Giveaways(client))
