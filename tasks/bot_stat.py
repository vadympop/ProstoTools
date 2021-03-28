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
        self.mem = ps.virtual_memory()

    @tasks.loop(minutes=5)
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

    @tasks.loop(minutes=5)
    async def cpu_stat_loop(self):
        await self.client.wait_until_ready()
        logger.info("Trying to add cpu stat")
        try:
            await self.client.database.add_stat_counter(entity="cpu", add_counter=ps.cpu_percent())
        except Exception as e:
            logger.error(f"An error occurred when adding cpu stat: {repr(e)}")
        else:
            logger.info("Cpu stat was added")

    @tasks.loop(minutes=5)
    async def memory_stat_loop(self):
        await self.client.wait_until_ready()
        logger.info("Trying to add memory stat")
        try:
            await self.client.database.add_stat_counter(entity="memory", add_counter=self.mem.percent)
        except Exception as e:
            logger.error(f"An error occurred when adding memory stat: {repr(e)}")
        else:
            logger.info("Memory stat was added")


def setup(client):
    client.add_cog(TasksBotStat(client))
