import uuid
import datetime
import json
import typing
import time as tm
import discord

from core.services.cache.cache_manager import CacheItem
from django.db import connection
from django.forms.models import model_to_dict
from .models import User, Warn, Giveaway, Guild, StatusReminder, Reminder, Mute, Punishment, Error, BotStat, Blacklist


class Database:
    def __init__(self, client):
        self.client = client
        self.cache = self.client.cache
        self.DB_HOST = self.client.config.DB_HOST
        self.DB_USER = self.client.config.DB_USER
        self.DB_PASSWORD = self.client.config.DB_PASSWORD
        self.DB_DATABASE = self.client.config.DB_DATABASE

    async def add_giveaway(
            self,
            channel_id: int,
            message_id: int,
            creator: discord.Member,
            num_winners: int,
            time: int,
            name: str,
            prize: int
    ) -> int:
        new_giveaway = Giveaway(
            guild_id=creator.guild.id,
            channel_id=channel_id,
            message_id=message_id,
            creator_id=creator.id,
            num_winners=num_winners,
            time=time,
            name=name,
            prize=prize
        )
        new_giveaway.save()

        self.cache.giveaways.add(model_to_dict(new_giveaway))
        return new_giveaway.id

    async def del_giveaway(self, giveaway_id: int) -> Giveaway:
        delete_giveaway = Giveaway.objects.get(id=giveaway_id)
        delete_giveaway.delete()

        self.cache.giveaways.remove(id=giveaway_id)
        return delete_giveaway

    async def get_giveaways(self, **kwargs) -> typing.List[Giveaway]:
        cached_giveaways = self.cache.giveaways.find(**kwargs)
        if len(cached_giveaways) > 0:
            return cached_giveaways

        return Giveaway.objects.filter(**kwargs)

    async def get_giveaway(self, giveaway_id: int) -> Giveaway:
        cached_giveaway = self.cache.giveaways.get(id=giveaway_id)
        if cached_giveaway is not None:
            return cached_giveaway

        return Giveaway.objects.get(id=giveaway_id)

    async def add_status_reminder(self, target_id: int, member_id: int, wait_for: str, type_reminder: str) -> int:
        new_reminder = StatusReminder(
            target_id=target_id,
            member_id=member_id,
            wait_for=wait_for,
            type=type_reminder
        )
        new_reminder.save()

        self.cache.status_reminders.add(model_to_dict(new_reminder))
        return new_reminder.id

    async def get_status_reminders(self, **kwargs) -> typing.List[StatusReminder]:
        cached_reminders = self.cache.status_reminders.find(**kwargs)
        if len(cached_reminders) > 0:
            return cached_reminders

        return StatusReminder.objects.filter(**kwargs)

    async def get_status_reminder(self, **kwargs) -> StatusReminder:
        cached_reminder = self.cache.status_reminders.get(**kwargs)
        if cached_reminder is not None:
            return cached_reminder

        return StatusReminder.objects.get(**kwargs)

    async def del_status_reminder(self, status_reminder_id: int) -> bool:
        db_reminder = StatusReminder.objects.get(id=status_reminder_id)
        if db_reminder is None:
            return False

        db_reminder.delete()
        self.cache.status_reminders.remove(id=status_reminder_id)
        return True

    async def add_reminder(
            self,
            member: discord.Member,
            channel: discord.TextChannel,
            time: int,
            text: str,
    ) -> int:
        new_reminder = Reminder(
            user_id=member.id,
            guild_id=member.guild.id,
            text=text,
            time=time,
            channel_id=channel.id
        )
        new_reminder.save()

        self.cache.reminders.add(model_to_dict(new_reminder))
        return new_reminder.id

    async def get_reminders(self, **kwargs) -> typing.List[Reminder]:
        cached_reminders = self.cache.reminders.find(**kwargs)
        if len(cached_reminders) > 0:
            return cached_reminders

        return Reminder.objects.filter(**kwargs)

    async def del_reminder(self, reminder_id: int) -> bool:
        db_reminder = Reminder.objects.get(id=reminder_id)
        if db_reminder is None:
            return False

        db_reminder.delete()
        self.cache.reminders.remove(id=reminder_id)
        return True

    async def add_warn(self, user_id: int, guild_id: int, reason: str, author: int) -> int:
        warns_count = Warn.objects.filter(user_id=user_id, guild_id=guild_id).count()+1
        new_warn = Warn(
            user_id=user_id,
            guild_id=guild_id,
            reason=reason,
            state=True,
            time=tm.time(),
            author=author,
            num=warns_count
        )
        new_warn.save()

        return new_warn.id

    async def del_warn(self, warn_id: int) -> typing.Optional[Warn]:
        db_warn = Warn.objects.get(id=warn_id)
        if db_warn is None:
            return None

        db_warn.update(state=False)
        return db_warn

    async def del_warns(self, **kwargs) -> None:
        Warn.objects.filter(**kwargs).update(state=False)

    async def get_warns(self, **kwargs) -> typing.List[Warn]:
        return Warn.objects.filter(**kwargs)

    async def add_mute(self, user_id: int, guild_id: int, reason: str, active_to: int, author: int) -> int:
        new_mute = Mute(
            user_id=user_id,
            guild_id=guild_id,
            reason=reason,
            active_to=active_to,
            time=tm.time(),
            author=author
        )
        new_mute.save()

        return new_mute.id

    async def del_mute(self, user_id: int, guild_id: int) -> None:
        db_mute = Mute.objects.get(user_id=user_id, guild_id=guild_id)
        if db_mute is None:
            return

        db_mute.delete()

    async def get_mutes(self, guild_id: int) -> typing.List[Mute]:
        return Mute.objects.filter(guild_id=guild_id)

    async def get_mute(self, guild_id: int, member_id: int) -> Mute:
        return Mute.objects.get(guild_id=guild_id, member_id=member_id)

    async def add_punishment(
            self,
            type_punishment: str,
            time: int,
            member: discord.Member,
            role_id: int = 0,
            **kwargs,
    ) -> None:
        new_punishment = Punishment(
            member_id=member.id,
            guild_id=member.guild.id,
            type=type_punishment,
            time=time,
            role_id=role_id
        )
        new_punishment.save()

        self.cache.punishments.add(model_to_dict(new_punishment))
        if type_punishment == "mute":
            await self.add_mute(
                active_to=time,
                user_id=member.id,
                guild_id=member.guild.id,
                reason=kwargs.pop("reason"),
                author=kwargs.pop("author"),
            )

    async def get_punishments(self) -> typing.List[Punishment]:
        cached_punishments = self.cache.punishments.items
        if len(cached_punishments) > 0:
            return [CacheItem(**p) for p in cached_punishments if p["time"] < tm.time()]

        return Punishment.objects.filter(time__lt=tm.time())

    async def del_punishment(self, member: discord.Member, guild_id: int, type_punishment: str) -> None:
        if type_punishment == "mute":
            await self.del_mute(member.id, member.guild.id)

        db_punishment = Punishment.objects.get(member_id=member.id, guild_id=guild_id, type=type_punishment)
        if db_punishment is None:
            return

        db_punishment.delete()
        self.cache.punishments.remove(member_id=member.id, guild_id=guild_id, type=type_punishment)

    async def sel_user(self, target: discord.Member) -> User:
        cached_user = self.cache.users.get(guild_id=target.guild.id, user_id=target.id)
        if cached_user is not None:
            return cached_user

        db_user = User.objects.get(user_id=target.id, guild_id=target.guild.id)
        if db_user is None:
            new_user = User(
                user_id=target.id,
                guild_id=target.guild.id,
                level=1,
                exp=0,
                money=0,
                coins=0,
                text_channel=20,
                reputation=0,
                prison="False",
                profile="default",
                bio="",
                clan="",
                items=[],
                pets=[],
                transactions=[],
            )
            new_user.save()
            self.cache.users.add(model_to_dict(new_user))
            return new_user

        return db_user

    async def sel_guild(self, guild: discord.Guild) -> Guild:
        cached_guild = self.cache.guilds.get(guild_id=guild.id)
        if cached_guild is not None:
            return cached_guild

        db_guild = Guild.objects.get(guild_id=guild.id)
        if db_guild is None:
            new_guild = Guild(
                guild_id=guild.id,
                textchannels_category=0,
                exp_multi=100,
                timedelete_textchannel=30,
                donate=False,
                prefix="p.",
                api_key=str(uuid.uuid4()),
                server_stats={},
                voice_channel={},
                shop_list=[],
                ignored_channels=[],
                auto_mod={
                    "anti_flud": {"state": False},
                    "anti_invite": {"state": False},
                    "anti_caps": {"state": False},
                    "react_commands": False,
                    "captcha": {"state": False}
                },
                clans=[],
                moderators=[],
                auto_reactions={},
                welcomer={
                    "join": {"state": False},
                    "leave": {"state": False}
                },
                auto_roles={},
                custom_commands=[],
                autoresponders={},
                audit={},
                rank_message={
                    "state": False
                },
                commands_settings={},
                warns_settings={"max": 3, "punishment": None},
            )
            self.cache.guilds.add(model_to_dict(new_guild))
            return new_guild

        return db_guild

    async def get_prefix(self, guild: discord.Guild):
        cached_guild = self.cache.guilds.get(guild_id=guild.id)
        if cached_guild is not None:
            return cached_guild.prefix

        return Guild.objects.get(guild_id=guild.id).prefix

    async def get_moder_roles(self, guild: discord.Guild):
        cached_guild = self.cache.guilds.get(guild_id=guild.id)
        if cached_guild is not None:
            return cached_guild.moderators

        return Guild.objects.get(guild_id=guild.id).moderators

    async def execute(
            self, query: str, val: typing.Iterable = (), fetchone: bool = False
    ) -> list:
        with connection.cursor() as cursor:
            cursor.execute(query, val)
            if fetchone:
                data = cursor.fetchone()
            else:
                data = cursor.fetchall()
        return data

    async def update(self, table: str, **kwargs):
        where = kwargs.pop("where")
        columns = []
        values = []
        for key, value in kwargs.items():
            columns.append(f"{key} = %s")
            values.append(json.dumps(value))

        query = ", ".join(columns)
        where_statement = ' AND '.join([
            f"{key} = {value}"
            for key, value in where.items()
        ])
        cached_entity = self.cache.__getattribute__(table).get(**where)
        if cached_entity is not None:
            cached_entity.update(kwargs)

        await self.execute(
            f"""UPDATE {table} SET {query} WHERE {where_statement}""",
            values
        )

    async def add_stat_counter(
            self, entity: str = "all commands", add_counter: int = None
    ) -> None:
        if add_counter is None:
            BotStat.objects.create(
                count=BotStat.objects.filter(entity="all commands").count()+1,
                timestamp=datetime.datetime.utcnow(),
                entity="all commands"
            )

        BotStat.objects.create(
            count=add_counter if add_counter is not None else BotStat.objects.filter(entity=entity).count()+1,
            timestamp=datetime.datetime.utcnow(),
            entity=entity
        )

    async def add_error(self, error_id: str, traceback: str, command: str) -> None:
        Error.objects.create(
            error_id=error_id,
            time=datetime.datetime.now(),
            traceback=traceback,
            command=command
        )

    async def add_blacklist_entity(self, entity_id: int, type_entity: str, reason: str) -> int:
        new_blacklist_entity = Blacklist(
            time=tm.time(),
            entity_id=entity_id,
            type=type_entity,
            reason=reason
        )
        new_blacklist_entity.save()

        self.cache.blacklist.add(model_to_dict(new_blacklist_entity))
        return new_blacklist_entity.id

    async def get_blacklist_entities(self, **kwargs) -> typing.List[Blacklist]:
        cached_blacklist_entities = self.cache.blacklist.find(**kwargs)
        if len(cached_blacklist_entities) > 0:
            return cached_blacklist_entities

        return Blacklist.objects.filter(**kwargs)

    async def get_blacklist_entity(self, **kwargs) -> Blacklist:
        cached_blacklist_entity = self.cache.status_reminders.get(**kwargs)
        if cached_blacklist_entity is not None:
            return cached_blacklist_entity

        return Blacklist.objects.get(**kwargs)

    async def del_blacklist_entity(self, **kwargs) -> bool:
        db_blacklist_entity = Blacklist.objects.get(**kwargs)
        if db_blacklist_entity is None:
            return False

        db_blacklist_entity.delete()
        self.cache.blacklist.remove(**kwargs)
        return True
