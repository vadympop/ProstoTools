import discord
import json
import typing
import time
import datetime
from datetime import datetime
from discord.utils import get


class Commands:
	def __init__(self, client):
		self.client = client
		self.MUTE_ROLE = self.client.config.MUTE_ROLE
		self.VMUTE_ROLE = self.client.config.VMUTE_ROLE
		self.SOFTBAN_ROLE = self.client.config.SOFTBAN_ROLE
		self.FOOTER = self.client.config.FOOTER_TEXT

	async def main_mute(
		self,
		ctx,
		member: discord.Member,
		author: discord.User,
		type_time: str = None,
		check_role: bool = True,
		reason: str = "Причина не указана",
		message: bool = True,
	) -> typing.Union[discord.Embed, bool]:
		client = self.client
		overwrite = discord.PermissionOverwrite(send_messages=False)

		mute_time = self.client.utils.time_to_num(type_time)
		times = time.time()+mute_time[0]

		if member in ctx.guild.members:
			data = await self.client.database.sel_user(target=member)
		else:
			return

		role = get(ctx.guild.roles, name=self.MUTE_ROLE)
		if not role:
			role = await ctx.guild.create_role(name=self.MUTE_ROLE)

		if check_role:
			if role in member.roles:
				emb = discord.Embed(
					title="Ошибка!",
					description=f"**Указаный пользователь уже замьючен!**",
					colour=discord.Color.green(),
				)
				emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
				return

		await member.add_roles(role)
		for channel in ctx.guild.text_channels:
			await channel.set_permissions(role, overwrite=overwrite)

		cur_lvl = data["lvl"]
		cur_coins = data["coins"] - 1500
		cur_money = data["money"]
		cur_reputation = data["reputation"] - 15
		cur_items = data["items"]
		prison = data["prison"]

		if cur_reputation < -100:
			cur_reputation = -100

		if cur_lvl <= 3:
			cur_money -= 250
		elif 3 < cur_lvl <= 5:
			cur_money -= 500
		elif cur_lvl > 5:
			cur_money -= 1000

		if cur_money <= -5000:
			prison = True
			cur_items = []
			emb_member = discord.Embed(
				description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком.**",
				colour=discord.Color.green(),
			)
			emb_member.set_author(
				name=client.user.name, icon_url=client.user.avatar_url
			)
			emb_member.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
			try:
				await member.send(embed=emb_member)
			except:
				pass

		sql = """UPDATE users SET money = %s, coins = %s, reputation = %s, items = %s, prison = %s WHERE user_id = %s AND guild_id = %s"""
		val = (
			cur_money,
			cur_coins,
			cur_reputation,
			json.dumps(cur_items),
			str(prison),
			member.id,
			ctx.guild.id,
		)

		await self.client.database.execute(sql, val)

		if mute_time[0] <= 0:
			if message:
				if reason:
					emb = discord.Embed(
						description=f"**{member.mention} Был перманентно замьючен по причине {reason}**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
				elif not reason:
					emb = discord.Embed(
						description=f"**{member.mention} Был перманентно замьючен**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
		elif mute_time[0] != 0:
			if message:
				if reason:
					emb = discord.Embed(
						description=f"**{member.mention} Был замьючен по причине {reason} на {mute_time[1]}{mute_time[2]}**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
				elif not reason:
					emb = discord.Embed(
						description=f"**{member.mention} Был замьючен на {mute_time[1]}{mute_time[2]}**",
						colour=discord.Color.green(),
					)
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)

		if mute_time[0] > 0:
			await self.client.database.set_punishment(
				type_punishment="mute",
				time=times,
				member=member,
				role_id=role.id,
				reason=reason,
				author=author.id,
			)

		if message:
			return emb
		elif not message:
			return True

	async def main_warn(
		self, ctx, member: discord.Member, author: discord.User, reason: str = None
	) -> discord.Embed:
		client = self.client

		if member in ctx.guild.members:
			data = await self.client.database.sel_user(target=member)
		else:
			return

		info = await self.client.database.sel_guild(guild=ctx.guild)
		max_warns = int(info["max_warns"])
		cur_lvl = data["lvl"]
		cur_coins = data["coins"]
		cur_money = data["money"]
		cur_warns = data["warns"]
		cur_state_pr = data["prison"]
		cur_reputation = data["reputation"] - 10

		warn_id = await self.client.database.set_warn(
			target=member,
			reason=reason,
			author=author.id,
			time=str(datetime.today()),
		)

		if cur_lvl <= 3:
			cur_money -= 250
		elif 3 < cur_lvl <= 5:
			cur_money -= 500
		elif cur_lvl > 5:
			cur_money -= 1000

		if cur_money <= -5000:
			cur_state_pr = True
			emb_member = discord.Embed(
				description=f"**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Текущий баланс - {cur_money}**",
				colour=discord.Color.green(),
			)
			emb_member.set_author(
				name=client.user.name, icon_url=client.user.avatar_url
			)
			emb_member.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
			await member.send(embed=emb_member)

		if cur_reputation < -100:
			cur_reputation = -100

		if len(cur_warns) >= 20:
			await self.client.database.del_warn(
				guild_id=ctx.guild.id,
				warn_id=[warn for warn in cur_warns if not warn["state"]][0]["id"]
			)

		if len(cur_warns) >= max_warns:
			await self.main_mute(
				ctx,
				member=member,
				author=author,
				type_time="2h",
				check_role=False,
				message=False,
			)
			emb_ctx = discord.Embed(
				description=f"**{member.mention} Достиг максимального значения предупреждения и был замючен на 2 часа.**",
				colour=discord.Color.green(),
			)
			emb_ctx.set_author(name=client.user.name, icon_url=client.user.avatar_url)
			emb_ctx.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
		else:
			emb_member = discord.Embed(
				description=f"**Вы были предупреждены {author.mention} по причине {reason}. Предупрежденний `{len(cur_warns)}`, id - `{warn_id}`**",
				colour=discord.Color.green(),
			)
			emb_member.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb_member.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)
			await member.send(embed=emb_member)

			emb_ctx = discord.Embed(
				description=f"**Пользователь {member.mention} получил предупреждения по причине {reason}. Количество предупрежденний - `{len(cur_warns)}`, id - `{warn_id}`**",
				colour=discord.Color.green(),
			)
			emb_ctx.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb_ctx.set_footer(text=self.FOOTER, icon_url=client.user.avatar_url)

		sql = """UPDATE users SET money = %s, coins = %s, reputation = %s, prison = %s WHERE user_id = %s AND guild_id = %s"""
		val = (cur_money, cur_coins, cur_reputation, str(cur_state_pr))

		await self.client.database.execute(sql, val)
		return emb_ctx
