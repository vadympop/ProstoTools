import discord
import uuid
from discord.ext import commands
from discord.utils import get
from colorama import *

init()


class Errors(commands.Cog, name="Errors"):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		PREFIX = self.client.database.get_prefix(guild=ctx.guild)

		if isinstance(error, commands.errors.CommandOnCooldown):
			await ctx.message.add_reaction("❌")
			retry_after = error.retry_after
			if retry_after < 60:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**Кулдавн в команде еще не прошёл! Подождите {int(retry_after)} секунд**",
					colour=discord.Color.green(),
				)
			elif retry_after > 60 and retry_after < 1800:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**Кулдавн в команде еще не прошёл! Подождите {int(retry_after / 60)} минут**",
					colour=discord.Color.green(),
				)
			elif retry_after > 1800:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**Кулдавн в команде еще не прошёл! Подождите {int(retry_after / 60 / 24)} часа**",
					colour=discord.Color.green(),
				)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif isinstance(error, commands.errors.MissingRequiredArgument):
			emb = await self.client.utils.create_error_embed(
				ctx,
				f"**Вы не указали аргумент. Укажити аргумент - {error.param.name} к указаной команде!**\n\n{ctx.command.help.format(Prefix=PREFIX)}"
				if ctx.command.help is not None
				else "**Указан не правильный аргумент!**",
				False
			)
			await ctx.send(embed=emb)
		elif isinstance(error, commands.errors.CommandNotFound):
			pass
		elif isinstance(error, commands.errors.NotOwner):
			await ctx.message.add_reaction("❌")
			emb = discord.Embed(
				title="Ошибка!",
				description="**Вы неявляетесь создателем бота! Эта команда только для создателей!**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif isinstance(error, commands.errors.MissingPermissions) or isinstance(error, commands.errors.CheckFailure):
			emb = await self.client.utils.create_error_embed(
				ctx, "У вас не достаточно прав на использования данной команды!"
			)
			await ctx.send(embed=emb)
		elif isinstance(error, commands.errors.BadArgument):
			emb = await self.client.utils.create_error_embed(
				ctx,
				f"**Указан не правильный аргумент!**\n\n{ctx.command.help.format(Prefix=PREFIX)}"
				if ctx.command.help is not None
				else "**Указан не правильный аргумент!**",
				False
			)
			await ctx.send(embed=emb)
		elif isinstance(error, commands.errors.BotMissingPermissions):
			owner = get(ctx.guild.members, id=ctx.guild.owner_id)
			emb_err = await self.client.utils.create_error_embed(
				ctx,
				f"У бота отсутствуют права: {' '.join(error.missing_perms)}\nВыдайте их ему для полного функционирования бота"
			)
			await owner.send(embed=emb_err)
		elif isinstance(error, commands.errors.MemberNotFound):
			emb = await self.client.utils.create_error_embed(ctx, "Указаный пользователь не найден!")
			await ctx.send(embed=emb)
		else:
			error_id = str(uuid.uuid4())
			await self.client.database.set_error(error_id, repr(error), ctx.command.name)
			await ctx.message.add_reaction("❌")
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