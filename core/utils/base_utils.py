import discord
import random

from core.services.database.models import Giveaway
from core.exceptions import *


class Utils:
    def __init__(self, client):
        self.client = client
        self.FOOTER = self.client.config.FOOTER_TEXT

    async def create_error_embed(self, ctx, error_msg: str, bold: bool = False):
        emb = discord.Embed(
            title="Ошибка!",
            description=f"**{error_msg}**" if bold else error_msg,
            colour=discord.Color.red()
        )
        emb.set_author(name="Документация", icon_url=ctx.author.avatar_url, url="https://docs.prosto-tools.ml")
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        try:
            await ctx.message.add_reaction("❌")
        except discord.errors.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass
        return emb

    async def global_command_check(self, ctx):
        if await self.client.database.get_blacklist_entity(
            entity_id=ctx.guild.id
        ) is not None or await self.client.database.get_blacklist_entity(
            entity_id=ctx.author.id
        ) is not None:
            raise Blacklisted

        commands_settings = (await self.client.database.sel_guild(guild=ctx.guild)).commands_settings
        if ctx.command.name in commands_settings.keys():
            if not commands_settings[ctx.command.name]["state"]:
                raise CommandOff

            if commands_settings[ctx.command.name]["target_channels"]:
                if ctx.channel.id not in commands_settings[ctx.command.name]["target_channels"]:
                    raise CommandChannelRequired

            if commands_settings[ctx.command.name]["target_roles"]:
                state = False
                for role in ctx.author.roles:
                    if role.id in commands_settings[ctx.command.name]["target_roles"]:
                        state = True

                if not state:
                    raise CommandRoleRequired

            if ctx.channel.id in commands_settings[ctx.command.name]["ignore_channels"]:
                raise CommandChannelIgnored

            for role in ctx.author.roles:
                if role.id in commands_settings[ctx.command.name]["ignore_roles"]:
                    raise CommandRoleIgnored

        return True

    async def end_giveaway(self, giveaway: Giveaway) -> bool:
        guild = self.client.get_guild(giveaway.guild_id)
        if guild is None:
            await self.client.database.del_giveaway(giveaway.id)
            return False

        channel = guild.get_channel(giveaway.channel_id)
        if channel is None:
            await self.client.database.del_giveaway(giveaway.id)
            return False

        try:
            message = await channel.fetch_message(giveaway.message_id)
        except discord.errors.NotFound:
            await self.client.database.del_giveaway(giveaway.id)
            return False

        message_reactions = message.reactions
        if "🎉" not in [str(r.emoji) for r in message_reactions]:
            await self.client.database.del_giveaway(giveaway.id)
            return False

        reacted_users = []
        for reaction in message_reactions:
            if str(reaction.emoji) == "🎉":
                reacted_users = await reaction.users().flatten()
                break

        for user in reacted_users:
            if user.bot:
                reacted_users.remove(user)

        winners = []
        for _ in range(giveaway.num_winners):
            if reacted_users == []:
                break

            winner = random.choice(reacted_users)
            winners.append(winner)
            reacted_users.remove(winner)

        if winners == []:
            winners_str = "Не удалось определить победителей!"
        else:
            winners_str = ", ".join([u.mention for u in winners])
        message.embeds[0].colour = discord.Color.green()
        message.embeds[0].description = f"**Розыгрыш окончен!**\n\nПобедители: {winners_str}\nОрганизатор: {guild.get_member(giveaway.creator_id)}\nПриз:\n>>> {giveaway.prize}"
        await message.edit(content="⏰ Розыгрыш окончен!", embed=message.embeds[0])
        await channel.send(
            f"**Розыгрыш** {message.jump_url} **окончен**\n**Победители:** {winners_str}"
        )
        await self.client.database.del_giveaway(giveaway.id)
        return True
