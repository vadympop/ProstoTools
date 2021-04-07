from core.bases.cog_base import BaseCog
from discord.ext import commands


class Shoplist(BaseCog):
    @commands.command()
    async def shoplist(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @shoplist.command(
        aliases=["show", "list", "ls"]
    )
    async def view(self, ctx):
        shoplist = (await self.client.database.sel_guild(guild=ctx.guild)).shop_list

    @shoplist.command()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, *, name: str):
        shoplist = (await self.client.database.sel_guild(guild=ctx.guild)).shop_list

    @shoplist.command()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, *, entity: str):
        shoplist = (await self.client.database.sel_guild(guild=ctx.guild)).shop_list

    @shoplist.command()
    @commands.has_permissions(administrator=True)
    async def edit(self, ctx, field: str, value: str):
        fields = ("description", "name", "count", "durability", "durability_mode")
        if field.lower() not in fields:
            return

        if field.lower() in ("durability", "count") and not value.isdigit():
            return

        if field.lower() == "durability_mode" and field.lower() not in ("off", "on"):
            return

        shoplist = (await self.client.database.sel_guild(guild=ctx.guild)).shop_list


def setup(client):
    client.add_cog(Shoplist(client))