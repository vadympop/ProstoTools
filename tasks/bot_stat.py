import psutil as ps
import pymysql
from discord.ext import commands, tasks


class TasksBotStat(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.ping_stat_loop.start()
        self.cpu_stat_loop.start()
        self.memory_stat_loop.start()
        self.mem = ps.virtual_memory()

    @tasks.loop(minutes=10)
    async def ping_stat_loop(self):
        try:
            ping = round(self.client.latency * 1000)
            await self.client.database.add_amout_command(entity="ping", add_counter=int(ping))
        except AttributeError:
            pass
        except ValueError:
            pass
        except pymysql.IntegrityError:
            pass

    @tasks.loop(minutes=5)
    async def cpu_stat_loop(self):
        try:
            await self.client.database.add_amout_command(entity="cpu", add_counter=ps.cpu_percent())
        except AttributeError:
            pass
        except pymysql.IntegrityError:
            pass

    @tasks.loop(minutes=5)
    async def memory_stat_loop(self):
        try:
            await self.client.database.add_amout_command(entity="memory", add_counter=self.mem.percent)
        except AttributeError:
            pass
        except pymysql.IntegrityError:
            pass


def setup(client):
    client.add_cog(TasksBotStat(client))
