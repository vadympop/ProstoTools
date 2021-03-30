from django.db import models
from django.core.exceptions import ObjectDoesNotExist


class QuerySet(models.query.QuerySet):
    def get(self, *args, **kwargs):
        try:
            return super().get(*args, **kwargs)
        except ObjectDoesNotExist:
            return None


class Manager(models.manager.BaseManager.from_queryset(QuerySet)):
    pass


class Warn(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField()
    guild_id = models.BigIntegerField()
    reason = models.TextField()
    state = models.BooleanField()
    time = models.BigIntegerField()
    author = models.BigIntegerField()
    num = models.IntegerField()
    objects = Manager()

    class Meta:
        db_table = "warns"


class Reminder(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField()
    guild_id = models.BigIntegerField()
    text = models.TextField()
    time = models.BigIntegerField()
    channel_id = models.BigIntegerField()
    objects = Manager()

    class Meta:
        db_table = "reminders"


class Mute(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField()
    guild_id = models.BigIntegerField()
    reason = models.TextField()
    active_to = models.BigIntegerField()
    time = models.BigIntegerField()
    author = models.BigIntegerField()
    objects = Manager()

    class Meta:
        db_table = "mutes"


class Giveaway(models.Model):
    id = models.BigAutoField(primary_key=True)
    guild_id = models.BigIntegerField()
    channel_id = models.BigIntegerField()
    message_id = models.BigIntegerField()
    creator_id = models.BigIntegerField()
    num_winners = models.IntegerField()
    time = models.BigIntegerField()
    name = models.TextField()
    prize = models.TextField()
    objects = Manager()

    class Meta:
        db_table = "giveaways"


class StatusReminder(models.Model):
    id = models.BigAutoField(primary_key=True)
    target_id = models.BigIntegerField()
    user_id = models.BigIntegerField()
    wait_for = models.TextField()
    type = models.TextField()
    objects = Manager()

    class Meta:
        db_table = "status_reminders"


class Punishment(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField()
    guild_id = models.BigIntegerField()
    type = models.TextField()
    time = models.BigIntegerField()
    role_id = models.BigIntegerField()
    objects = Manager()

    class Meta:
        db_table = "punishments"


class BotStat(models.Model):
    id = models.BigAutoField(primary_key=True)
    count = models.BigIntegerField()
    timestamp = models.DateTimeField()
    entity = models.TextField()
    objects = Manager()

    class Meta:
        db_table = "bot_stats"


class Error(models.Model):
    error_id = models.TextField(primary_key=True)
    time = models.DateTimeField()
    traceback = models.TextField()
    command = models.TextField()
    objects = Manager()

    class Meta:
        db_table = "errors"


class User(models.Model):
    user_id = models.BigIntegerField(primary_key=True)
    guild_id = models.BigIntegerField(primary_key=True)
    level = models.BigIntegerField()
    exp = models.BigIntegerField()
    money = models.BigIntegerField()
    coins = models.BigIntegerField()
    reputation = models.BigIntegerField()
    prison = models.BooleanField()
    profile = models.TextField()
    bio = models.TextField()
    clan = models.TextField()
    items = models.JSONField()
    pets = models.JSONField()
    transactions = models.JSONField()
    bonuses = models.JSONField()
    objects = Manager()

    class Meta:
        db_table = "users"


class Guild(models.Model):
    guild_id = models.BigIntegerField(primary_key=True)
    exp_multi = models.FloatField()
    donate = models.BooleanField()
    prefix = models.TextField()
    api_key = models.TextField()
    timezone = models.TextField()
    server_stats = models.JSONField()
    voice_channel = models.JSONField()
    shop_list = models.JSONField()
    ignored_channels = models.JSONField()
    auto_mod = models.JSONField()
    clans = models.JSONField()
    moderators = models.JSONField()
    auto_reactions = models.JSONField()
    welcomer = models.JSONField()
    auto_roles = models.JSONField()
    custom_commands = models.JSONField()
    autoresponders = models.JSONField()
    audit = models.JSONField()
    rank_message = models.JSONField()
    commands_settings = models.JSONField()
    warns_settings = models.JSONField()
    objects = Manager()

    class Meta:
        db_table = "guilds"


class Blacklist(models.Model):
    id = models.BigAutoField(primary_key=True)
    time = models.BigIntegerField()
    entity_id = models.BigIntegerField()
    type = models.TextField()
    reason = models.TextField()
    objects = Manager()

    class Meta:
        db_table = "blacklist"


class AuditLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    guild_id = models.BigIntegerField()
    user_id = models.BigIntegerField()
    time = models.DateTimeField()
    username = models.TextField()
    discriminator = models.IntegerField()
    avatar_url = models.TextField()
    type = models.TextField()

    class Meta:
        db_table = "audit_logs"