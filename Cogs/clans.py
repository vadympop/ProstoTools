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

		if user_data['coins'] < 15000:
			emb = discord.Embed(title='Ошибка!', description='**У вас не достаточно коинов**', colour=discord.Color.green())
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
		coins = user_data['coins'] - 15000
		new_id = str(uuid.uuid4())
		data.append({
			'id': new_id,
			'name': name,
			'role_id': role.id,
			'members': [ctx.author.id],
			'owner': ctx.author.id,
			'description': 'Не указано',
			'short_desc': 'Не указано',
			'size': 10
		})

		emb = discord.Embed(title=f'Успешно созданн новый клан', description=f'**Id -** `{new_id}`\n**Названия -** `{name}`', colour=discord.Color.green())
		emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
		await ctx.send(embed=emb)

		sql = ("""UPDATE guilds SET clans = %s WHERE guild_id = %s AND guild_id = %s""")
		val = (json.dumps(data), ctx.guild.id, ctx.guild.id)
		self.cursor.execute(sql, val)
		sql = ("""UPDATE users SET coins = %s, clan = %s WHERE guild_id = %s AND user_id = %s""")
		val = (coins, new_id, ctx.guild.id, ctx.author.id)
		self.cursor.execute(sql, val)
		self.conn.commit()


	@clan.command()
	async def edit(self, ctx, clan_id: str, field: str, value):
		pass

	
	@clan.command()
	async def delete(self, ctx):
		data = DB().sel_guild(guild=ctx.guild)['clans']
		user_clan = DB().sel_user(target=ctx.author)['clan']
		if user_clan == "":
			emb = discord.Embed(title='Ошибка!', description='**Вас нету ни в одном клане сервера!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		for clan in data:
			if clan['id'] == user_clan:
				if clan['owner'] == ctx.author.id:
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
				else:
					emb = discord.Embed(title='Ошибка!', description='**Вы не владелец указаного клана!**', colour=discord.Color.green())
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
			val = ('', ctx.guild.id, member_id)
			self.cursor.execute(sql, val)
		self.conn.commit()
		await ctx.message.add_reaction('✅')


	@clan.command()
	async def members(self, ctx, clan_id: str = None):
		data = DB().sel_guild(guild=ctx.guild)['clans']
		state = False
		if not clan_id:
			if DB().sel_user(target=ctx.author)['clan'] != '':
				clan_id = DB().sel_user(target=ctx.author)['clan']
			else:
				emb = discord.Embed(title='Ошибка!', description='**Вы не указали аргумент. Укажити аргумент - clan_id к указаной команде!**', colour=discord.Color.green())
				emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction('❌')

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
	async def kick(self, ctx, member: discord.Member):
		data = DB().sel_guild(guild=ctx.guild)['clans']
		user_clan = DB().sel_user(target=ctx.author)['clan']
		if user_clan == '':
			emb = discord.Embed(title='Ошибка!', description='**Вас нету ни в одном клане сервера!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='**Вы не можете кикнуть самого себя!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		for clan in data:
			if clan['id'] == user_clan:
				if clan['owner'] == ctx.author.id:
					if member.id in clan['members']:
						clan['members'].remove(member.id)
						try:
							await member.remove_roles(ctx.guild.get_role(clan['role_id']))
						except:
							pass
						self.cursor.execute(("""UPDATE users SET clan = %s WHERE user_id = %s AND guild_id = %s"""), ('', member.id, ctx.guild.id))
						self.cursor.execute(("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""), (json.dumps(data), ctx.guild.id))
						self.conn.commit()
						await ctx.message.add_reaction('✅')
						return
					else:
						emb = discord.Embed(title='Ошибка!', description='**В клане нету указаного участника!**', colour=discord.Color.green())
						emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
						emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction('❌')
						return
				else:
					emb = discord.Embed(title='Ошибка!', description='**Вы не владелец указаного клана!**', colour=discord.Color.green())
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction('❌')
					return


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
	async def info(self, ctx, clan_id: str = None):
		data = DB().sel_guild(guild=ctx.guild)['clans']
		state = False
		if not clan_id:
			if DB().sel_user(target=ctx.author)['clan'] != '':
				clan_id = DB().sel_user(target=ctx.author)['clan']
			else:
				emb = discord.Embed(title='Ошибка!', description='**Вы не указали аргумент. Укажити аргумент - clan_id к указаной команде!**', colour=discord.Color.green())
				emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
				emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
				await ctx.send(embed=emb)
				await ctx.message.add_reaction('❌')

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
		if user_clan == '':
			emb = discord.Embed(title='Ошибка!', description='**Вас нету ни в одном клане сервера!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		for clan in data:
			if clan['id'] == user_clan:
				if clan['owner'] != ctx.author.id:
					try:
						await ctx.author.remove_roles(ctx.guild.get_role(clan['role_id']))
					except:
						pass
					clan['members'].remove(ctx.author.id)
					self.cursor.execute(("""UPDATE users SET clan = %s WHERE user_id = %s AND guild_id = %s"""), ('', ctx.author.id, ctx.guild.id))
					self.cursor.execute(("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""), (json.dumps(data), ctx.guild.id))
					self.conn.commit()
					await ctx.message.add_reaction('✅')
					break
				else:
					emb = discord.Embed(title='Ошибка!', description='**Вы не можете покинуть свой клан!**', colour=discord.Color.green())
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction('❌')
					return


	@clan.command()
	async def invite(self, ctx, member: discord.Member):
		user_clan = DB().sel_user(target=ctx.author)['clan']
		data = DB().sel_guild(guild=ctx.guild)['clans']

		if member == ctx.author:
			emb = discord.Embed(title='Ошибка!', description='**Вы не можете пригласить себя!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
		
		if user_clan == '':
			emb = discord.Embed(title='Ошибка!', description='**Вас нету ни в одном клане сервера!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return
		
		for clan in data:
			if clan['id'] == user_clan:
				if len(clan['members']) < clan['size']:
					pass
				else:
					emb = discord.Embed(title='Ошибка!', description='**Указаный клан переполнен!**', colour=discord.Color.green())
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction('❌')
					return


	@clan.command(name='send-join-request')
	async def send_join_request(self, ctx, clan_id: str):
		data = DB().sel_guild(guild=ctx.guild)['clans']
		state = False

		if DB().sel_user(target=ctx.author)['clan'] != '':
			emb = discord.Embed(title='Ошибка!', description='**Вы уже находитесь в одном из кланов сервера!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		for clan in data:
			if clan['id'] == clan_id:
				state = True
				if len(clan['members']) < clan['size']:
					pass
				else:
					emb = discord.Embed(title='Ошибка!', description='**Указаный клан переполнен!**', colour=discord.Color.green())
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction('❌')

		if not state:
			emb = discord.Embed(title='Ошибка!', description='**Клана с таким id не существует!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')


	@clan.command()
	async def buy(self, ctx, item: str, color: str = None):
		user_data = DB().sel_user(target=ctx.author)
		data = DB().sel_guild(guild=ctx.guild)['clans']
		item = item.lower()

		if user_data['clan'] == '':
			emb = discord.Embed(title='Ошибка!', description='**Вас нету ни в одном клане сервера!**', colour=discord.Color.green())
			emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
			await ctx.send(embed=emb)
			await ctx.message.add_reaction('❌')
			return

		for clan in data:
			if clan['id'] == user_data['clan']:
				if item == 'category' or item == 'категория':
					if 'category_id' not in clan.keys():
						if user_data['coins'] >= 10000:
							overwrites = {ctx.guild.get_member(member_id): discord.PermissionOverwrite(send_messages=True, read_messages=True) for member_id in clan['members']}
							overwrites.update({
								ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=False),
								self.client.user: discord.PermissionOverwrite(send_messages=True, read_messages=True)
							})
							category = await ctx.guild.create_category(name='PT-[CLAN]-'+clan['name'], overwrites=overwrites)
							clan.update({'category_id': category.id})
							user_data['coins'] - 10000

							emb = discord.Embed(description=f"""**Вы успешно купили категорию - `{category.name}` для клана - `{clan['name']}`!**""", colour=discord.Color.green())
							emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
							emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
							await ctx.send(embed=emb)
							
							self.cursor.execute(("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""), (json.dumps(data), ctx.guild.id))
							self.cursor.execute(("""UPDATE users SET coins = %s WHERE user_id = %s AND guild_id = %s"""), (user_data['coins'], ctx.author.id, ctx.guild.id))
							self.conn.commit()
						else:
							emb = discord.Embed(title='Ошибка!', description='**У вас не достаточно коинов!**', colour=discord.Color.green())
							emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
							emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
							await ctx.send(embed=emb)
							await ctx.message.add_reaction('❌')
							return
					else:
						emb = discord.Embed(title='Ошибка!', description='**Клан уже имеет категорию!**', colour=discord.Color.green())
						emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
						emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction('❌')
						return
				elif item == 'size' or item == 'размер':
					if user_data['coins'] >= 7500:
						if clan['size'] >= 25:
							emb = discord.Embed(title='Ошибка!', description='**Клан достиг максимального размера!**', colour=discord.Color.green())
							emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
							emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
							await ctx.send(embed=emb)
							await ctx.message.add_reaction('❌')
							return
						
						emb = discord.Embed(description='**Вы успешно расширили клан на 5 слотов!**', colour=discord.Color.green())
						emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
						emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
						await ctx.send(embed=emb)
						
						clan['size'] + 5
						user_data['coins'] - 7500
						self.cursor.execute(("""UPDATE guilds SET clans = %s WHERE guild_id = %s"""), (json.dumps(data), ctx.guild.id))
						self.cursor.execute(("""UPDATE users SET coins WHERE user_id = %s AND guild_id = %s"""), (user_data['coins'], ctx.author.id, ctx.guild.id))
						self.conn.commit()
					else:
						emb = discord.Embed(title='Ошибка!', description='**У вас не достаточно коинов!**', colour=discord.Color.green())
						emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
						emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction('❌')
						return
				elif item == 'color' or item == 'colour' or item == 'цвет':
					colors = {
						'teal': 0x1abc9c,
						'dark_teal': 0x11806a,
						'green': 0x2ecc71,
						'dark_green': 0x1f8b4c,
						'blue': 0x3498db,
						'dark_blue': 0x206694,
						'purple': 0x9b59b6,
						'dark_purple': 0x71368a,
						'magenta': 0xe91e63,
						'dark_magenta': 0xad1457,
						'gold': 0xf1c40f,
						'dark_gold': 0xc27c0e,
						'orange': 0xe67e22,
						'dark_orange': 0xa84300,
						'red': 0xe74c3c,
						'dark_red': 0x992d22,
						'lighter_gray': 0x95a5a6,
						'dark_gray': 0x607d8b,
						'light_gray': 0x979c9f,
						'darker_gray': 0x546e7a,
						'blurple': 0x7289da,
						'greyple': 0x99aab5,
					}
					if user_data['coins'] >= 5000:
						try:
							await ctx.guild.get_role(clan['role_id']).edit(colour=colors[color.lower()])
							emb = discord.Embed(description='**Вы успешно купили новый цвет для роли вашего клана!**', colour=discord.Color.green())
							emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
							emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
							await ctx.send(embed=emb)
						except:
							emb = discord.Embed(title='Ошибка!', description='**Была удалена роль клана!**', colour=discord.Color.green())
							emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
							emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
							await ctx.send(embed=emb)
							await ctx.message.add_reaction('❌')
							return
					else:
						emb = discord.Embed(title='Ошибка!', description='**У вас не достаточно коинов!**', colour=discord.Color.green())
						emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
						emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
						await ctx.send(embed=emb)
						await ctx.message.add_reaction('❌')
						return
				else:
					emb = discord.Embed(title='Ошибка!', description='**Вы указали не правильный предмет!**', colour=discord.Color.green())
					emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
					emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
					await ctx.send(embed=emb)
					await ctx.message.add_reaction('❌')
					return

	
	@clan.command()
	async def add_member_test(self, ctx, member: discord.Member):
		data = DB().sel_guild(guild=ctx.guild)['clans']
		user_clan = DB().sel_user(target=ctx.author)['clan']
		for clan in data:
			if clan['id'] == user_clan:
				if member.id not in clan['members']:
					clan_id = clan['id']
					clan['members'].append(member.id)

		self.cursor.execute(("""UPDATE users SET clan = %s WHERE user_id = %s AND guild_id = %s"""), (clan_id, member.id, ctx.guild.id))
		self.cursor.execute(("""UPDATE guilds SET clans = %s WHERE guild_id = %s AND guild_id = %s"""), (json.dumps(data), ctx.guild.id, ctx.guild.id))
		self.conn.commit()
		await ctx.message.add_reaction('✅')


def setup(client):
	client.add_cog(Clans(client))