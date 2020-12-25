import psutil as ps
from discord.ext import commands, tasks


class TasksBotStat(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.ping_stat_loop.start()
        self.cpu_stat_loop.start()
        self.memory_stat_loop.start()
        self.mem = ps.virtual_memory()

    @tasks.loop(minutes=30)
    async def ping_stat_loop(self):
        if self.client.is_ready():
            try:
                ping = round(self.client.latency * 1000)
                await self.client.database.add_amout_command(entity="ping", add_counter=int(ping))
            except:
                pass

    @tasks.loop(minutes=5)
    async def cpu_stat_loop(self):
        if self.client.is_ready():
            await self.client.database.add_amout_command(entity="cpu", add_counter=ps.cpu_percent())

    @tasks.loop(minutes=10)
    async def memory_stat_loop(self):
        if self.client.is_ready():
            await self.client.database.add_amout_command(entity="memory", add_counter=self.mem.percent)


def setup(client):
    client.add_cog(TasksBotStat(client))
