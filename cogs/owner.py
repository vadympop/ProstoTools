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


def update():
    from core.services.database.models import Guild

    for i in Guild.objects.all():
        i.warns_settings.update({
            "state": i.warns_settings["punishment"] is not None,
            "role": {"type": "add", "role_id": None, "time": None}
        })
        i.auto_mod.update({
            "anti_mentions": {
                "state": False,
                "max_mentions": 4,
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            },
            "anti_link": {
                "state": False,
                "domains": [],
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            },
            "auto_nick_corrector": {
                "state": False,
                "target_roles": [],
                "ignore_roles": [],
                "replace_with": "New nick",
                "percent": 60
            },
        })
        if "anti_caps" in i.auto_mod.keys():
            i.auto_mod["anti_caps"].update({"min_chars": 10})
            for j in ("target_roles", "target_channels", "ignore_roles", "ignore_channels"):
                if j not in i.auto_mod["anti_caps"].keys():
                    i.auto_mod["anti_caps"][j] = []
        else:
            i.auto_mod["anti_caps"] = {
                "state": False,
                "percent": 40,
                "min_chars": 10,
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            }

        if "anti_flud" in i.auto_mod.keys():
            for j in ("target_roles", "target_channels", "ignore_roles", "ignore_channels"):
                if j not in i.auto_mod["anti_flud"].keys():
                    i.auto_mod["anti_flud"][j] = []
        else:
            i.auto_mod["anti_flud"] = {
                "state": False,
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            }

        if "anti_invite" in i.auto_mod.keys():
            for j in ("target_roles", "target_channels", "ignore_roles", "ignore_channels"):
                if j not in i.auto_mod["anti_invite"].keys():
                    i.auto_mod["anti_invite"][j] = []
        else:
            i.auto_mod["anti_invite"] = {
                "state": False,
                "target_roles": [],
                "target_channels": [],
                "ignore_roles": [],
                "ignore_channels": [],
            }

        ec = i.audit["economy"] if "economy" in i.audit.keys() else None
        mc = i.audit["moderate"] if "moderate" in i.audit.keys() else None
        cc = i.audit["clans"] if "clans" in i.audit.keys() else None
        ms = "moderate" in i.audit.keys()
        es = "economy" in i.audit.keys()
        cs = "clan" in i.audit.keys()
        me = 'message_edit'
        md = 'message_delete'
        i.audit = {
            'message_edit': {'state': me in i.audit.keys(), "channel_id": i.audit[me] if me in i.audit.keys() else None},
            'message_delete': {'state': md in i.audit.keys(), "channel_id": i.audit[md] if md in i.audit.keys() else None},
            'member_mute': {'state': ms, "channel_id": mc},
            'member_unmute': {'state': ms, "channel_id": mc},
            'member_vmute': {'state': ms, "channel_id": mc},
            'member_unvmute': {'state': ms, "channel_id": mc},
            'member_ban': {'state': ms, "channel_id": mc},
            'member_unban': {'state': ms, "channel_id": mc},
            'member_nick_update': {"state": False, "channel_id": None},
            'member_roles_update': {"state": False, "channel_id": None},
            'clan_delete': {'state': cs, "channel_id": cc},
            'clan_create': {'state': cs, "channel_id": cc},
            'money_remove': {'state': es, "channel_id": ec},
            'money_add': {'state': es, "channel_id": ec},
            'member_voice_move': {'state': False, "channel_id": None},
            'member_voice_connect': {'state': False, "channel_id": None},
            'member_voice_disconnect': {'state': False, "channel_id": None},
            'member_join': {'state': False, "channel_id": None},
            'member_leave': {'state': False, "channel_id": None},
            'bot_join': {'state': False, "channel_id": None},
            'bot_leave': {'state': False, "channel_id": None},
            'member_kick': {'state': ms, "channel_id": mc},
            'new_warn': {'state': ms, "channel_id": mc},
            'warns_reset': {'state': ms, "channel_id": mc}
        }
        Guild.objects.filter(guild_id=i.guild_id).update(
            warns_settings=i.warns_settings,
            audit=i.audit,
            auto_mod=i.auto_mod
        )
