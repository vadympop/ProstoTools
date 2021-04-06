import traceback
import discord
import datetime

from core import Paginator
from core.converters import BlacklistEntity
from core.bases.cog_base import BaseCog
from discord.ext import commands


class Owner(BaseCog):
    async def cog_check(self, ctx):
        return await ctx.bot.is_owner(ctx.author)

    @commands.group(aliases=["bl", "b"])
    async def blacklist(self, ctx):
        pass

    @blacklist.command(aliases=["a"])
    async def add(self, ctx, entity: BlacklistEntity, *, reason: str):
        type_entity = "guild" if isinstance(entity, discord.Guild) else "user"
        await self.client.database.add_blacklist_entity(
            entity_id=entity.id,
            type_entity=type_entity,
            reason=reason
        )
        try:
            await ctx.message.add_reaction("✅")
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

    @blacklist.command(aliases=["r", "rm"])
    async def remove(self, ctx, entity: BlacklistEntity):
        await self.client.database.del_blacklist_entity(entity_id=entity.id)
        try:
            await ctx.message.add_reaction("✅")
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

    @blacklist.command(aliases=["l", "ls"])
    async def list(self, ctx):
        blacklist = await self.client.database.get_blacklist_entities()
        if len(blacklist) > 0:
            embeds = []
            entities = []
            for entity in blacklist:
                adding_time = datetime.datetime.fromtimestamp(entity.time).strftime("%d %B %Y %X")
                text = f"""Id: `{entity.id}`\nId сущности: {entity.entity_id}\nТип: {entity.type}\nПричина: **{entity.reason[:256]}**\nВремя добавления: `{adding_time}`"""
                entities.append(text)

            grouped_warns = [entities[x:x + 10] for x in range(0, len(entities), 10)]
            for group in grouped_warns:
                emb = discord.Embed(
                    title=f"Черный список",
                    description="\n\n".join(group),
                    colour=discord.Color.green(),
                )
                emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
                emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
                embeds.append(emb)

            message = await ctx.send(embed=embeds[0])
            paginator = Paginator(ctx, message, embeds, footer=True)
            await paginator.start()
        else:
            emb = discord.Embed(
                title=f"Черный список",
                description="Черный список пуст",
                colour=discord.Color.green(),
            )
            emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

    @commands.command()
    async def _sh(self, ctx, *, message: str = None):
        try:
            result = await self.client.template_engine.render(ctx.message, ctx.author, message)
        except Exception:
            await ctx.send(f"```{traceback.format_exc()}```")
        else:
            try:
                await ctx.send(result)
            except Exception:
                await ctx.send(f"```{traceback.format_exc()}```")

    @commands.command()
    async def _rc(self, ctx, *, command: str):
        command = self.client.get_command(command)
        command.reset_cooldown(ctx)
        await ctx.message.add_reaction("✅")


def setup(client):
    client.add_cog(Owner(client))