import discord
import datetime
import os
import json
import asyncio
import ast
from discord.ext import commands
from discord.utils import get
from discord.voice_client import VoiceClient
from discord.ext.commands import Bot
from configs import configs
from Tools.database import DB

def clear_commands( guild ):

	data = DB().sel_guild(guild = guild)
	purge = data['purge']
	return purge


def insert_returns( body ):
   
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

   
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)


    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

global Footer
Footer = configs['FOOTER_TEXT']

class Owner(commands.Cog, name = 'Owner'):

	def __init__(self, client):
		self.client = client


	@commands.command()
	@commands.is_owner()
	async def restart( self, ctx ):
		client = self.client

		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		emb = discord.Embed( title = 'Перезагрузка бота', colour = discord.Color.green() )
		emb.set_image( url = 'https://i.gifer.com/Jx6X.gif' )

		emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
		emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

		msg = await ctx.send( embed = emb )	

		e = discord.Embed( title = 'Бот перезагружен', colour = discord.Color.green() )

		e.set_image( url = 'http://www.clipartbest.com/cliparts/9iz/6Rp/9iz6RpkGT.gif' )
		e.set_author( name = client.user.name, icon_url = client.user.avatar_url )
		e.set_footer( text = Footer, icon_url = client.user.avatar_url )

		await asyncio.sleep(2)

		await msg.edit( embed = e )

		await client.logout()
		await os.system('python bot.py')


	@commands.command()
	@commands.is_owner()
	async def cls( self, ctx ):
		client = self.client

		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		emb = discord.Embed( title = 'Ожидайте... Происходит очистка консоли...', colour = discord.Color.green() )
		emb.set_image( url = 'https://i.gifer.com/Jx6X.gif' )

		emb.set_author( name = client.user.name, icon_url = client.user.avatar_url )
		emb.set_footer( text = Footer, icon_url = client.user.avatar_url )

		msg = await ctx.send( embed = emb )	

		e = discord.Embed( title = 'Консоль успешно очищена!', colour = discord.Color.green() )

		e.set_image( url = 'http://www.clipartbest.com/cliparts/9iz/6Rp/9iz6RpkGT.gif' )
		e.set_author( name = client.user.name, icon_url = client.user.avatar_url )
		e.set_footer( text = Footer, icon_url = client.user.avatar_url )

		await asyncio.sleep(3)

		await msg.edit( embed = e )

		os.system('cls')


	@commands.command( aliases = ['print'] )
	@commands.is_owner()
	async def p( self, ctx, *, arg ):
		client = self.client

		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		print(arg)


	@commands.command( aliases = ['eval'] ) 
	@commands.is_owner()
	async def e( self, ctx, *, cmd ):
		client = self.client

		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		fn_name = "_eval_expr"

		cmd = cmd.strip("` ")
		cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

		body = f"async def {fn_name}():\n{cmd}"

		parsed = ast.parse(body)
		body = parsed.body[0].body

		insert_returns(body)

		env = {
			'client': ctx.bot,
			'discord': discord,
			'os': os,
			'commands': commands,
			'ctx': ctx,
			'get': get,
			'__import__': __import__
		}
		exec(compile(parsed, filename="<ast>", mode="exec"), env)

		result = (await eval(f"{fn_name}()", env))

		if result != None:
			await ctx.send(result)
		elif result == None:
			return


	@commands.command()
	@commands.is_owner()
	async def rest_cd(self, ctx, *, command: str):
		client = self.client

		purge = clear_commands(ctx.guild)
		await ctx.channel.purge( limit = purge )

		command = client.get_command(command)
		command.reset_cooldown(ctx)

		
def setup( client ):
	client.add_cog(Owner(client))