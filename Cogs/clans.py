import discord
import os
import uuid
import json
import mysql.connector
from configs import configs
from Tools.database import DB
from discord.ext import commands

class Clans(commands.Cog):

	def __init__(self, client):
		self.client = client
		self.FOOTER = configs['FOOTER_TEXT']
		self.conn = mysql.connector.connect(user='root', password=os.environ['DB_PASSWORD'], host='localhost', database='data')
		self.cursor = self.conn.cursor(buffered=True)


	@commands.group()
	async def clan(self, ctx):
		purge = self.client.clear_commands(ctx.guild)
		await ctx.channel.purge(limit=purge)


	@clan.command()
	async def create(self, ctx, *, name: str):
		data = DB().sel_guild(guild=ctx.guild)['clans']
		user_data = DB().sel_user(target=ctx.author)

		for clan in data:
			if ctx.author.id in clan['members']:
				emb = discord.Embed(title='Ошибка!', description='**Вы уже находитесь в одном из кланов сервера!**', colour=discord.Color.green())
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction('❌')
				return

		if user_data['coins'] < 5000:
			emb = discord.Embed(title='Ошибка!', description='**У вас не достаточно денег для создания клана!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if len(data) > 20:
			emb = discord.Embed(title='Ошибка!', description='**Превышен лимит кланов на сервере!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		role = await ctx.guild.create_role(name='PT-[CLAN]-'+name)
		await ctx.author.add_roles(role)
		coins = user_data['coins'] - 5000
		new_id = str(uuid.uuid4())
		clan_data = {
			'id': new_id,
			'name': name,
			'role_id': role.id,
			'members': [ctx.author.id],
			'owner': ctx.author.id,
			'description': 'Не указано',
			'short_desc': 'Не указано',
			'size': 10
		}
		data.append(clan_data)

		emb = discord.Embed(title=f'Успешно созданн новый клан', description=f'**Id -** `{new_id}`\n**Названия -** `{name}`', colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		sql = ("""UPDATE guilds SET clans = %s WHERE guild_id = %s AND guild_id = %s""")
		val = (json.dumps(data), ctx.guild.id, ctx.guild.id)
		self.cursor.execute(sql, val)
		sql = ("""UPDATE users SET coins = %s, clan = %s WHERE guild_id = %s AND user_id = %s""")
		val = (coins, json.dumps(clan_data), ctx.guild.id, ctx.author.id)
		self.cursor.execute(sql, val)
		self.conn.commit()


	@clan.command()
	async def edit(self, ctx, clan_id: str):
		pass

	
	@clan.command()
	async def delete(self, ctx, clan_id: str):
		data = DB().sel_guild(guild=ctx.guild)['clans']

		for clan in data:
			if clan['id'] == clan_id:
				delete_clan = clan
				try:
					data.remove(clan)
					for member_id in clan['members']:
						try:
							await ctx.guild.get_member(member_id).remove_roles(ctx.guild.get_role(clan['role_id']))
							await ctx.guild.get_role(clan['role_id']).delete()
						except AttributeError:
							pass
				except ValueError:
					emb = discord.Embed(title='Ошибка!', description='**Клана с таким id не существует!**', colour=discord.Color.green())
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction('❌')
					return

		sql = ("""UPDATE guilds SET clans = %s WHERE guild_id = %s AND guild_id = %s""")
		val = (json.dumps(data), ctx.guild.id, ctx.guild.id)
		self.cursor.execute(sql, val)
		for member_id in delete_clan['members']:
			sql = ("""UPDATE users SET clan = %s WHERE guild_id = %s AND user_id = %s""")
			val = (json.dumps({}), ctx.guild.id, member_id)
			self.cursor.execute(sql, val)
		self.conn.commit()
		await ctx.message.add_reaction('✅')


	@clan.command()
	async def members(self, ctx, clan_id: str):
		data = DB().sel_guild(guild=ctx.guild)['clans']
		state = False
		for clan in data:
			if clan['id'] == clan_id:
				state = True
				members = '\n'.join(f'**Участник -** `{str(ctx.guild.get_member(member_id))}`' if member_id != clan['owner'] else f'**Владелец -** `{str(ctx.guild.get_member(member_id))}`' for member_id in clan['members'])
				emb = discord.Embed(title=f"""Список участников клана - {clan['name']}""", description=members, colour=discord.Color.green())
				break

		if state:
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		else:
			emb = discord.Embed(title='Ошибка!', description='**Клана с таким id не существует!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')


	@clan.command()
	async def kick(self, ctx, clan_id: str, member: discord.Member = None):
		pass


	@clan.command(name='list')
	async def list_clans(self, ctx):
		data = DB().sel_guild(guild=ctx.guild)['clans']
		if data != []:
			emb = discord.Embed(title='Список кланов сервера', description=f'**Общее количество кланов на сервере:** `{len(data)}`', colour=discord.Color.green())
			for clan in data:
				emb.add_field(name=clan['name'], value=f"""**Id -** `{clan['id']}`\n**Краткое описания -** `{clan['short_desc']}`\n**Максимальное количество участников -** `{clan['size']}`\n**Владелец -** `{str(ctx.guild.get_member(clan['owner']))}`""")
		else:
			emb = discord.Embed(title='Список кланов сервера', description=f'**На сервере нету кланов**', colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)


	@clan.command()
	async def info(self, ctx, clan_id: str):
		data = DB().sel_guild(guild=ctx.guild)['clans']
		state = False
		for clan in data:
			if clan['id'] == clan_id:
				state = True
				emb = discord.Embed(title=f"""Информация о клане - {clan['name']}""", description=f"""**Id -** `{clan['id']}`\n**Описания -** `{clan['description']}`\n**Владелец -** `{ctx.guild.get_member(clan['owner'])}`\n**Роль клана -** `{ctx.guild.get_role(clan['role_id']).name}`\n**Максимальное количество участников -** `{clan['size']}`\n**Участников -** `{len(clan['members'])}`""", colour=discord.Color.green())
				break

		if state:
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
		else:
			emb = discord.Embed(title='Ошибка!', description='**Клана с таким id не существует!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')


	@clan.command()
	async def leave(self, ctx):
		data = DB().sel_guild(guild=ctx.guild)['clans']
		user_clan = DB().sel_user(target=ctx.author)['clan']
		state = False
		for clan in data:
			if clan['id'] == user_clan['id']:
				if clan['owner'] != ctx.author.id:
					state = True
					self.cursor.execute(("""UPDATE users SET clan = %s WHERE user_id = %s AND guild_id = %s"""), (json.dumps({}), ctx.author.id, ctx.guild.id))
					await ctx.message.add_reaction('✅')
					break
				else:
					emb = discord.Embed(title='Ошибка!', description='**Вы не можете покинуть свой клан!**', colour=discord.Color.green())
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction('❌')
					return

		if not state:
			emb = discord.Embed(title='Ошибка!', description='**Клана с таким id не существует!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')


	@clan.command()
	async def invite(self, ctx, member: discord.Member):
		user_clan = DB().sel_user(target=ctx.author)['clan']

		# if member == ctx.author:
		# 	emb = discord.Embed(title='Ошибка!', description='**Вы не можете пригласить себя!**', colour=discord.Color.green())
		# 	emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		# 	emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		# 	await ctx.send(embed=emb)
		# 	await ctx.message.add_reaction('❌')
		
		if user_clan != {}:
			if len(user_clan['members']) <= user_clan['size']:
				emb = discord.Embed(title=f"""Запрос на присоидениния к клану - {user_clan['name']}""", description=f"""**Id -** `{user_clan['id']}`\n**Краткое описания -** `{user_clan['short_desc']}`\n**Владелец -** `{str(ctx.guild.get_member(user_clan['owner']))}`""", colour=discord.Color.green())
				emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
				emb.set_footer(text=f'Запрос отправил: {str(ctx.author)}', icon_url=ctx.author.avatar_url)
				message = await member.send(embed=emb)
				await message.add_reaction('✅')
				await message.add_reaction('❌')
				reaction, user = await self.client.wait_for('on_raw_reaction_add', check=lambda reaction, user: reaction.emoji == '✅' and reaction.message.id == message.id)
				if reaction.emoji == '✅':
					print('Prinyal')

				reaction, user = await self.client.wait_for('on_raw_reaction_add', check=lambda reaction, user: reaction.emoji == '❌' and reaction.message.id == message.id)
				if reaction.emoji == '❌':
					print('Ne Prinyal')
			
			else:
				emb = discord.Embed(title='Ошибка!', description='**Указаный клан переполнен!**', colour=discord.Color.green())
				emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction('❌')
		else:
			emb = discord.Embed(title='Ошибка!', description='**Вы не находитесь но в одном клане сервера!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')


def setup(client):
	client.add_cog(Clans(client))