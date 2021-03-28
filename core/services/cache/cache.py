from .cache_manager import CacheManager
from core.services.database.models import Blacklist, Reminder, StatusReminder, Punishment, Giveaway


class Cache:
    users = CacheManager(name="Users", max_length=2000)
    guilds = CacheManager(name="Guilds", max_length=500)
    blacklist = CacheManager(name="Blacklist", max_length=2000)
    reminders = CacheManager(name="Reminders", max_length=1500)
    punishments = CacheManager(name="Punishments", max_length=2000)
    status_reminders = CacheManager(name="StatusReminders", max_length=1500)
    giveaways = CacheManager(name="Giveaways", max_length=1000)

    async def run(self):
        self.blacklist.items = list(Blacklist.objects.all().values())
        self.reminders.items = list(Reminder.objects.all().values())
        self.status_reminders.items = list(StatusReminder.objects.all().values())
        self.giveaways.items = list(Giveaway.objects.all().values())
        self.punishments.items = list(Punishment.objects.all().values())