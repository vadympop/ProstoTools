from discord.ext import commands


class CommandOff(commands.CommandError):
    pass


class CommandRoleRequired(commands.CommandError):
    pass


class CommandChannelRequired(commands.CommandError):
    pass


class CommandRoleIgnored(commands.CommandError):
    pass


class CommandChannelIgnored(commands.CommandError):
    pass
