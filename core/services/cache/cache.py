from .cache_manager import CacheManager
from core.services.database.models import Blacklist, Reminder, StatusReminder, Punishment, Giveaway


class Cache:
    users = CacheManager(name="Users", max_size=4000)
    guilds = CacheManager(name="Guilds", max_size=1000)
    blacklist = CacheManager(name="Blacklist", max_size=2000)
    reminders = CacheManager(name="Reminders", max_size=1500)
    punishments = CacheManager(name="Punishments", max_size=2000)
    status_reminders = CacheManager(name="StatusReminders", max_size=1500)
    giveaways = CacheManager(name="Giveaways", max_size=1000)

    async def run(self):
        self.blacklist.items = list(Blacklist.objects.all().values())
        self.reminders.items = list(Reminder.objects.all().values())
        self.status_reminders.items = list(StatusReminder.objects.all().values())
        self.giveaways.items = list(Giveaway.objects.all().values())
        self.punishments.items = list(Punishment.objects.all().values())