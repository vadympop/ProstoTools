import discord
import json
import asyncio
import typing
import datetime
import time
import random
import os
import mysql.connector
from Tools.database import DB
from random import randint
from datetime import datetime
from discord.ext import commands
from discord.utils import get
from discord.voice_client import VoiceClient
from discord.ext.commands import Bot
from configs import configs


def check_role(ctx):
	data = DB().sel_guild(guild = ctx.guild)['moder_roles']
	roles = ctx.guild.roles
	roles.reverse()
	data.append(roles[0].id)

	if data != []:
		for role in data:
			role = get(ctx.guild.roles, id = role)
			yield role in ctx.author.roles
	else:
		return ctx.author.guild_permission.administrator


def clear_commands( guild ):
	data = DB().sel_guild(guild = guild)
	purge = data['purge']
	return purge


global Footer, Mute_role, Vmute_role
Mute_role = configs['MUTE_ROLE']
Vmute_role = configs['VMUTE_ROLE']
SOFTban_role = configs['SOFTBAN_ROLE']
Footer = configs['FOOTER_TEXT']


class Moderate(commands.Cog, name = 'Moderate'):

	def __init__(self, client):
		self.client = client
		self.conn = mysql.connector.connect(user = 'root', password = os.environ['DB_PASSWORD'], host = 'localhost', database = 'data')
		self.cursor = self.conn.cursor(buffered = True)


	@commands.command(brief = 'True', description = '**Удаляет указаное число сообщений**', usage = 'clear |@Участник| [Число удаляемых сообщений]')
	@commands.check(check_role)	
	async def clear( self, ctx, member: typing.Optional[discord.Member], amount: int ):
		client = self.client
		amount_1 = amount + 1
		DB().add_amout_command(entity=ctx.command.name)
		if not member:
			number = 0

			async for msg in ctx.channel.history():
				await msg.delete()
				number += 1

				if number >= amount_1:
					emb = discord.Embed( description = f'** :white_check_mark: Удаленно {number - 1} сообщений**', colour = discord.Color.green() )
					
					emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
					emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
					
					await ctx.send( embed = emb )
					break


		elif member != None and member in ctx.guild.members:
			number = 0

			def check( message ):
				return message.author == member

			async for msg in ctx.channel.history().filter(check):
				await msg.delete()
				number += 1

				if number >= amount_1:

					emb = discord.Embed( description = f'** :white_check_mark: Удаленно {number} сообщений от пользователя {member.mention}**', colour = discord.Color.green() )
			
					emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
					emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
					
					await ctx.send( embed = emb )
					break


	@commands.command(aliases=['temprole'], brief = 'True', name = 'temp-role', description = '**Дает указаную роль учаснику на время**', usage = 'temp-role [@Участник] [Id роли] [Длительность]')
	@commands.check(check_role)	
	async def temprole( self, ctx, member: discord.Member, role: discord.Role, role_time: int = 0, role_typetime: str = None ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed(title = 'Ошибка!', description = 'Вы не можете применить эту команду к себе!', colour = discord.Color.green()) 
			
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send(embed = emb)
			return

		if ctx.author.top_role <= role and ctx.author != ctx.guild.id:
			emb = discord.Embed(title = 'Ошибка!', description = 'Вы не можете выдать роль которая выше вашей роли!', colour = discord.Color.green()) 
			
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send(embed = emb)
			return

		if role_time > 0:
			emb = discord.Embed( description = f'**`{member}` Была виданно новая роль {role.name} на {role_time}мин**', colour = discord.Color.green() )
		elif role_time <= 0:
			emb = discord.Embed( title = 'Ошибка!', description = f'**Укажите на какое время вы выдаете роль!**', colour = discord.Color.green() )
			
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send(embed = emb)
			return

		if role_typetime == 'мин' or role_typetime == 'м' or role_typetime == 'm' or role_typetime == "min":
			role_minutes = role_time * 60
		elif role_typetime == 'час'  or role_typetime == 'ч' or role_typetime == 'h' or role_typetime == "hour":
			role_minutes = role_time * 60
		elif role_typetime == 'дней' or role_typetime == 'д' or role_typetime == 'd' or role_typetime == "day":
			role_minutes = role_time * 120 * 12
		elif role_typetime == 'недель' or role_typetime == "н" or role_typetime == 'week' or role_typetime == "w":
			role_minutes = role_time * 120 * 12 * 7			
		elif role_typetime == 'месяц' or role_typetime == "м" or role_typetime == 'mounth' or role_typetime == "m":
			role_minutes = role_time * 120 * 12 * 30
		else:
			role_minutes = role_time * 60			

		await member.add_roles( role )

		emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
		emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

		await ctx.send( embed = emb )

		if role_minutes > 0:
			await asyncio.sleep( role_minutes )
			await member.remove_roles( role )


	@commands.command(aliases=['slowmode'], brief = 'True', name = 'slow-mode', description = '**Ставить медленний режим указаному каналу(Если канал не указан медленный режим ставиться всем каналам, 0 - выключает медленный режим, длительность не указывать меньше нуля)**', usage = 'slow-mode [Время] |Id канала|')
	@commands.check(check_role)	
	async def slowmode( self, ctx, delay: int, channel: typing.Optional[ int ] ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if not channel:

			guild_text_channels = ctx.guild.text_channels
			for channel in guild_text_channels:
				await channel.edit( slowmode_delay = delay )

			if delay > 0:
				emb = discord.Embed( description = f'**Для всех каналов этого сервера был поставлен медленний режим на {delay}сек**', colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )

			elif delay == 0:
				emb = discord.Embed( description = f'**Для всех каналов этого сервера был снят медленний режим**', colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )

			elif delay < 0:
				emb = discord.Embed( description = f'**Вы не правильно указали время, укажыте длительность медленого режима больше ноля**', colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )


		elif channel:
			slowmode_channel = client.get_channel(channel)
			await slowmode_channel.edit( slowmode_delay = delay )

			if delay > 0:

				emb = discord.Embed( description = f'**Для канала {slowmode_channel.name} был поставлен медленний режим на {delay}сек**', colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )

			elif delay == 0:

				emb = discord.Embed( description = f'**Для канала {slowmode_channel.name} был снят медленний**', colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )

			elif delay < 0:

				emb = discord.Embed( description = f'**Вы не правильно указали время, укажыте длительность медленого режима больше ноля**', colour = discord.Color.green() )

				emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

				await ctx.send( embed = emb )


	@commands.command(brief = 'True', description = '**Кикает учасника из сервера**', usage = 'kick [@Участник] |Причина|')
	@commands.check(check_role)	
	async def kick( self, ctx, member: discord.Member, *, reason = None ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed(title = 'Ошибка!', description = 'Вы не можете применить эту команду к себе!', colour = discord.Color.green()) 
			
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send(embed = emb)
			return

		guild = ctx.guild
		if not reason:
			reason = 'Нарушения правил сервера'

		await member.kick( reason = reason )

		emb = discord.Embed( description = f'**{ctx.author.mention} Кикнул `{member}` по причине {reason}**' , colour = discord.Color.green() )
		emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
		emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			
		await ctx.send( embed = emb )

		emb = discord.Embed( description = f'**Модератор {ctx.author.mention} кикнул вас из сервера `{guild.name}` по причине {reason}**' , colour = discord.Color.green() )
		emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
		emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			
		await member.send( embed = emb )


	@commands.command(aliases=['softban'], brief = 'True', name = 'soft-ban', description = '**Апаратно банит указаного участника - участник имеет доступ к серверу, но к каналам доступа нет**', usage = 'soft-ban [@Участник] |Причина|')
	@commands.check(check_role)	
	async def softban(self, ctx, member: discord.Member, *, reason = None):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed(title = 'Ошибка!', description = 'Вы не можете применить эту команду к себе!', colour = discord.Color.green()) 
			
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send(embed = emb)
			return

		if not reason:
			emb = discord.Embed( description = f'**{ctx.author.mention} Апаратно забанил `{member}`**' , colour = discord.Color.green() )
			
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send( embed = emb )

			emb = discord.Embed( description = f'**Вы были апаратно забанены на сервере `{ctx.guild.name}`**', colour = discord.Color.green() )

			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await member.send( embed = emb )
		elif reason:
			emb = discord.Embed( description = f'**{ctx.author.mention} Апаратно забанил `{member}` по причине {reason}**' , colour = discord.Color.green() )
			
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send( embed = emb )

			emb = discord.Embed( description = f'**Вы были апаратно забанены на сервере `{ctx.guild.name}` по причине {reason}**', colour = discord.Color.green() )

			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await member.send( embed = emb )


		overwrite = discord.PermissionOverwrite( connect = False, view_channel = False, send_messages = False )
		role = get( ctx.guild.roles, name = SOFTban_role )

		if not role:
			role = await ctx.guild.create_role( name = SOFTban_role )

		await member.edit( voice_channel = None )
		for channel in ctx.guild.channels:
			await channel.set_permissions( role, overwrite = overwrite )

		await member.add_roles( role )


	@commands.command(aliases=['unsoftban'], brief = 'True', name = 'unsoft-ban', description = '**Снимает апаратный с указаного участника**', usage = 'unsoft-ban [@Участник]')
	@commands.check(check_role)	
	async def unsoftban(self, ctx, member: discord.Member):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed(title = 'Ошибка!', description = 'Вы не можете применить эту команду к себе!', colour = discord.Color.green()) 
			
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send(embed = emb)
			return

		emb = discord.Embed( description = f'**{ctx.author.mention} Разбанил `{member}`**' , colour = discord.Color.green() )
		
		emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
		emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
		
		await ctx.send( embed = emb )

		emb = discord.Embed( description = f'**Вы были разбанены на сервере `{ctx.guild.name}`**', colour = discord.Color.green() )

		emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
		emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

		await member.send( embed = emb )
	
		role = get( ctx.guild.roles, name = SOFTban_role )
		if not role:
			role = await ctx.guild.create_role( name = SOFTban_role )

		if role in member.roles:
			await member.remove_roles( role )


	@commands.command(hidden = True, description = '**Банит учасника по указаной причине (Перманентно или на время)**', usage = 'ban [@Участник] |Длительность| |Тип времени| |Причина|')
	@commands.has_permissions( ban_members = True )
	async def ban( self, ctx, member: discord.Member, ban_time: typing.Optional[int] = 0, ban_typetime: typing.Optional[str] = None, *, reason: typing.Optional[str] = None ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed(title = 'Ошибка!', description = 'Вы не можете применить эту команду к себе!', colour = discord.Color.green()) 
			
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send(embed = emb)
			return

		if member in ctx.guild.members:
			DB().sel_user(target = member)
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f"**На сервере не существует такого пользователя!**", colour = discord.Color.green() )

			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send( embed = emb )
			return

		types = ['мин', 'м', 'm', 'min', 'час', 'ч', 'h', 'hour', 'дней', 'д', 'd', 'day', 'недель', 'н', 'week', 'w', 'месяц', 'м', 'mounth', 'm']

		if ban_typetime == 'мин' or ban_typetime == 'м' or ban_typetime == 'm' or ban_typetime == "min":
			ban_minutes = ban_time * 60
		elif ban_typetime == 'час'  or ban_typetime == 'ч' or ban_typetime == 'h' or ban_typetime == "hour":
			ban_minutes = ban_time * 60
		elif ban_typetime == 'дней' or ban_typetime == 'д' or ban_typetime == 'd' or ban_typetime == "day":
			ban_minutes = ban_time * 120 * 12
		elif ban_typetime == 'недель' or ban_typetime == "н" or ban_typetime == 'week' or ban_typetime == "w":
			ban_minutes = ban_time * 120 * 12 * 7			
		elif ban_typetime == 'месяц' or ban_typetime == "м" or ban_typetime == 'mounth' or ban_typetime == "m":
			ban_minutes = ban_time * 120 * 12 * 30

		if not reason and ban_typetime not in types:
			reason = ban_typetime

		await member.ban( reason = reason )
		if not reason:
			emb = discord.Embed( description = f'**{ctx.author.mention} Забанил `{member}`**' , colour = discord.Color.green() )
			
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send( embed = emb )

			emb = discord.Embed( description = f'**Вы были забанены на сервере `{ctx.guild.name}`**', colour = discord.Color.green() )

			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await member.send( embed = emb )
		elif reason:
			emb = discord.Embed( description = f'**{ctx.author.mention} Забанил `{member}` по причине {reason}**' , colour = discord.Color.green() )
			
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send( embed = emb )

			emb = discord.Embed( description = f'**Вы были забанены на сервере `{ctx.guild.name}` по причине {reason}**', colour = discord.Color.green() )

			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await member.send( embed = emb )

			if ban_time > 0:

				sql = ("""UPDATE users SET clans = %s, items = %s, money = %s, coins = %s, reputation = %s WHERE user_id = %s AND guild_id = %s""")
				val = (json.dumps([]), json.dumps([]), 0, 0, -100)

				self.cursor.execute(sql, val)
				self.conn.commit()

				await asyncio.sleep( ban_minutes )
				await ctx.guild.unban( member )


	@commands.command(aliases=['unban'], hidden = True, name = 'un-ban', description = '**Снимает бан из указаного учасника**', usage = 'un-ban [@Участник]')
	@commands.has_permissions( ban_members = True )
	async def unban( self, ctx, *, member: discord.User):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed(title = 'Ошибка!', description = 'Вы не можете применить эту команду к себе!', colour = discord.Color.green()) 
			
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send(embed = emb)
			return

		banned_users = await ctx.guild.bans()

		for ban_entry in banned_users:
			user = ban_entry.user

			if (user.name, user.discriminator, user.id) == (member.name, member.discriminator, member.id):
				await ctx.guild.unban(user)

				emb = discord.Embed( description = f'**{ctx.author.mention} Разбанил `{member}`**' , colour = discord.Color.green() )
				emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
				await ctx.send( embed = emb )

				emb = discord.Embed( description = f'**Вы были разбанены на сервере `{ctx.guild.name}`**', colour = discord.Color.green() )
				emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
				await member.send( embed = emb )
				

	@commands.command(brief = 'True', description = '**Мьютит указаного участника в голосовых каналах**', usage = 'vmute [@Участник] [Длительность (В минутах)]')
	@commands.check(check_role)	
	async def vmute( self, ctx, member: discord.Member, vmute_time: int = 0 ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed(title = 'Ошибка!', description = 'Вы не можете применить эту команду к себе!', colour = discord.Color.green()) 
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send(embed = emb)
			return

		guild = ctx.guild
		vmute_minutes = vmute_time * 60
		overwrite = discord.PermissionOverwrite( connect = False )
		role = get( ctx.guild.roles, name = Vmute_role )

		if not role:
			role = await guild.create_role( name = Vmute_role )
		for channel in guild.voice_channels:
			await channel.set_permissions( role, overwrite = overwrite )

		await member.add_roles( role )
		await member.edit( voice_channel = None )

		if vmute_minutes > 0:
			emb = discord.Embed( description = f'**{ctx.author.mention} Замутил `{member}` в голосовых каналах на {vmute_time}мин**' , colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )
			await asyncio.sleep(vmute_minutes)
			await member.remove_roles( role )

			overwrite = discord.PermissionOverwrite( connect = None )
			for channel in guild.voice_channels:
				await channel.set_permissions( role, overwrite = overwrite )

		elif vmute_minutes <= 0:
			emb = discord.Embed( description = f'**{ctx.author.mention} Перманентно замутил `{member}` в голосовых каналах**' , colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )


	@commands.command(aliases=['unvmute'], brief = 'True', name = 'un-vmute', description = '**Снимает мьют с указаного участника в голосовых каналах**', usage = 'un-vmute [@Участник]')
	@commands.check(check_role)	
	async def unvmute( self, ctx, member: discord.Member):
		client = self.client
		guild = ctx.guild
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed(title = 'Ошибка!', description = 'Вы не можете применить эту команду к себе!', colour = discord.Color.green()) 
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send(embed = emb)
			return

		for vmute_role in guild.roles:
			if vmute_role.name == Vmute_role:
				await member.remove_roles( vmute_role )
				overwrite = discord.PermissionOverwrite( connect = None )

				for channel in guild.voice_channels:
					await channel.set_permissions( vmute_role, overwrite = overwrite )

				emb = discord.Embed( description = f'**{ctx.author.mention} Размутил `{member}` в голосовых каналах**' , colour = discord.Color.green() )
				emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
				await ctx.send( embed = emb )
				return


	@commands.command(brief = 'True', description = '**Мютит учасника по указаной причине (На выбор, можно без причины)**', usage = 'mute [@Участник] |Длительность| |Тип времени| |Причина|')
	@commands.check(check_role)	
	async def mute( self, ctx, member: discord.Member, type_time: str = None, *, reason = None ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed(title = 'Ошибка!', description = 'Вы не можете применить эту команду к себе!', colour = discord.Color.green()) 
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send(embed = emb)
			return

		guild = ctx.guild
		mute_typetime = type_time[-1:]
		mute_time = int(type_time[:-1])
		overwrite = discord.PermissionOverwrite( send_messages = False )
		types = ['мин', 'м', 'm', 'min', 'час', 'ч', 'h', 'hour', 'дней', 'д', 'd', 'day', 'недель', 'н', 'week', 'w', 'месяц', 'м', 'mounth', 'm']

		if mute_typetime == 'мин' or mute_typetime == 'м' or mute_typetime == 'm' or mute_typetime == "min":
			mute_minutes = mute_time * 60
		elif mute_typetime == 'час'  or mute_typetime == 'ч' or mute_typetime == 'h' or mute_typetime == "hour":
			mute_minutes = mute_time * 60
		elif mute_typetime == 'дней' or mute_typetime == 'д' or mute_typetime == 'd' or mute_typetime == "day":
			mute_minutes = mute_time * 120 * 12
		elif mute_typetime == 'недель' or mute_typetime == "н" or mute_typetime == 'week' or mute_typetime == "w":
			mute_minutes = mute_time * 120 * 12 * 7			
		elif mute_typetime == 'месяц' or mute_typetime == "м" or mute_typetime == 'mounth' or mute_typetime == "m":
			mute_minutes = mute_time * 120 * 12 * 30
		else:
			mute_minutes = mute_time * 60

		times = time.time()
		times += mute_minutes

		if not reason and mute_typetime not in types:
			reason = mute_typetime

		if member in ctx.guild.members:
			data = DB().sel_user(target = member)
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f"**На сервере не существует такого пользователя!**", colour = discord.Color.green() )
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return

		role = get( ctx.guild.roles, name = Mute_role )
		if not role:
			role = await guild.create_role( name = Mute_role )

		if role in member.roles:
			emb = discord.Embed( title = 'Ошибка!', description = f'**Указаный пользователь уже замьючен!**' , colour = discord.Color.green() )
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await member.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return			
		
		await member.add_roles( role )
		for channel in ctx.guild.text_channels:
			await channel.set_permissions( role, overwrite = overwrite )

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

		if cur_money <= -5000:
			prison = True
			cur_items = []
			emb = discord.Embed( description = f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Текущий баланс - `{cur_money}`**' , colour = discord.Color.green() )
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await member.send( embed = emb )

		sql = ("""UPDATE users SET money = %s, coins = %s, reputation = %s, items = %s, prison = %s WHERE user_id = %s AND guild_id = %s""")
		val = (cur_money, cur_coins, cur_reputation, json.dumps(cur_items), str(prison), member.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		if mute_minutes <= 0:
			if reason != None:
				emb = discord.Embed( description = f'**{ctx.author.mention} Перманентно замутил `{member}` по причине {reason}**' , colour = discord.Color.green() )
				emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
				await ctx.send( embed = emb )
			elif reason == None:
				emb = discord.Embed( description = f'**{ctx.author.mention} Перманентно замутил `{member}`**' , colour = discord.Color.green() )
				emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
				await ctx.send( embed = emb )
		elif mute_minutes != 0:
			if reason != None:
				emb = discord.Embed( description = f'**{ctx.author.mention} Замутил `{member}` по причине {reason} на {mute_time}{mute_typetime}**' , colour = discord.Color.green() )
				emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
				await ctx.send( embed = emb )
			elif reason == None:
				emb = discord.Embed( description = f'**{ctx.author.mention} Замутил `{member}` на {mute_time}{mute_typetime}**' , colour = discord.Color.green() )
				emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
				await ctx.send( embed = emb )
		
		if mute_minutes > 0:
			DB().set_punishment(type_punishment='mute', time=times, member=member, role_id=int(role.id))


	@commands.command(aliases=['unmute'], brief = 'True', name = 'un-mute', description = '**Размютит указаного учасника**', usage = 'un-mute [@Участник]')
	@commands.check(check_role)	
	async def unmute( self, ctx, member: discord.Member ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed(title = 'Ошибка!', description = 'Вы не можете применить эту команду к себе!', colour = discord.Color.green()) 
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send(embed = emb)
			return

		guild = ctx.guild
		for role in guild.roles:
			if role.name == Mute_role:
				DB().del_punishment(member=member, guild_id=guild.id, type_punishment='mute')
				await member.remove_roles(role)

				emb = discord.Embed( description = f'**{ctx.author.mention} Размутил `{member}`**' , colour = discord.Color.green() )
				emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )			
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
				await ctx.send( embed = emb )

				emb = discord.Embed( description = f'**Вы были размьючены на сервере `{ctx.guild.name}`**', colour = discord.Color.green() )
				emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
				emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
				await member.send( embed = emb )	


	@commands.command(aliases=['clearwarns'], brief = 'True', name = 'clear-warns', description = '**Очищает предупреждения в указаного пользователя**', usage = 'clear-warns [@Участник]')
	@commands.check(check_role)	
	async def clearwarn( self, ctx, member: discord.Member ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member in ctx.guild.members:
			DB().sel_user(target = member)
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f"**На сервере не существует такого пользователя!**", colour = discord.Color.green() )
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return

		sql = ("""UPDATE users SET warns = %s WHERE user_id = %s AND guild_id = %s""")
		val = (json.dumps([]), member.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()

		emb = discord.Embed( description = f'**У пользователя `{member}` были сняты предупреждения**', colour = discord.Color.green() )
		emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
		emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
		await ctx.send( embed = emb )


	@commands.command(brief = 'True', description = '**Дает придупреждения учаснику по указаной причине**', usage = 'warn [@Участник] |Причина|')
	@commands.check(check_role)	
	async def warn( self, ctx, member: discord.Member, *, reason = None ):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if member == ctx.author:
			emb = discord.Embed(title = 'Ошибка!', description = 'Вы не можете применить эту команду к себе!', colour = discord.Color.green()) 
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send(embed = emb)
			return

		if not reason:
			reason = 'Нарушения правил сервера'

		if member == ctx.author:
			emb = discord.Embed( title = 'Ей! Ты точно подумал прежде чем предупреждать себя?', colour = discord.Color.green() )
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )
			return

		if member in ctx.guild.members:
			data = DB().sel_user(target = member)
		else:
			emb = discord.Embed( title = 'Ошибка!', description = f"**На сервере не существует такого пользователя!**", colour = discord.Color.green() )
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )
			await ctx.message.add_reaction('❌')
			return

		info = DB().sel_guild(guild = ctx.guild)
		max_warns = int(info['max_warns'])

		cur_lvl = data['lvl']
		cur_coins = data['coins']
		cur_money = data['money']
		cur_warns = data['warns']
		cur_state_pr = data['prison']
		cur_reputation = data['reputation'] - 10

		num = ''
		stop = 0
		while stop <= 7:
			num = num + str(randint(1, 9))
			stop += 1

		if cur_warns == []:
			num_warns = 1
		else:
			num_warns = len(cur_warns) + 1

		warn_data = {
			'num_warn': num_warns,
			'author': ctx.author.name,
			'id': int(num),
			'time': str(datetime.today()),
			'reason': reason
		}
		cur_warns.append(warn_data)

		if cur_lvl <= 3:
			cur_money -= 250
		elif cur_lvl > 3 and cur_lvl <= 5:
			cur_money -= 500
		elif cur_lvl > 5:
			cur_money -= 1000

		if cur_money <= -5000:
			cur_state_pr = True
			emb = discord.Embed( description = f'**Вы достигли максимального борга и вы сели в тюрму. Что бы выбраться с тюрмы надо выплатить борг, в тюрме можно работать уборщиком. Текущий баланс - {cur_money}**' , colour = discord.Color.green() )
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await member.send( embed = emb )

		if cur_reputation < -100:
			cur_reputation = -100

		if len(cur_warns) >= max_warns:

			cur_coins -= 1000
			cur_warns = []

			if cur_reputation < -100:
				cur_reputation = -100

			if cur_coins < 0:
				cur_coins = 0

			overwrite = discord.PermissionOverwrite( send_messages = False )
			role = get( ctx.guild.roles, name = Mute_role )

			if not role:
				role = await ctx.guild.create_role( name = Mute_role )

			await member.add_roles( role )
			for channel in ctx.guild.text_channels:
				await channel.set_permissions( role, overwrite = overwrite )

			emb = discord.Embed( description = f'**`{member}` Достиг максимального значения предупреждения и был замючен на 2 часа.**' , colour = discord.Color.green() )
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )

			await asyncio.sleep(120 * 60)
			await member.remove_roles( role )
			return
		else:
			emb = discord.Embed( description = f'**Вы были предупреждены {ctx.author.mention} по причине {reason}. Количество предупрежденний - `{len(cur_warns)}`, id - `{num}`**' , colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await member.send( embed = emb )

			emb = discord.Embed( description = f'**Пользователь `{member}` получил предупреждения по причине {reason}. Количество предупрежденний - `{len(cur_warns)}`, id - `{num}`**' , colour = discord.Color.green() )
			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			await ctx.send( embed = emb )

		sql = ("""UPDATE users SET money = %s, coins = %s, reputation = %s, warns = %s, prison = %s WHERE user_id = %s AND guild_id = %s""")
		val = (cur_money, cur_coins, cur_reputation, json.dumps(cur_warns), str(cur_state_pr), member.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()


	@commands.command(aliases=['remwarn', 'rem-warn'], brief = 'True', name = 'remove-warn', description = '**Снимает указаное предупреждения в участика**', usage = 'remove-warn [@Участник] [Id предупреждения]')
	@commands.check(check_role)	
	async def rem_warn(self, ctx, member: discord.Member, warn_id: int):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		data = DB().sel_user(target = member)
		warns = data['warns']
		state = False

		for warn in warns:
			if warn['id'] == warn_id:
				warns.remove(warn)
				state = True
				break

		if not state:
			emb = discord.Embed(title = 'Ошибка!', description = '**Предупреждения с таким айди не существует! Укажите правильный айди предупреждения**', colour = discord.Color.green())

			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send(embed = emb)
			return
		elif state:
			emb = discord.Embed(description = f'**Предупреждения успешно было снято с участника `{member}`**', colour = discord.Color.green())

			emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await ctx.send(embed = emb)

		sql = ("""UPDATE users SET warns = %s WHERE user_id = %s AND guild_id = %s""")
		val = (json.dumps(warns), member.id, ctx.guild.id)

		self.cursor.execute(sql, val)
		self.conn.commit()


	@commands.command(description = '**Показывает список предупреждений**', usage = 'warns |@Участник|')
	async def warns(self, ctx, member: discord.Member = None):
		client = self.client
		DB().add_amout_command(entity=ctx.command.name)
		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		if not member:
			member = ctx.author

		data = DB().sel_user(target = member)
		warns = data['warns']

		if warns == []:
			emb = discord.Embed( title = f'Предупреждения пользователя - `{member}`', description = 'Список предупреждений пуст.', colour = discord.Color.green() )
		else:
			emb = discord.Embed( title = f'Предупреждения пользователя - `{member}`', colour = discord.Color.green() )

		for warn in warns:
			id_warn = warn['id']
			time_warn = warn['time']
			author_warn = warn['author']
			reason = warn['reason']

			emb.add_field( value = f'**Причина:** {reason}', name = f'Id - {id_warn}, время - {time_warn}, автор - {author_warn}', inline = False )

		emb.set_author( name = member.name, icon_url = member.avatar_url )
		emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

		await ctx.send(embed = emb)

def setup( client ):
	client.add_cog(Moderate(client))