import discord
import uuid
import humanize

from core.bases.cog_base import BaseCog
from core.exceptions import *
from discord.ext import commands
from colorama import *

init()


class Errors(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.ignored = (
			commands.errors.CommandNotFound,
			commands.errors.NotOwner,
			CommandOff
		)
		self.PERMISSIONS_DICT = self.client.config.PERMISSIONS_DICT

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		if ctx.guild is None:
			return

		PREFIX = str(await self.client.database.get_prefix(guild=ctx.guild))
		if isinstance(error, self.ignored):
			return

		if isinstance(error, commands.errors.CommandOnCooldown):
			retry = humanize.precisedelta(error.retry_after, minimum_unit='seconds')
			emb = await self.client.utils.create_error_embed(
				ctx, f"**Кулдавн в команде еще не прошёл! Подождите {retry}**"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, commands.errors.MissingRequiredArgument):
			ctx.command.reset_cooldown(ctx)
			command_usage = f"\n*Использование команды:*\n{PREFIX}{ctx.command.usage}" if ctx.command.usage is not None else ""
			command_help = f"\n\n{ctx.command.help.format(Prefix=PREFIX)}" if ctx.command.help is not None else ""
			emb = await self.client.utils.create_error_embed(
				ctx,
				f"**Вы не указали аргумент. Укажити аргумент - {error.param.name} к указанной команде!**"+command_usage+command_help
			)
			await ctx.send(embed=emb)
		elif isinstance(error, commands.BadColourArgument):
			emb = await self.client.utils.create_error_embed(
				ctx, "Цвет указан в неправильном формате! Цвет должен быть в `hex` формате"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, (commands.errors.BadArgument, commands.errors.BadUnionArgument)):
			ctx.command.reset_cooldown(ctx)
			command_usage = f"\n*Использование команды:*\n{PREFIX}{ctx.command.usage}" if ctx.command.usage is not None else ""
			command_help = f"\n\n{ctx.command.help.format(Prefix=PREFIX)}" if ctx.command.help is not None else ""
			emb = await self.client.utils.create_error_embed(
				ctx, f"**Указан неправильный аргумент!**"+command_usage+command_help
			)
			await ctx.send(embed=emb)
		elif isinstance(error, commands.errors.BotMissingPermissions):
			ctx.command.reset_cooldown(ctx)
			missing_perms = ", ".join([self.PERMISSIONS_DICT[p] for p in error.missing_perms])
			emb = await self.client.utils.create_error_embed(
				ctx, f"У бота отсутствуют права: {missing_perms}\nВыдайте их ему для полного функционирования бота"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, (commands.errors.MissingPermissions, commands.errors.CheckFailure)):
			ctx.command.reset_cooldown(ctx)
			emb = await self.client.utils.create_error_embed(
				ctx, "У вас не достаточно прав на использования данной команды!"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, commands.errors.MemberNotFound):
			ctx.command.reset_cooldown(ctx)
			emb = await self.client.utils.create_error_embed(ctx, "Указаный пользователь не найден!")
			await ctx.send(embed=emb)
		elif isinstance(error, BadTimeArgument):
			emb = await self.client.utils.create_error_embed(
				ctx,
				"Время указанно в неправильном формате!\n\n*Примеры правильного использования:*\n`1m` - через одну минуту\n`2030-05-01.10:30` - в определенное время, в 2030-ом году первого мая в 10:30"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, Blacklisted):
			try:
				await ctx.message.add_reaction("✋")
			except discord.errors.Forbidden:
				pass
			except discord.errors.HTTPException:
				pass
		elif isinstance(error, CommandRoleRequired):
			emb = await self.client.utils.create_error_embed(
				ctx, "У вас нет необходимых ролей!"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, CommandChannelRequired) or isinstance(error, CommandChannelIgnored):
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете использовать эту команду в этом канале!"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, CommandRoleIgnored):
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете использовать эту команду с вашей ролью!"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, RoleHigherThanYour):
			emb = await self.client.utils.create_error_embed(
				ctx, "В указанного пользователя роль выше чем ваша!"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, RoleHigherThanMy):
			emb = await self.client.utils.create_error_embed(
				ctx, "В указанного пользователя роль выше чем моя!"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, TakeActionWithYourself):
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете применить эту команду к себе!"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, TakeActionWithMe):
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете взаимодействовать с ботом в этой команде!"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, TakeActionWithOwner):
			emb = await self.client.utils.create_error_embed(
				ctx, "Вы не можете взаимодействовать с владельцем сервера в этой команде!"
			)
			await ctx.send(embed=emb)
		else:
			ctx.command.reset_cooldown(ctx)
			if isinstance(error.original, discord.errors.Forbidden):
				emb = await self.client.utils.create_error_embed(
					ctx, f"У бота отсутствуют необходимые права!"
				)
				await ctx.send(embed=emb)
				return
			elif isinstance(error.original, discord.errors.NotFound):
				return

			error_id = str(uuid.uuid4())
			await self.client.database.add_error(
				error_id=error_id,
				traceback=repr(error),
				command=ctx.message.content,
				guild_id=ctx.guild.id,
				user_id=ctx.author.id
			)
			try:
				await ctx.message.add_reaction("❌")
			except discord.errors.Forbidden:
				pass
			except discord.errors.HTTPException:
				pass
			emb = discord.Embed(
				title="Ошибка!",
				description="**Произошла неизвестная ошибка, обратитесь к моему создателю!**",
				colour=discord.Color.red(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=f"Id ошибки: {error_id}", icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			raise error


def setup(client):
	client.add_cog(Errors(client))
