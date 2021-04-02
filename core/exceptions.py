from discord.ext import commands


class ProstoToolsException(commands.CommandError):
    pass


class CommandOff(ProstoToolsException):
    pass


class CommandRoleRequired(ProstoToolsException):
    pass


class CommandChannelRequired(ProstoToolsException):
    pass


class CommandRoleIgnored(ProstoToolsException):
    pass


class CommandChannelIgnored(ProstoToolsException):
    pass


class RoleHigherThanYour(ProstoToolsException):
    pass


class RoleHigherThanMy(ProstoToolsException):
    pass


class TakeActionWithMe(ProstoToolsException):
    pass


class TakeActionWithYourself(ProstoToolsException):
    pass


class TakeActionWithOwner(ProstoToolsException):
    pass


class Blacklisted(ProstoToolsException):
    pass


class BadTimeArgument(ProstoToolsException):
    pass