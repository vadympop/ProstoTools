import discord
import json
import typing
import time
import datetime
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
		reason: str = "Причина не указана",
		message: bool = True,
	) -> typing.Union[discord.Embed, bool, None]:
		client = self.client
		overwrite = discord.PermissionOverwrite(send_messages=False)

		mute_time = self.client.utils.time_to_num(type_time)
		times = time.time()+mute_time[0]

		data = await self.client.database.sel_user(target=member)
		role = get(ctx.guild.roles, name=self.MUTE_ROLE)
		if not role:
			role = await ctx.guild.create_role(name=self.MUTE_ROLE)

		await member.add_roles(role)
		for channel in ctx.guild.text_channels:
			await channel.set_permissions(role, overwrite=overwrite)

		cur_lvl = data["level"]
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

		await self.client.database.update(
			"users",
			where={"user_id": member.id, "guild_id": ctx.guild.id},
			money=cur_money,
			coins=cur_coins,
			reputation=cur_reputation,
			items=json.dumps(cur_items),
			prison=str(prison)
		)

		if message:
			description_time = str(mute_time[1]) + str(mute_time[2]) if mute_time[0] != 0 else "Перманентно"
			emb = discord.Embed(
				description=f"**{member}**({member.mention}) Был замьючен\nВремя: `{description_time}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow()
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)

			emb = discord.Embed(
				description=f"Вы были замьчены на сервере\nСервер: `{ctx.guild.name}`\nВремя: `{description_time}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow()
			)
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			try:
				await member.send(embed=emb)
			except:
				pass

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

		data = await self.client.database.sel_user(target=member)
		info = await self.client.database.sel_guild(guild=ctx.guild)
		max_warns = int(info["warns_settings"]["max"])
		warn_punishment = info["warns_settings"]["punishment"]
		cur_lvl = data["level"]
		cur_coins = data["coins"]
		cur_money = data["money"]
		cur_warns = data["warns"]
		cur_state_pr = data["prison"]
		cur_reputation = data["reputation"] - 10

		warn_id = await self.client.database.set_warn(
			target=member,
			reason=reason,
			author=author.id,
			time=str(datetime.datetime.utcnow()),
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

		if len([warn for warn in cur_warns if warn["state"]]) >= max_warns:
			cur_coins -= 1000

			if cur_reputation < -100:
				cur_reputation = -100

			if cur_coins < 0:
				cur_coins = 0

			if warn_punishment is not None:
				if warn_punishment["type"] == "mute":
					await self.client.support_commands.main_mute(
						ctx=ctx,
						member=member,
						type_time=warn_punishment["time"],
						reason=reason,
						author=ctx.author,
					)
				elif warn_punishment["type"] == "kick":
					try:
						await member.kick(reason=reason)
					except discord.errors.Forbidden:
						pass
				elif warn_punishment["type"] == "ban":
					ban_time = self.client.utils.time_to_num(
						data["auto_mod"]["anti_invite"]["punishment"]["time"]
					)
					times = time.time() + ban_time[0]
					try:
						await member.ban(reason=reason)
					except discord.errors.Forbidden:
						pass

					if ban_time > 0:
						await self.client.database.update(
							"users",
							where={"user_id": member.id, "guild_id": ctx.guild.id},
							money=0,
							coins=0,
							reputation=-100,
							items=json.dumps([]),
							clan=""
						)
						await self.client.database.set_punishment(
							type_punishment="ban", time=times, member=member
						)
				elif warn_punishment["type"] == "soft-ban":
					softban_time = self.client.utils.time_to_num(
						data["auto_mod"]["anti_invite"]["punishment"]["time"]
					)
					times = time.time() + softban_time[0]
					overwrite = discord.PermissionOverwrite(
						connect=False, view_channel=False, send_messages=False
					)
					role = discord.utils.get(
						ctx.guild.roles, name=self.SOFTBAN_ROLE
					)
					if role is None:
						role = await ctx.guild.create_role(name=self.SOFTBAN_ROLE)

					await member.edit(voice_channel=None)
					for channel in ctx.guild.channels:
						await channel.set_permissions(role, overwrite=overwrite)

					await member.add_roles(role)
					if softban_time[0] > 0:
						await self.client.database.set_punishment(
							type_punishment="temprole", time=times, member=member, role=role.id
						)

			for warn_id in [warn["id"] for warn in cur_warns]:
				await self.client.database.del_warn(ctx.guild.id, warn_id)
		else:
			emb_ctx = discord.Embed(
				description=f"**{member}**({member.mention}) Получил предупреждения\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns) + 1}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow()
			)
			emb_ctx.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb_ctx.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)

			emb_member = discord.Embed(
				description=f"Вы получили предупреждения на сервере\nСервер: `{ctx.guild.name}`\nId предупреждения: {warn_id}\nКоличество предупреждений: `{len(cur_warns) + 1}`\nМодератор: `{ctx.author}`\nПричина: **{reason}**",
				colour=discord.Color.green(),
				timestamp=datetime.datetime.utcnow()
			)
			emb_member.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb_member.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			try:
				await member.send(embed=emb_member)
			except:
				pass

		await self.client.database.update(
			"users",
			where={"user_id": member.id, "guild_id": ctx.guild.id},
			money=cur_money,
			coins=cur_coins,
			reputation=cur_reputation,
			prison=str(cur_state_pr)
		)
		return emb_ctx
