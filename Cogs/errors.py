import discord
import colorama
import datetime
import json
import sys
from discord.ext import commands
from discord.utils import get
from discord.ext.commands import Bot
from Tools.database import DB
from configs import configs
from colorama import *
init()

def dump( filename, filecontent ):
	with open( filename, 'w', encoding = 'utf-8' ) as f:
		f.writelines( filecontent )


def load( filename ):
	with open( filename, 'r', encoding = 'utf-8' ) as f:
		return f.read()

global Footer
Footer = configs['FOOTER_TEXT']

class Errors(commands.Cog, name = 'Errors'):

	def __init__(self, client):
		self.client = client


	@commands.Cog.listener()
	async def on_command_error( self, ctx, error ):
		DB().add_amout_command()
		client = self.client
		now_date = str(datetime.datetime.today())[:-16]
		filename = f'./Data/Logs/log-{now_date}.txt'
		space = ''
		log_error = f'\n\n=============================================================\nВремя: {str(datetime.datetime.today())}\n\nОшибка:\n{error}\n============================================================='

		try:
			log = load(filename)
		except:
			dump(filename, space)
			log = load(filename)

		if log == '':
			dump(filename, log_error)
		else:
			log_error = log + log_error
			dump(filename, log_error)

		if isinstance( error, commands.errors.CommandOnCooldown ):
			await ctx.message.add_reaction('❌')
			retry_after = error.retry_after

			if retry_after < 60:
				emb = discord.Embed( title = 'Ошибка!', description = f'**Кулдавн в команде еще не прошёл! Подождите {int(retry_after)} секунд**', colour = discord.Color.green() )
			elif retry_after > 60 and retry_after < 1800:
				emb = discord.Embed( title = 'Ошибка!', description = f'**Кулдавн в команде еще не прошёл! Подождите {int(retry_after / 60)} минут**', colour = discord.Color.green() )
			elif retry_after > 1800:
				emb = discord.Embed( title = 'Ошибка!', description = f'**Кулдавн в команде еще не прошёл! Подождите {int(retry_after / 60 / 24)} часа**', colour = discord.Color.green() )

			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			
			await ctx.send( embed = emb )

		elif isinstance( error, commands.errors.MissingRequiredArgument ):
			await ctx.message.add_reaction('❌')
			emb = discord.Embed( title = 'Ошибка!', description = f'**Вы не указали аргумент. Укажати аргумент - {error.param.name} к указаной команде!**', colour = discord.Color.green() )
			
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			
			await ctx.send( embed = emb )

		elif isinstance( error, commands.errors.CommandNotFound ):
			pass

		elif isinstance( error, commands.errors.NotOwner ):

			emb = discord.Embed( title = 'Ошибка!', description = '**Вы неявляетесь создателем бота! Эта команда только для создателей!**', colour = discord.Color.green() )
			
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			
			await ctx.send( embed = emb )
		elif isinstance( error, commands.errors.MissingPermissions ):

			emb = discord.Embed( title = 'Ошибка!', description = '**У вас не достаточно прав! Для этой команды нужны права администратора**', colour = discord.Color.green() )
			
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			
			await ctx.send( embed = emb )
		elif isinstance( error, commands.errors.BadArgument ):
			emb = discord.Embed( title = 'Ошибка!', description = '**Указан не правильный аргумент! Возможно вы указали не тот ID**', colour = discord.Color.green() )
			
			emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb.set_footer( text = Footer, icon_url = client.user.avatar_url )
			
			await ctx.send( embed = emb )
		elif isinstance(error, commands.errors.BotMissingPermissions):
			owner = get( ctx.guild.members, id = ctx.guild.owner_id)

			emb_err = discord.Embed( title = 'Ошибка!', description = f'**У бота не достаточно прав на модерацию! Пожалуйста для корректной работы бота поместите роль бота више всех остальных!**' , colour = discord.Color.green() )

			emb_err.set_author( name = client.user.name, icon_url = client.user.avatar_url )
			emb_err.set_footer( text = Footer, icon_url = client.user.avatar_url )

			await owner.send(embed = emb_err)
		elif isinstance(error, commands.errors.CheckFailure):
			pass
		else:
			raise error


def setup( client ):
	client.add_cog(Errors(client))
