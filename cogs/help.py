import discord

from discord.ext import commands
from discord.utils import get


class Help(commands.Cog, name="Help"):
	def __init__(self, client):
		self.client = client
		self.FOOTER = self.client.config.FOOTER_TEXT
		self._names = []
		for cog in self.client.cogs:
			for command in self.client.get_cog(cog).get_commands():
				for alias in command.aliases:
					self._names.append(alias)
				self._names.append(command.name)
		self.commands = self._names

	@commands.command()
	async def works(self, ctx):

		purge = self.client.clear_commands(ctx.guild)
		Prefix = self.get_prefix(self.client, ctx)
		await ctx.channel.purge(limit=purge)

		emb = discord.Embed(
			title="Категория команд - works",
			description="[Пример] - требуется, |Пример| - необязательно",
			colour=discord.Color.green(),
		)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)

		emb.add_field(
			name=f"{Prefix}loader",
			value="**Работа грузчиком. Получает от 80$ до 100$, можна работать с 3 уровня, кулдавн 3 часа после 2 попыток**",
			inline=False,
		)
		emb.add_field(
			name=f"{Prefix}treasure-hunter",
			value="**Работа кладо искателем. Получает от 0$(Ты ничего не нашёл) до 500$, можна работать с 2 уровня, нужно купить апарат за 500$ или второго уровня за 1000$(На 20% больше найти клад), кулдавн 5 часов**",
			inline=False,
		)
		emb.add_field(
			name=f"{Prefix}barman",
			value="**Работа барменом. Получает 150$ + чаевые до 50$, можна работать с 4 уровня, кулдавн 3 часа после 2 попыток**",
			inline=False,
		)
		emb.add_field(
			name=f"{Prefix}cleaner",
			value="**Работа уборщиком. Получает от 40$ до 50$, уровень пользователя не важен, кулдавн 2 часа после 3 попыток**",
			inline=False,
		)
		emb.add_field(
			name=f"{Prefix}window-washer",
			value="**Работа мойщиком окон. Получает от 250$ до 300$, можна работать с 5 уровня, может упасть и потерять 300$, кулдавн 5 часов**",
			inline=False,
		)

		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)

		await ctx.send(embed=emb)

	@commands.command(
		help="**Примеры использования:**\n1. {Prefix}help\n2. {Prefix}help moderate\n2. {Prefix}help ban\n\n**Пример 1:** Показывает список всех команд бота\n**Пример 2:** Показывает список всех указаной групы\n**Пример 3:** Показывает документацию по указаной команде"
	)
	async def help(self, ctx, cog_name: str = None):
		purge = await self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)
		groups = ["settings", "works", "clans"]
		PREFIX = self.client.database.get_prefix(guild=ctx.guild)

		if cog_name is None:
			emb = await self.client.utils.build_help(ctx, PREFIX, groups)
			await ctx.send(embed=emb)
			return

		if cog_name.lower() not in [cog.lower() for cog in self.client.cogs]:
			if cog_name.lower() not in self.commands:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"Такой категории нет, введите названия правильно. Список доступных категорий: {', '.join([cog.lower() for cog in self.client.cogs])}",
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				return
			else:
				aliases = (
					f"""Алиасы команды: {', '.join(self.client.get_command(cog_name.lower()).aliases)}\n\n"""
					if self.client.get_command(cog_name.lower()).aliases != []
					else ""
				)
				emb = discord.Embed(
					title=f"Команда: {PREFIX+cog_name.lower()}",
					description=aliases
					+ self.client.get_command(cog_name.lower()).help.format(
						Prefix=PREFIX
					),
					colour=discord.Color.green(),
				)
				emb.set_author(
					name=self.client.user.name, icon_url=self.client.user.avatar_url
				)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				return

		emb_2 = discord.Embed(
			title=f"Категория команд - {cog_name.capitalize()}",
			description="[Пример] - требуется, |Пример| - необязательно",
			colour=discord.Color.green(),
		)
		for c in self.client.get_cog(cog_name.capitalize()).get_commands():
			if (
				self.client.get_cog(cog_name.capitalize()).qualified_name.lower()
				in groups
			):
				for command in c.commands:
					emb_2.add_field(
						name=f"{PREFIX}{command.usage}",
						value=f"{command.description[2:-2]}.",
						inline=False,
					)
			else:
				emb_2.add_field(
					name=f"{PREFIX}{c.usage}",
					value=f"{c.description[2:-2]}.",
					inline=False,
				)
		emb_2.set_author(
			name=self.client.user.name, icon_url=self.client.user.avatar_url
		)
		emb_2.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb_2)


def setup(client):
	client.add_cog(Help(client))
