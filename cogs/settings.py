import discord
import typing

from core.bases.cog_base import BaseCog
from discord.ext import commands


class Settings(BaseCog):
	def __init__(self, client):
		super().__init__(client)
		self.FILTERS = self.client.config.FILTERS

	@commands.group(
		usage="setting [Команда]",
		description="Категория команд - настройки",
		help=f"""**Команды групы:** shop-role, auto-reactions\n\n"""
	)
	@commands.guild_only()
	@commands.has_permissions(administrator=True)
	async def setting(self, ctx):
		if ctx.invoked_subcommand is None:
			PREFIX = str(await self.client.database.get_prefix(ctx.guild))
			commands = "\n".join(
				[f"`{PREFIX}setting {c.name}`" for c in self.client.get_command("setting").commands]
			)
			emb = discord.Embed(
				title="Команды настройки",
				description=commands,
				colour=discord.Color.green(),
			)
			emb.set_author(
				name=self.client.user.name, icon_url=self.client.user.avatar_url
			)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

	@setting.command(
		name="shop-role",
		description="Настройка магазина на сервере",
		usage="setting shop-role [clear - очищает список ролей, add - добавляет роль, delete - удаляет роль] [@Роль] [Стоимость роли]",
	)
	@commands.has_permissions(administrator=True)
	async def shoplist(
		self, ctx, cl_add: typing.Optional[str], role: discord.Role, cost: int
	):
		data = await self.client.database.sel_guild(guild=ctx.guild)
		shoplist = data.shop_list

		if cost <= 0:
			emb = await self.client.utils.create_error_embed(ctx, "Укажите стоимость предмета больше 0!")
			await ctx.send(embed=emb)
			return

		if role.is_integration():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль управляется интеграцией!")
			await ctx.send(embed=emb)
			return

		if role.is_bot_managed():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль управляется ботом!")
			await ctx.send(embed=emb)
			return

		if role.is_premium_subscriber():
			emb = await self.client.utils.create_error_embed(ctx, "Указанная роль используеться для бустером сервера!")
			await ctx.send(embed=emb)
			return

		if cl_add == "add":
			shoplist.append([role.id, cost])
			emb = discord.Embed(
				description=f"**Добавленна новая роль - `{role}`, стоимость - `{cost}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif cl_add == "clear":
			shoplist = []
			emb = discord.Embed(
				description=f"**Ваш список продаваемых ролей успешно очищен**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif cl_add == "delete" or cl_add == "remove" or cl_add == "del":
			try:
				for shop_role in shoplist:
					if role.id in shop_role and cost in shop_role:
						shoplist.remove(shop_role)
			except:
				emb = await self.client.utils.create_error_embed(
					ctx, "**Такой роли не существует в списке продаваемых ролей!**"
				)
				await ctx.send(embed=emb)
				return

			emb = discord.Embed(
				description=f"**Вы успешно удалили продаваемую роль из списка продаваемых ролей! Удалённая роль - `{role}`**",
				colour=discord.Color.green(),
			)
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		elif cl_add != "clear" and cl_add != "add":
			emb = await self.client.utils.create_error_embed(
				ctx, "**Укажите одно из этих действий: add, clear, delete!**",
			)
			await ctx.send(embed=emb)
			return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			shop_list=shoplist
		)

	@setting.command(
		name="auto-reactions",
		aliases=["autoreactions"],
		description="Настройка авто-реакций",
		usage="setting auto-reactions [set/off] |Канал| |Эмодзи|",
	)
	@commands.has_permissions(administrator=True)
	async def auto_reactions(self, ctx, action: str, channel: typing.Optional[discord.TextChannel], *reactions):
		auto_reactions = (await self.client.database.sel_guild(guild=ctx.guild)).auto_reactions
		if action.lower() not in ("set", "off", "setting-filters", "sf", "set-filters"):
			emb = await self.client.utils.create_error_embed(
				ctx, "Укажите одно из этих действий: set, off, settings-filters"
			)
			await ctx.send(embed=emb)

		if channel is None:
			channel = ctx.channel

		if action.lower() == "set":
			if len(reactions) <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите эмодзи!"
				)
				await ctx.send(embed=emb)
				return

			auto_reactions.update({
				channel.id: {
					"reactions": reactions,
					"filter_mode": "all",
					"filters": []
				}
			})
		elif action.lower() == "off":
			try:
				auto_reactions.pop(channel.id)
			except KeyError:
				emb = await self.client.utils.create_error_embed(
					ctx, "Для указанного канала авто-реакции не настроены!"
				)
				await ctx.send(embed=emb)
				return
		elif action.lower() in ("setting-filters", "sf", "set-filters"):
			if len(reactions) <= 0:
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите настройку изменения!"
				)
				await ctx.send(embed=emb)
				return

			if reactions[0].lower() not in ("mode", "add", "remove"):
				emb = await self.client.utils.create_error_embed(
					ctx, "Укажите одну из этих настроек: mode, add, remove"
				)
				await ctx.send(embed=emb)
				return

			if reactions[0].lower() == "mode":
				if len(reactions) <= 1:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите режим фильтров!"
					)
					await ctx.send(embed=emb)
					return

				if reactions[1].lower() not in ("any", "all"):
					emb = await self.client.utils.create_error_embed(
						ctx, "Указан неправильный режим!"
					)
					await ctx.send(embed=emb)
					return

				try:
					auto_reactions[channel.id]["filter_mode"] = reactions[1].lower()
				except KeyError:
					emb = await self.client.utils.create_error_embed(
						ctx, "Авто-реакции для указанного канала нету"
					)
					await ctx.send(embed=emb)
					return
			elif reactions[0].lower() == "add":
				if len(reactions) <= 1:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите фильтр!"
					)
					await ctx.send(embed=emb)
					return

				if reactions[1].lower() not in self.FILTERS:
					emb = await self.client.utils.create_error_embed(
						ctx, "Указан неправильный фильтр!"
					)
					await ctx.send(embed=emb)
					return

				try:
					auto_reactions[channel.id]["filters"].append(reactions[1].lower())
				except KeyError:
					emb = await self.client.utils.create_error_embed(
						ctx, "Авто-реакции для указанного канала нету"
					)
					await ctx.send(embed=emb)
					return
			elif reactions[0].lower() == "remove":
				if len(reactions) <= 1:
					emb = await self.client.utils.create_error_embed(
						ctx, "Укажите фильтр!"
					)
					await ctx.send(embed=emb)
					return

				if reactions[1].lower() not in self.FILTERS:
					emb = await self.client.utils.create_error_embed(
						ctx, "Указан неправильный фильтр!"
					)
					await ctx.send(embed=emb)
					return

				try:
					auto_reactions[channel.id]["filters"].remove(reactions[1].lower())
				except KeyError:
					emb = await self.client.utils.create_error_embed(
						ctx, "Авто-реакции для указанного канала нету/В списке фильтров нету указанного"
					)
					await ctx.send(embed=emb)
					return

		await self.client.database.update(
			"guilds",
			where={"guild_id": ctx.guild.id},
			auto_reactions=auto_reactions
		)
		try:
			await ctx.message.add_reaction("✅")
		except discord.errors.Forbidden:
			pass
		except discord.errors.HTTPException:
			pass


def setup(client):
	client.add_cog(Settings(client))
