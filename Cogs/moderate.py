import discord
import json
import asyncio
import typing
import datetime
import time
import random
import os
import mysql.connector
from Tools.commands import Commands
from Tools.database import DB
from random import randint
from datetime import datetime
from discord.ext import commands
from discord.utils import get
from discord.voice_client import VoiceClient
from discord.ext.commands import Bot
from configs import configs

def check_role(ctx):
	data = DB().sel_guild(guild=ctx.guild)['moder_roles']
	roles = ctx.guild.roles
	roles.reverse()
	data.append(roles[0].id)

	if data != []:
		for role in data:
			role = get(ctx.guild.roles, id=role)
			yield role in ctx.author.roles
	else:
		return ctx.author.guild_permission.administrator

class Moderate(commands.Cog, name = 'Moderate'):

	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(user = 'root', password = os.environ['DB_PASSWORD'], host = 'localhost', database = 'data')
		self.cursor = self.conn.cursor(buffered = True)
		self.MUTE_ROLE = configs['MUTE_ROLE']
		self.VMUTE_ROLE = configs['VMUTE_ROLE']
		self.SOFTBAN_ROLE = configs['SOFTBAN_ROLE']
		self.FOOTER = configs['FOOTER_TEXT']


	@commands.command(brief='True', description='**Удаляет указаное число сообщений**', usage='clear |@Участник| [Число удаляемых сообщений]')
	@commands.check(check_role)	
	async def clear(self, ctx, member: typing.Optional[discord.Member], amount: int):
		amount_1 = amount + 1
		DB().add_amout_command(entity=ctx.command.name)
		if not member:
			number = 0
			async for msg in ctx.channel.history():
				await msg.delete()
				number += 1
				if number >= amount_1:
					emb = discord.Embed(description=f'** :white_check_mark: Удаленно {number - 1} сообщений**', colour=discord.Color.green())
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await ctx.send(embed=emb)
					break

		elif member != None and member in ctx.guild.members:
			number = 0
			def check( message ):
				return message.author == member

			async for msg in ctx.channel.history().filter(check):
				await msg.delete()
				number += 1
				if number >= amount_1:
					emb = discord.Embed(description=f'** :white_check_mark: Удаленно {number} сообщений от пользователя {member.mention}**', colour=discord.Color.green())
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await ctx.send(embed=emb)
					break


	@commands.command(aliases=['temprole'], brief='True', name='temp-role', description='**Дает указаную роль учаснику на время**', usage='temp-role [@Участник] [Id роли] [Длительность]')
	@commands.check(check_role)	
	async def temprole(self, ctx, member: discord.Member, role: discord.Role, type_time: str = None):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете применить эту команду к себе!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if ctx.author.top_role <= role and ctx.author != ctx.guild.owner:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете выдать роль которая выше вашей роли!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if type_time:
			role_time = int(''.join(char for char in type_time if not char.isalpha()))
			role_typetime = str(type_time.replace(str(role_time), ''))
		else:
			role_typetime = None
			role_time = 0

		if role_time > 0:
			emb = discord.Embed(description=f'**`{member}` Была виданно новая роль {role.name} на {role_time}{role_typetime}**', colour=discord.Color.green())
		elif role_time <= 0:
			emb = discord.Embed(title='Ошибка!', description=f'**Укажите на какое время вы выдаете роль!**', colour=discord.Color.green())
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url= self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		minutes = ['m', 'min', 'mins', 'minute', 'minutes', 'м', 'мин', 'минута', 'минуту', 'минуты', 'минут']
		hours = ['h', 'hour', 'hours', 'ч', 'час', 'часа', 'часов']
		days = ['d', 'day', 'days', 'д', 'день', 'дня', 'дней']
		weeks = ['w', 'week', 'weeks', 'н', 'нед', 'неделя', 'недели', 'недель', 'неделю']
		monthes = ['m', 'month', 'monthes', 'mo', 'mos', 'months', 'мес', 'месяц', 'месяца', 'месяцев']
		years = ['y', 'year', 'years', 'г', 'год', 'года', 'лет']
		if role_typetime in minutes: 
			role_minutes = role_time * 60
		elif role_typetime in hours: 
			role_minutes = role_time * 60 * 60
		elif role_typetime in days: 
			role_minutes = role_time * 60 * 60 * 12
		elif role_typetime in weeks: 
			role_minutes = role_time * 60 * 60 * 12 * 7
		elif role_typetime in monthes:
			role_minutes = role_time * 60 * 60 * 12 * 7 * 31
		elif role_typetime in years:
			role_minutes = role_time * 60 * 60 * 12 * 7 * 31 * 12
		else: 
			role_minutes = role_time

		times = time.time()
		times += role_minutes

		await member.add_roles(role)
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		if role_minutes > 0:
			DB().set_punishment(type_punishment='temprole', time=times, member=member, role_id=int(role.id))


	@commands.command(aliases=['slowmode'], brief='True', name='slow-mode', description='**Ставить медленный режим указаному каналу(Если канал не указан медленный режим ставиться всем каналам, 0 - выключает медленный режим, длительность не указывать меньше нуля)**', usage='slow-mode [Время] |Канал|')
	@commands.check(check_role)	
	async def slowmode(self, ctx, delay: int, channel: discord.TextChannel):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if not channel:
			guild_text_channels = ctx.guild.text_channels
			for channel in guild_text_channels:
				await channel.edit(slowmode_delay=delay)

			if delay > 0:
				emb = discord.Embed(description=f'**Для всех каналов этого сервера был поставлен медленний режим на {delay}сек**', colour=discord.Color.green())
			elif delay == 0:
				emb = discord.Embed(description=f'**Для всех каналов этого сервера был снят медленний режим**', colour=discord.Color.green())
			elif delay < 0:
				emb = discord.Embed(description=f'**Вы не правильно указали время, укажите длительность медленого режима больше ноля**', colour=discord.Color.green())

		elif channel:
			slowmode_channel = channel
			await slowmode_channel.edit(slowmode_delay=delay)
			if delay > 0:
				emb = discord.Embed(description=f'**Для канала {slowmode_channel.name} был поставлен медленний режим на {delay}сек**', colour=discord.Color.green())
			elif delay == 0:
				emb = discord.Embed(description=f'**Для канала {slowmode_channel.name} был снят медленний**', colour=discord.Color.green())
			elif delay < 0:
				emb = discord.Embed(description=f'**Вы не правильно указали время, укажыте длительность медленого режима больше ноля**', colour=discord.Color.green())

		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)


	@commands.command(brief='True', description='**Кикает учасника из сервера**', usage='kick [@Участник] |Причина|')
	@commands.check(check_role)	
	async def kick(self, ctx, member: discord.Member, *, reason = None):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете применить эту команду к себе!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете можете кикнуть участника который имеет больше прав чем у вас!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if not reason:
			reason = 'Причина не указана'

		await member.kick(reason=reason)

		emb = discord.Embed(description=f'**{ctx.author.mention} Кикнул `{member}` по причине {reason}**', colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(description=f'**Модератор {ctx.author.mention} кикнул вас из сервера `{ctx.guild.name}` по причине {reason}**', colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass


	@commands.command(aliases=['softban'], brief='True', name='soft-ban', description='**Апаратно банит указаного участника - участник имеет доступ к серверу, но к каналам доступа нет**', usage='soft-ban [@Участник] |Причина|')
	@commands.check(check_role)	
	async def softban(self, ctx, member: discord.Member, type_time: str = None, *, reason = None):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете применить эту команду к себе!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете можете забанить участника который имеет больше прав чем у вас!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if type_time:
			softban_time = int(''.join(char for char in type_time if not char.isalpha()))
			softban_typetime = str(type_time.replace(str(softban_time), ''))
		else:
			softban_typetime = None
			softban_time = 0

		minutes = ['m', 'min', 'mins', 'minute', 'minutes', 'м', 'мин', 'минута', 'минуту', 'минуты', 'минут']
		hours = ['h', 'hour', 'hours', 'ч', 'час', 'часа', 'часов']
		days = ['d', 'day', 'days', 'д', 'день', 'дня', 'дней']
		weeks = ['w', 'week', 'weeks', 'н', 'нед', 'неделя', 'недели', 'недель', 'неделю']
		monthes = ['m', 'month', 'monthes', 'mo', 'mos', 'months', 'мес', 'месяц', 'месяца', 'месяцев']
		years = ['y', 'year', 'years', 'г', 'год', 'года', 'лет']
		if softban_typetime in minutes: 
			softban_minutes = softban_time * 60
		elif softban_typetime in hours: 
			softban_minutes = softban_time * 60 * 60
		elif softban_typetime in days: 
			softban_minutes = softban_time * 60 * 60 * 12
		elif softban_typetime in weeks: 
			softban_minutes = softban_time * 60 * 60 * 12 * 7
		elif softban_typetime in monthes:
			softban_minutes = softban_time * 60 * 60 * 12 * 7 * 31
		elif softban_typetime in years:
			softban_minutes = softban_time * 60 * 60 * 12 * 7 * 31 * 12
		else: 
			softban_minutes = softban_time
		
		times = time.time()
		times += softban_minutes

		if not reason:
			reason = 'Причина не указана'

		emb = discord.Embed(description=f'**{ctx.author.mention} Апаратно забанил `{member}` по причине {reason}**' , colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(description=f'**Вы были апаратно забанены на сервере `{ctx.guild.name}` по причине {reason}**', colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass

		overwrite = discord.PermissionOverwrite(connect=False, view_channel=False, send_messages=False)
		role = get(ctx.guild.roles, name=self.SOFTBAN_ROLE)

		if not role:
			role = await ctx.guild.create_role(name=self.SOFTBAN_ROLE)

		await member.edit(voice_channel=None)
		for channel in ctx.guild.channels:
			await channel.set_permissions(role, overwrite=overwrite)

		await member.add_roles(role)

		if softban_time > 0:
			DB().set_punishment(type_punishment='temprole', time=times, member=member, role=role.id)


	@commands.command(aliases=['unsoftban'], brief='True', name='unsoft-ban', description='**Снимает апаратный с указаного участника**', usage='unsoft-ban [@Участник]')
	@commands.check(check_role)	
	async def unsoftban(self, ctx, member: discord.Member):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете применить эту команду к себе!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		emb = discord.Embed(description=f'**{ctx.author.mention} Разбанил `{member}`**' , colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(description=f'**Вы были разбанены на сервере `{ctx.guild.name}`**', colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass
	
		role = get(ctx.guild.roles, name=self.SOFTBAN_ROLE)
		if not role:
			role = await ctx.guild.create_role(name=self.SOFTBAN_ROLE)

		if role in member.roles:
			await member.remove_roles(role)


	@commands.command(hidden=True, description='**Банит учасника по указаной причине (Перманентно или на время)**', usage='ban [@Участник] |Длительность| |Тип времени| |Причина|')
	@commands.has_permissions(ban_members=True)
	async def ban(self, ctx, member: discord.Member, type_time: str = None, *, reason: str = None):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете применить эту команду к себе!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете можете забанить участника который имеет больше прав чем у вас!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if member in ctx.guild.members:
			DB().sel_user(target = member)
		else:
			emb = discord.Embed(title='Ошибка!', description=f"**На сервере не существует такого пользователя!**", colour=discord.Color.green())
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return

		if type_time:
			ban_time = int(''.join(char for char in type_time if not char.isalpha()))
			ban_typetime = str(type_time.replace(str(ban_time), ''))
		else:
			ban_typetime = None
			ban_time = 0

		minutes = ['m', 'min', 'mins', 'minute', 'minutes', 'м', 'мин', 'минута', 'минуту', 'минуты', 'минут']
		hours = ['h', 'hour', 'hours', 'ч', 'час', 'часа', 'часов']
		days = ['d', 'day', 'days', 'д', 'день', 'дня', 'дней']
		weeks = ['w', 'week', 'weeks', 'н', 'нед', 'неделя', 'недели', 'недель', 'неделю']
		monthes = ['m', 'month', 'monthes', 'mo', 'mos', 'months', 'мес', 'месяц', 'месяца', 'месяцев']
		years = ['y', 'year', 'years', 'г', 'год', 'года', 'лет']
		if ban_typetime in minutes: 
			ban_minutes = ban_time * 60
		elif ban_typetime in hours: 
			ban_minutes = ban_time * 60 * 60
		elif ban_typetime in days: 
			ban_minutes = ban_time * 60 * 60 * 12
		elif ban_typetime in weeks: 
			ban_minutes = ban_time * 60 * 60 * 12 * 7
		elif ban_typetime in monthes:
			ban_minutes = ban_time * 60 * 60 * 12 * 7 * 31
		elif ban_typetime in years:
			ban_minutes = ban_time * 60 * 60 * 12 * 7 * 31 * 12
		else: 
			ban_minutes = ban_time
		
		times = time.time()
		times += ban_minutes

		if not reason:
			reason = 'Причина не указана'

		await member.ban(reason=reason)
		emb = discord.Embed(description=f'**{ctx.author.mention} Забанил `{member}` по причине {reason}**', colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		emb = discord.Embed(description=f'**Вы были забанены на сервере `{ctx.guild.name}` по причине {reason}**', colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		try:
			await member.send(embed=emb)
		except:
			pass

		if ban_time > 0:
			sql = ("""UPDATE users SET clans = %s, items = %s, money = %s, coins = %s, reputation = %s WHERE user_id = %s AND guild_id = %s""")
			val = (json.dumps([]), json.dumps([]), 0, 0, -100, member.id, ctx.guild.id)

			self.cursor.execute(sql, val)
			self.conn.commit()

			DB().set_punishment(type_punishment='ban', time=times, member=member)


	@commands.command(aliases=['unban'], hidden=True, name='un-ban', description='**Снимает бан из указаного учасника**', usage='un-ban [@Участник]')
	@commands.has_permissions(ban_members=True)
	async def unban(self, ctx, *, member: discord.User):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете применить эту команду к себе!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		banned_users = await ctx.guild.bans()
		for ban_entry in banned_users:
			user = ban_entry.user

			if user.id == member.id:
				await ctx.guild.unban(user)
				DB().del_punishment(member=member, guild_id=ctx.guild.id, type_punishment='ban')

				emb = discord.Embed(description=f'**{ctx.author.mention} Разбанил `{member}`**', colour=discord.Color.green())
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)

				emb = discord.Embed(description=f'**Вы были разбанены на сервере `{ctx.guild.name}`**', colour=discord.Color.green())
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				try:
					await member.send(embed=emb)
				except:
					pass
				

	@commands.command(brief='True', description='**Мьютит указаного участника в голосовых каналах**', usage='vmute [@Участник] [Длительность (В минутах)] [Причина]')
	@commands.check(check_role)	
	async def vmute(self, ctx, member: discord.Member, type_time: str = None, reason: str = None):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете применить эту команду к себе!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете можете замьютить участника который имеет больше прав чем у вас!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if not reason:
			reason = 'Причина не указанна'

		if type_time:
			vmute_time = int(''.join(char for char in type_time if not char.isalpha()))
			vmute_typetime = str(type_time.replace(str(vmute_time), ''))
		else:
			vmute_typetime = None
			vmute_time = 0

		minutes = ['m', 'min', 'mins', 'minute', 'minutes', 'м', 'мин', 'минута', 'минуту', 'минуты', 'минут']
		hours = ['h', 'hour', 'hours', 'ч', 'час', 'часа', 'часов']
		days = ['d', 'day', 'days', 'д', 'день', 'дня', 'дней']
		weeks = ['w', 'week', 'weeks', 'н', 'нед', 'неделя', 'недели', 'недель', 'неделю']
		monthes = ['m', 'month', 'monthes', 'mo', 'mos', 'months', 'мес', 'месяц', 'месяца', 'месяцев']
		years = ['y', 'year', 'years', 'г', 'год', 'года', 'лет']
		if vmute_typetime in minutes: 
			vmute_minutes = vmute_time * 60
		elif vmute_typetime in hours: 
			vmute_minutes = vmute_time * 60 * 60
		elif vmute_typetime in days: 
			vmute_minutes = vmute_time * 60 * 60 * 12
		elif vmute_typetime in weeks: 
			vmute_minutes = vmute_time * 60 * 60 * 12 * 7
		elif vmute_typetime in monthes:
			vmute_minutes = vmute_time * 60 * 60 * 12 * 7 * 31
		elif vmute_typetime in years:
			vmute_minutes = vmute_time * 60 * 60 * 12 * 7 * 31 * 12
		else: 
			vmute_minutes = vmute_time

		times = time.time()
		times += vmute_minutes

		vmute_minutes = vmute_time * 60
		overwrite = discord.PermissionOverwrite(connect=False)
		role = get(ctx.guild.roles, name=self.VMUTE_ROLE)

		if not role:
			role = await ctx.guild.create_role(name=self.VMUTE_ROLE)
		for channel in ctx.guild.voice_channels:
			await channel.set_permissions(role, overwrite=overwrite)

		await member.add_roles(role)
		await member.edit(voice_channel=None)

		if vmute_minutes > 0:
			emb = discord.Embed(description=f'**{ctx.author.mention} Замьютил `{member}` в голосовых каналах на {vmute_time}{vmute_typetime} по причине {reason}**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			DB().set_punishment(type_punishment='vmute', time=times, member=member, role_id=int(role.id))

		elif vmute_minutes <= 0:
			emb = discord.Embed(description=f'**{ctx.author.mention} Перманентно замьютил `{member}` в голосовых каналах по причине {reason}**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)


	@commands.command(aliases=['unvmute'], brief='True', name='un-vmute', description='**Снимает мьют с указаного участника в голосовых каналах**', usage='un-vmute [@Участник]')
	@commands.check(check_role)	
	async def unvmute(self, ctx, member: discord.Member):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете применить эту команду к себе!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		for vmute_role in ctx.guild.roles:
			if vmute_role.name == self.VMUTE_ROLE:
				DB().del_punishment(member=member, guild_id=ctx.guild.id, type_punishment='vmute')
				await member.remove_roles(vmute_role)
				overwrite = discord.PermissionOverwrite(connect=None)

				for channel in ctx.guild.voice_channels:
					await channel.set_permissions(vmute_role, overwrite=overwrite)

				emb = discord.Embed(description=f'**{ctx.author.mention} Размьютил `{member}` в голосовых каналах**', colour=discord.Color.green())
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)

				emb = discord.Embed(description=f'**Вы были размьючены в голосовых каналах**', colour=discord.Color.green())
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				try:
					await member.send(embed=emb)
				except:
					pass
				return


	@commands.command(brief='True', description='**Мютит учасника по указаной причине (На выбор, можно без причины)**', usage='mute [@Участник] |Длительность| |Тип времени| |Причина|')
	@commands.check(check_role)	
	async def mute(self, ctx, member: discord.Member, type_time: str = None, *, reason = None ):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете применить эту команду к себе!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете можете замьютить участника который имеет больше прав чем у вас!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if type_time:
			mute_time = int(''.join(char for char in type_time if not char.isalpha()))
			mute_typetime = str(type_time.replace(str(mute_time), ''))
		else:
			mute_typetime = None
			mute_time = 0

		minutes = ['m', 'min', 'mins', 'minute', 'minutes', 'м', 'мин', 'минута', 'минуту', 'минуты', 'минут']
		hours = ['h', 'hour', 'hours', 'ч', 'час', 'часа', 'часов']
		days = ['d', 'day', 'days', 'д', 'день', 'дня', 'дней']
		weeks = ['w', 'week', 'weeks', 'н', 'нед', 'неделя', 'недели', 'недель', 'неделю']
		monthes = ['m', 'month', 'monthes', 'mo', 'mos', 'months', 'мес', 'месяц', 'месяца', 'месяцев']
		years = ['y', 'year', 'years', 'г', 'год', 'года', 'лет']
		if mute_typetime in minutes: 
			mute_minutes = mute_time * 60
		elif mute_typetime in hours: 
			mute_minutes = mute_time * 60 * 60
		elif mute_typetime in days: 
			mute_minutes = mute_time * 60 * 60 * 12
		elif mute_typetime in weeks: 
			mute_minutes = mute_time * 60 * 60 * 12 * 7
		elif mute_typetime in monthes:
			mute_minutes = mute_time * 60 * 60 * 12 * 7 * 31
		elif mute_typetime in years:
			mute_minutes = mute_time * 60 * 60 * 12 * 7 * 31 * 12
		else: 
			mute_minutes = mute_time

		times = time.time()
		times += mute_minutes

		if not reason:
			reason = 'Причина не указана'

		if member in ctx.guild.members:
			data = DB().sel_user(target = member)
		else:
			emb = discord.Embed(title='Ошибка!', description=f"**На сервере не существует такого пользователя!**", colour=discord.Color.green())
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		role = get(ctx.guild.roles, name=self.MUTE_ROLE)
		if not role:
			role = await ctx.guild.create_role(name=self.MUTE_ROLE)

		if role in member.roles:
			emb = discord.Embed(title='Ошибка!', description=f'**Указаный пользователь уже замьючен!**' , colour=discord.Color.green())
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return			
		
		overwrite = discord.PermissionOverwrite(send_messages=False)
		await member.add_roles(role)
		for channel in ctx.guild.text_channels:
			await channel.set_permissions(role, overwrite=overwrite)

		cur_lvl = data['lvl']
		cur_coins = data['coins'] - 1500
		cur_money = data['money']
		cur_reputation = data['reputation'] - 15
		cur_items = data['items']
		prison = data['prison']

		if cur_reputation < -100:
			cur_reputation = -100

		if cur_lvl <= 3:
			cur_money -= 250
		elif cur_lvl > 3 and cur_lvl <= 5:
			cur_money -= 500
		elif cur_lvl > 5:
			cur_money -= 1000

		if cur_coins <= 0:
			cur_coins = 0

		if cur_money <= -5000:
			prison = True
			cur_items = []
			emb = discord.Embed(description=f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Текущий баланс - `{cur_money}`**', colour=discord.Color.green())
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			try:
				await member.send(embed=emb)
			except:
				pass

		sql = ("""UPDATE users SET money = %s, coins = %s, reputation = %s, items = %s, prison = %s WHERE user_id = %s AND guild_id = %s""")
		val = (cur_money, cur_coins, cur_reputation, json.dumps(cur_items), str(prison), member.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		if mute_minutes <= 0:
			emb = discord.Embed(description=f'**{ctx.author.mention} Перманентно замутил `{member}` по причине {reason}**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			emb = discord.Embed(description=f'**Вы были перманентно замьючены модератором `{member}` по причине {reason}**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			try:
				await member.send(embed=emb)
			except:
				pass
		elif mute_minutes > 0:
			DB().set_punishment(type_punishment='mute', time=times, member=member, role_id=int(role.id), reason=reason, author=str(ctx.author))
			emb = discord.Embed(description=f'**{ctx.author.mention} Замутил `{member}` по причине {reason} на {mute_time}{mute_typetime}**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

			emb = discord.Embed(description=f'**Вы были замьючены модератором `{member}` по причине {reason} на {mute_time}{mute_typetime}**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			try:
				await member.send(embed=emb)
			except:
				pass


	@commands.command(aliases=['unmute'], brief='True', name='un-mute', description='**Размютит указаного учасника**', usage='un-mute [@Участник]')
	@commands.check(check_role)	
	async def unmute(self, ctx, member: discord.Member):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете применить эту команду к себе!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		for role in ctx.guild.roles:
			if role.name == self.MUTE_ROLE:
				DB().del_punishment(member=member, guild_id=ctx.guild.id, type_punishment='mute')
				await member.remove_roles(role)

				emb = discord.Embed(description=f'**{ctx.author.mention} Размьютил `{member}`**', colour=discord.Color.green())
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)			
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)

				emb = discord.Embed(description=f'**Вы были размьючены на сервере `{ctx.guild.name}`**', colour=discord.Color.green())
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				try:
					await member.send(embed=emb)
				except:
					pass


	@commands.command(aliases=['clearwarns'], brief='True', name='clear-warns', description='**Очищает предупреждения в указаного пользователя**', usage='clear-warns [@Участник]')
	@commands.check(check_role)	
	async def clearwarn(self, ctx, member: discord.Member):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете применить эту команду к себе!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if member in ctx.guild.members:
			DB().sel_user(target=member)
		else:
			emb = discord.Embed(title='Ошибка!', description=f"**На сервере не существует такого пользователя!**", colour=discord.Color.green())
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		sql = ("""UPDATE users SET warns = %s WHERE user_id = %s AND guild_id = %s""")
		val = (json.dumps([]), member.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		emb = discord.Embed(description=f'**У пользователя `{member}` были сняты предупреждения**', colour=discord.Color.green())
		emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)


	@commands.command(brief='True', description='**Дает придупреждения учаснику по указаной причине**', usage='warn [@Участник] |Причина|')
	@commands.check(check_role)
	async def warn(self, ctx, member: discord.Member, *, reason = None):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете применить эту команду к себе!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
			emb = discord.Embed(title='Ошибка!', description='Вы не можете можете дать предупреждения участнику который имеет больше прав чем у вас!', colour=discord.Color.green()) 
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if member.bot:			
			emb = discord.Embed(title='Ошибка!', description=f"**Вы не можете дать предупреждения боту!**", colour=discord.Color.green())
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb )
			await ctx.message.add_reaction('❌')
			return

		if not reason:
			reason = 'Причина не указана'

		if member in ctx.guild.members:
			data = DB().sel_user(target=member)
		else:
			emb = discord.Embed(title='Ошибка!', description=f"**На сервере не существует такого пользователя!**", colour=discord.Color.green())
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		info = DB().sel_guild(guild=ctx.guild)
		max_warns = int(info['max_warns'])

		cur_lvl = data['lvl']
		cur_coins = data['coins']
		cur_money = data['money']
		cur_warns = data['warns']
		cur_state_pr = data['prison']
		cur_reputation = data['reputation'] - 10

		warn_id = DB().set_warn(target=member, reason=reason, author=str(ctx.author), time=str(datetime.today()))

		if cur_lvl <= 3:
			cur_money -= 250
		elif cur_lvl > 3 and cur_lvl <= 5:
			cur_money -= 500
		elif cur_lvl > 5:
			cur_money -= 1000

		if cur_money <= -5000:
			cur_state_pr = True
			emb = discord.Embed(description=f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Текущий баланс - {cur_money}**' , colour = discord.Color.green() )
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			try:
				await member.send(embed=emb)
			except:
				pass

		if cur_reputation < -100:
			cur_reputation = -100

		if len(cur_warns) >= 20:
			DB().del_warn([warn for warn in cur_warns if not warn['state']][0]['id'])

		if len([warn for warn in cur_warns if warn['state']]) >= max_warns:
			cur_coins -= 1000
			cur_warns = []

			if cur_reputation < -100:
				cur_reputation = -100

			if cur_coins < 0:
				cur_coins = 0

			await Commands(self.client).main_mute(ctx=ctx.message, member=member, reason=reason, check_role=False, mute_typetime='h', mute_time=2)
			emb = discord.Embed(description=f'**`{member}` Достиг максимального значения предупреждения и был замючен на 2 часа.**', colour=discord.Color.green())
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return
		else:
			emb = discord.Embed(description=f'**Вы были предупреждены {ctx.author.mention} по причине {reason}. Количество предупрежденний - `{len(cur_warns)+1}`, id - `{warn_id}`**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			try:
				await member.send(embed=emb)
			except:
				pass

			emb = discord.Embed(description=f'**Пользователь `{member}` получил предупреждения по причине {reason}. Количество предупрежденний - `{len(cur_warns)+1}`, id - `{warn_id}`**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)

		sql = ("""UPDATE users SET money = %s, coins = %s, reputation = %s, prison = %s WHERE user_id = %s AND guild_id = %s""")
		val = (cur_money, cur_coins, cur_reputation, str(cur_state_pr), member.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()


	@commands.command(aliases=['remwarn', 'rem-warn'], brief='True', name='remove-warn', description='**Снимает указаное предупреждения в участика**', usage='remove-warn [@Участник] [Id предупреждения]')
	@commands.check(check_role)	
	async def rem_warn(self, ctx, warn_id: int):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)
		data = DB().del_warn(ctx.guild.id, warn_id)

		if not data:
			emb = discord.Embed(title='Ошибка!', description='**Предупреждения с таким айди не существует! Укажите правильный айди предупреждения**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			return
		elif data:
			emb = discord.Embed(description=f'**Предупреждения успешно было снято с участника `{ctx.guild.get_member(data[0])}`**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)


	@commands.command(description='**Показывает список предупреждений**', usage='warns |@Участник|')
	async def warns(self, ctx, member: discord.Member = None):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)

		if member.bot:			
			emb = discord.Embed(title='Ошибка!', description=f"**Вы не можете просмотреть предупреждения бота!**", colour=discord.Color.green())
			emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb )
			await ctx.message.add_reaction('❌')
			return

		if not member:
			member = ctx.author

		data = DB().sel_user(target=member)
		warns = data['warns']

		if warns == []:
			emb = discord.Embed(title=f'Предупреждения пользователя - `{member}`', description='Список предупреждений пуст.', colour=discord.Color.green())
		else:
			emb = discord.Embed(title=f'Предупреждения пользователя - `{member}`', colour=discord.Color.green() )

		for warn in warns:
			id_warn = warn['id']
			time_warn = warn['time']
			author_warn = warn['author']
			reason = warn['reason']
			state = warn['state']

			if state:
				emb.add_field(value=f'**Причина:** {reason}', name=f'Id - {id_warn}, время - {time_warn}, автор - {author_warn}', inline=False)
			elif not state:
				emb.add_field(value=f'~~**Причина:** {reason}~~', name=f'Не активный - |Id - {id_warn}, время - {time_warn}, автор - {author_warn}|', inline=False)

		emb.set_author(name=member.name, icon_url=member.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

def setup( client ):
	client.add_cog(Moderate(client))