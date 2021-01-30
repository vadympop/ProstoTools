from discord.ext import commands


class CommandOff(commands.CommandError):
    pass


class CommandTargetRoleRequired(commands.CommandError):
    pass


class CommandTargetChannelRequired(commands.CommandError):
    pass


class CommandRoleIgnored(commands.CommandError):
    pass


class CommandChannelIgnored(commands.CommandError):
    pass
