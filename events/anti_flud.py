import discord

from core.bases.cog_base import BaseCog
from core.utils.other import process_auto_moderate
from discord.ext import commands


class EventsAntiFlud(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.messages = {}

    def update(self, time: int, key: str, message: discord.Message):
        if key not in self.messages.keys():
            self.messages.update({
                key: [{
                    "time": time,
                    "content": message.content
                }]
            })
        else:
            self.messages[key].append({
                "time": time,
                "content": message.content
            })

        if len(self.messages[key]) > 10:
            self.messages[key].pop(0)

    def remove(self, key: str, items: list):
        for item in items:
            try:
                self.messages[key].remove(item)
            except KeyError:
                pass

        if not len(self.messages[key]):
            self.messages.pop(key)

    def get_after(self, key: str, time: int, limit: int = 5) -> list:
        return [message for message in self.messages[key] if message["time"] >= time][limit:]

    def get_same_by_content(self, items: list) -> list:
        same = []
        [
            same.append(item)
            for item in items
            if item["content"].lower() not in [i["content"].lower() for i in same]
        ]
        return same

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        key = f"{message.guild.id}/{message.author.id}"
        time = (await self.client.utils.get_guild_time(message.guild)).timestamp()
        self.update(time, key, message)
        messages_after = self.get_after(
            key, int(time-10)
        )
        if not messages_after:
            return

        if len(self.get_same_by_content(messages_after)) == 1:
            self.remove(f"{message.guild.id}/{message.author.id}", messages_after)
            data = await self.client.database.sel_guild(guild=message.guild)
            if data.auto_mod["anti_flud"]["state"]:
                await process_auto_moderate(await self.client.get_context(message), "anti_flud", data)


def setup(client):
    client.add_cog(EventsAntiFlud(client))
