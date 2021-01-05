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

	@commands.command(
		help="**Примеры использования:**\n1. {Prefix}help\n2. {Prefix}help moderate\n2. {Prefix}help ban\n\n**Пример 1:** Показывает список всех команд бота\n**Пример 2:** Показывает список всех указаной групы\n**Пример 3:** Показывает документацию по указаной команде"
	)
	async def help(self, ctx, cog_name: str = None):
		groups = ["settings", "works", "clans"]
		moder_roles = (await self.client.database.sel_guild(guild=ctx.guild))["moder_roles"]
		PREFIX = self.client.database.get_prefix(guild=ctx.guild)
		cogs_aliases = {
			"economy": "Economy",
			"funeditimage": "FunEditImage",
			"funother": "FunOther",
			"funrandomimage": "FunRandomImage",
			"clans": "Clans",
			"different": "Different",
			"moderate": "Moderate",
			"settings": "Settings",
			"utils": "Utils",
			"works": "Works"
		}

		if cog_name is None:
			emb = await self.client.utils.build_help(ctx, PREFIX, groups, moder_roles)
			await ctx.send(embed=emb)
			return

		if cog_name.lower() not in cogs_aliases.keys():
			if cog_name.lower() not in self.commands:
				str_cogs = ", ".join([
					cogs_aliases[cog.lower()] for cog in self.client.cogs
					if cog.lower() in cogs_aliases.keys()
				])
				emb = discord.Embed(
					title="Ошибка!",
					description=f"Такой категории нет, введите названия правильно. Список доступных категорий: {str_cogs}",
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

		def add_command_field(emb, c):
			emb.add_field(
				name=f"{PREFIX}{c.usage}",
				value=f"{c.description[2:-2]}.",
				inline=False,
			)

		def check_command_permissions(emb, c):
			if not c.hidden:
				if c.brief != "True":
					add_command_field(emb, c)
				else:
					state = False
					for role_id in moder_roles:
						if ctx.guild.get_role(role_id) in ctx.author.roles:
							state = True
							break

					if state or ctx.guild.owner == ctx.author or ctx.author.guild_permissions.administrator:
						add_command_field(emb, c)
			else:
				if ctx.guild.owner == ctx.author or ctx.author.guild_permissions.administrator:
					add_command_field(emb, c)

		emb_2 = discord.Embed(
			title=f"Категория команд - {cogs_aliases[cog_name.lower()]}",
			description="[Пример] - требуется, |Пример| - необязательно",
			colour=discord.Color.green(),
		)
		for c in self.client.get_cog(cogs_aliases[cog_name.lower()]).get_commands():
			if self.client.get_cog(cogs_aliases[cog_name.lower()]).qualified_name.lower() in groups:
				for command in c.commands:
					check_command_permissions(emb_2, command)
			else:
				check_command_permissions(emb_2, c)
		emb_2.set_author(
			name=self.client.user.name, icon_url=self.client.user.avatar_url
		)
		emb_2.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb_2)


def setup(client):
	client.add_cog(Help(client))
