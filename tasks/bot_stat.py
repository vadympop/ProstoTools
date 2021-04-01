import psutil as ps
import logging

from core.bases.cog_base import BaseCog
from discord.ext import tasks

logger = logging.getLogger(__name__)


class TasksBotStat(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.ping_stat_loop.start()
        self.cpu_stat_loop.start()
        self.memory_stat_loop.start()
        self.cache_size_stat_loop.start()

    @tasks.loop(minutes=2)
    async def ping_stat_loop(self):
        await self.client.wait_until_ready()
        logger.info("Trying to add ping stat")
        try:
            ping = round(self.client.latency * 1000)
            await self.client.database.add_stat_counter(entity="ping", add_counter=int(ping))
        except Exception as e:
            logger.error(f"An error occurred when adding ping stat: {repr(e)}")
        else:
            logger.info("Ping stat was added")

    @tasks.loop(minutes=2)
    async def cpu_stat_loop(self):
        await self.client.wait_until_ready()
        logger.info("Trying to add cpu stat")
        try:
            await self.client.database.add_stat_counter(entity="cpu", add_counter=ps.cpu_percent())
        except Exception as e:
            logger.error(f"An error occurred when adding cpu stat: {repr(e)}")
        else:
            logger.info("Cpu stat was added")

    @tasks.loop(minutes=2)
    async def memory_stat_loop(self):
        await self.client.wait_until_ready()
        logger.info("Trying to add memory stat")

        mem = ps.virtual_memory()
        try:
            await self.client.database.add_stat_counter(
                entity="memory used",
                add_counter=mem.used // 1024 // 1024
            )
            await self.client.database.add_stat_counter(
                entity="memory free",
                add_counter=mem.free
            )
            await self.client.database.add_stat_counter(
                entity="memory cached",
                add_counter=mem.cached
            )
            await self.client.database.add_stat_counter(
                entity="memory percent",
                add_counter=mem.percent
            )
        except Exception as e:
            logger.error(f"An error occurred when adding memory stat: {repr(e)}")
        else:
            logger.info("Memory stat was added")

    @tasks.loop(minutes=2)
    async def cache_size_stat_loop(self):
        await self.client.wait_until_ready()
        logger.info("Trying to add cache stat")
        try:
            await self.client.database.add_stat_counter(
                entity="cache users",
                add_counter=self.client.cache.users.count()
            )
            await self.client.database.add_stat_counter(
                entity="cache guilds",
                add_counter=self.client.cache.guilds.count()
            )
            await self.client.database.add_stat_counter(
                entity="cache punishments",
                add_counter=self.client.cache.punishments.count()
            )
            await self.client.database.add_stat_counter(
                entity="cache reminders",
                add_counter=self.client.cache.reminders.count()
            )
            await self.client.database.add_stat_counter(
                entity="cache status_reminders",
                add_counter=self.client.cache.status_reminders.count()
            )
            await self.client.database.add_stat_counter(
                entity="cache blacklist",
                add_counter=self.client.cache.blacklist.count()
            )
            await self.client.database.add_stat_counter(
                entity="cache giveaways",
                add_counter=self.client.cache.giveaways.count()
            )
        except Exception as e:
            logger.error(f"An error occurred when adding cache stat: {repr(e)}")
        else:
            logger.info("Cache stat was added")


def setup(client):
    client.add_cog(TasksBotStat(client))
