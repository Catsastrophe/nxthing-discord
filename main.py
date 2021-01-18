token = "Nzk1MDU1Mjc4Mzk4ODk4MjI2.X_Dy7Q.Qcu3CHrJ6yGHOo4IvUDSXBBLKR4"
role_for_commands = 'inquisitixn'
MLP = [10,30,50,100,150,200,250,300,350,400,450]
LevelRole = [10,20]

import os,discord
from datetime import datetime
from discord.ext import commands
from discord.utils import get
import sqlite3

database = sqlite3.connect('nothing.db')
sql = database.cursor()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = '-',intents=intents)
bot.remove_command('help')

sql.execute("""CREATE TABLE IF NOT EXISTS users (
		user_id BIGINT,
		level INT,
		messages BIGINT,
		server_id BIGINT,
		balance INT,
		rep INT,
		name TEXT
	)""")
database.commit()

sql.execute("""CREATE TABLE IF NOT EXISTS servers (
		server_id BIGINT,
		auto_role TEXT
	)""")
database.commit()

sql.execute("""CREATE TABLE IF NOT EXISTS roles (
		role TEXT,
		level INT,
		server_id INT
	)""")
database.commit()

sql.execute("""CREATE TABLE IF NOT EXISTS shop (
		role_id INT,
		server_id INT,
		cost BIGINT
	)""")

@bot.event
async def on_ready():
		
		print(f"{bot.user.name} is online")
		await bot.change_presence( status = discord.Status.online, activity = discord.Game('nxthing-discord') )

# SERVER.TXT - SERVER:ROLE # GET ROLE FROM SERVER AND GIVE ROLE TO USER

def MemberLvlUp(user_id):
	sql.execute(f"SELECT level FROM users WHERE user_id = '{user_id}'")
	level = sql.fetchone()[0]

	sql.execute(f"UPDATE users SET level = '{1 + level}' WHERE user_id = '{user_id}'")
	database.commit()

def WriteToLog( text ):
		time = datetime.now().strftime("%Y-%B-%d %H:%M:%S ")
		with open('log.txt','a') as file:
			file.write(time + text + '\n')

@bot.event
async def on_member_remove(member):
		await ctx.send(embed = discord.Embed( description = f'``{member.name}`` ливает с нашего лампового сервера. Да и пофиг)'), 
						color = 0x0c0c0c )
		WriteToLog(f'Member left: {member.name} has left a server')

@bot.command()
async def ping(ctx):
		await ctx.send(f'ping { round(bot.latency * 1000) }ms')

@bot.command()
async def clear(ctx,amount = 3):
		await ctx.channel.purge(limit=amount)

@bot.command()
@commands.has_role( role_for_commands )
async def kick(ctx, member: discord.Member, * , reason = None):
		await ctx.channel.purge(limit=1)

		await member.kick( reason=reason )
		await ctx.send( f'Пользователь {member.mention} был кикнут.')
		WriteToLog(f'{ctx.author.name} kick {member.name} from server {ctx.Guild.name}')

@bot.command()
@commands.has_role( role_for_commands )
async def ban( ctx, member: discord.Member, *, reason = None):
		emb = discord.Embed( title = 'Ban', colour = discord.Color.red() )
		await member.ban(reason= reason)
		emb.set_author( name = member.name, icon_url = member.avatar_url )
		emb.add_field(name = ' ' , value = f'Banned user: {member.mention}')

		await ctx.send( embed = emb )

@bot.command()
#@commands.has_role( role_for_commands )
async def role(ctx,member:discord.Member, *, name:str ):
		role = discord.utils.get( member.guild.roles, name = name)
		await member.add_roles(role)
		await ctx.send(f'Role added')

@bot.command()
#@commands.has_role( role_for_commands )
async def remove_role(ctx,member:discord.Member, *, name:str ):
		role = discord.utils.get( member.guild.roles, name = name )

		await member.remove_roles( role )
		await ctx.send(f'Role removed')
@bot.command()
async def add_shop(ctx, role: discord.Role = None, cost: int = None):
		if role is None:
			await ctx.send (f"**{ctx.author.name}**, укажите роль, которую вы желаете продать")
		elif cost is None:
			await ctx.send (f"**{ctx.author.name}**, укажите цену, за которую вы желаете продать роль")
		elif cost < 0:
			await ctx.send (f"**{ctx.author.name}**, стоимость роли не может быть меньше 0")
		else:
			sql.execute(f"INSERT INTO shop VALUES (?,?,?)", (role.id, ctx.guild.id, cost))
			database.commit()

			await ctx.send(f"Роль **{role.name}** была выставлена участником **{ctx.author.name}** за {cost} :money_with_wings:")

@bot.command()
async def remove_shop(ctx, role: discord.Role = None):
		if role is None:
			await ctx.send (f"**{ctx.author.name}**, укажите роль, которую вы желаете удалить из магазина")
		else:
			sql.execute(f"DELETE FROM shop WHERE role_id = '{role.id}'")
			database.commit()
			await ctx.send(f'Вы удалили роль **{role.mention}** из магазина')

@bot.command()
async def shop(ctx):
		embed = discord.Embed( title = 'Магазин' )

		for i in sql.execute(f"SELECT role_id, cost FROM shop WHERE server_id = '{ctx.guild.id}'"):
			if ctx.guild.get_role(i[0]) != None:
				embed.add_field(
						name = f'Стоимость: {i[1]} :money_with_wings:',
						value = f'Роль: {ctx.guild.get_role(i[0]).mention}',
						inline = False
					)
			else:
				embed.add_field(
					name = 'В магазине ничего нет',
					)
				await ctx.send('В магазине ничего нет!')
		await ctx.send(embed = embed)

@bot.command()
async def buy(ctx, role: discord.Role = None):

		sql.execute(f"SELECT cost FROM shop WHERE role_id = '{role.id}'")
		role_money = sql.fetchone()[0]

		sql.execute(f"SELECT balance FROM users WHERE user_id = '{ctx.author.id}' AND server_id = '{ctx.guild.id}'")
		user_money = sql.fetchone()[0]

		if role is None:
			await ctx.send (f"**{ctx.author.name}**, укажите роль, которую вы желаете купить")
		else:
			if role in ctx.author.roles:
				await ctx.send(f"**{ctx.author.name}**, данная роль уже имеется у вас")
			elif user_money < role_money:
				await ctx.send(f'**{ctx.author.name}**, у вас недостаточно денег для приобретения.')
				await ctx.send(f'У вас: {money}, вам не хватает {int(role_money) - int(user_money)} :money_with_wings:')
			else:
				await ctx.author.add_roles(role)
				sql.execute(f"UPDATE users SET balance = '{int(user_money) - int(role_money)}' WHERE user_id = '{ctx.author.id}' AND server_id = '{ctx.guild.id}'")
				database.commit()

				sql.execute(f"SELECT balance FROM users WHERE user_id = '{ctx.author.id}' AND server_id = '{ctx.guild.id}'")
				user_money = sql.fetchone()[0]

				await ctx.send(f"Вы успешно купили {role.mention} за {role_money}. У вас осталось {user_money} :money_with_wings:")

@bot.command()
async def userid(ctx, member:discord.Member):
		await ctx.send(f'Member: {member.mention} has id {member.id}')

@bot.command()
async def guildid(ctx,member:discord.Member):
		await ctx.send(f'Guild ID: {ctx.guild.id}')

@bot.command()
async def balance(ctx, member:discord.Member):
	sql.execute(f"SELECT balance FROM users WHERE user_id = '{member.id}' AND server_id = '{member.guild.id}'")
	balance = sql.fetchone()

	await ctx.send(f'Balance of {member.mention}: {balance[0]} :money_with_wings:')

@bot.command()
async def add_balance(ctx, member:discord.Member = None, money:int = None):

		if member is None:
			await ctx.send(f'**{ctx.author.name}**, укажите пользователя, которому надо выдать баланс.')
		elif money is None:
			await ctx.send(f'**{ctx.author.name}**, укажите количество денег.')
		elif money <= 0:
			await ctx.send(f'**{ctx.author.name}**, укажите количество денег больше 0')
		else:
			sql.execute(f"SELECT balance FROM users WHERE user_id = '{member.id}' AND server_id = '{ctx.guild.id}'")
			sql_money = sql.fetchone()[0]


			sql.execute(f"UPDATE users SET balance = '{money + int(sql_money)}' WHERE user_id = '{member.id}' AND server_id = '{ctx.guild.id}'")
			database.commit()
			await ctx.send(f'**{member.name}**, было выдано {money} :money_with_wings:')

@bot.command()
async def take_balance(ctx, member:discord.Member = None, money:int = None):

		if member is None:
			await ctx.send(f'**{ctx.author.name}**, укажите пользователя, которому надо выдать баланс.')
		elif money is None:
			await ctx.send(f'**{ctx.author.name}**, укажите количество денег.')
		elif money < 0:
			await ctx.send(f'**{ctx.author.name}**, укажите количество денег больше 0')

		elif money == 0:
			sql.execute(f"UPDATE users SET balance = '0' WHERE user_id = '{member.id}' AND server_id = '{ctx.guild.id}")
			database.commit()
			await ctx.send(f'**{member.name}**, ваш баланс обнулили:money_with_wings:')
			pass

		else:
			sql.execute(f"SELECT balance FROM users WHERE user_id = '{member.id}' AND server_id = '{ctx.guild.id}'")
			sql_money = sql.fetchone()[0]


			sql.execute(f"UPDATE users SET balance = '{int(sql_money) - money}' WHERE user_id = '{member.id}' AND server_id = '{ctx.guild.id}'")
			database.commit()
			await ctx.send(f'**{member.name}**, с вашего баланса снято {money} :money_with_wings:')

@bot.command()
async def update_autorole(ctx, role:str):
		guild_id = ctx.guild.id
		print(role)

		sql.execute(f"SELECT auto_role FROM servers WHERE server_id = '{guild_id}'")
		if sql.fetchone() is None:
			sql.execute(f"INSERT INTO servers VALUES (?, ?)", (guild_id, role))
			database.commit()
		else:
			sql.execute(f"UPDATE servers SET auto_role = '{role}' WHERE server_id = '{guild_id}'")
			database.commit()

@bot.command()
async def main(ctx):
		for i in sql.execute(f"SELECT auto_role FROM servers WHERE server_id = '{ctx.guild.id}'"):
			await ctx.send(f"auto role is: {i[0]}")

@bot.command()
async def messages(ctx, member:discord.Member):
		user_id = member.id
		sql.execute(f"SELECT messages FROM users WHERE user_id = '{user_id}' AND server_id = '{ctx.guild.id}'")
		if sql.fetchone() == None:
			messages = 0
		else:
			messages = sql.fetchone()[0]
		await ctx.send(f'User: {member.mention} has {messages} messages')

@bot.command()
async def level(ctx,member:discord.Member):
		user_id = member.id
		sql.execute(f"SELECT level FROM users WHERE user_id = '{user_id}' AND server_id = '{ctx.guild.id}'")
		level = sql.fetchone()[0]

		await ctx.send(f'Level {member.mention} is {level}')

@bot.command()
async def set_level(ctx,member:discord.Member, level:int):
		user_id = member.id
		guild_id = ctx.guild.id

		sql.execute(f"UPDATE users SET level = '{level}' WHERE user_id = '{user_id}' AND server_id = '{guild_id}'")

		if level == 10:
			channel = bot.get_channel(795068829008134164)
			role = discord.utils.get( member.guild.roles, name = 'feel some good')
			await member.add_roles(role)
			await channel.send(f'{member.name} has arrived 10 LVL and get new role')

@bot.command()
async def all_lvls(ctx):

		for x in sql.execute(f"SELECT role FROM roles WHERE server_id = '{ctx.guild.id}'"):
			await ctx.send(f'Role: {x[0]}')

		for x in sql.execute(f"SELECT level FROM roles WHERE server_id = '{ctx.guild.id}'"):
			await ctx.send(f'Level: {x[0]}')
	#await ctx.send(text)

@bot.command()
@commands.has_role( role_for_commands )
async def sendupdate(ctx,text):

		channel = bot.get_channel(800341261647216651)
		print(text)
		text = text.split(',')
		print(text)

		title = text[0]
		text = text[1]

		colour = discord.Color.blue()
		emb = discord.Embed( title = title, description = text , colour = colour)
		emb.set_author( name = ctx.author.name, icon_url = ctx.author.avatar_url)

		await channel.send( embed = emb )


@bot.command()
async def lvl_role(ctx, level:int, *, role:str):
		guild_id = ctx.guild.id

		sql.execute(f"SELECT role FROM roles WHERE server_id = '{guild_id}'")
		sql_role = sql.fetchone()

		print(sql_role)

		if sql_role == None:
			sql.execute(f"INSERT INTO roles VALUES (?,?,?)", (f'{role}', level, guild_id))
			database.commit()

		sql.execute(f"SELECT level FROM roles WHERE server_id = '{guild_id}'")
		sql_level = sql.fetchone()

		print(sql_level)

		if level == sql_level[0]:
			# поменять роль
			sql.execute(f"UPDATE roles SET role = '{role}' WHERE server_id = '{guild_id}'")
			database.commit()
			await ctx.send(f'For Guild: {ctx.guild.name} updated role from {sql_role} to {role} for level: {level}')

		elif role == sql_role[0]:
			# поменять уровень
			sql.execute(f"UPDATE roles SET level = '{level}' WHERE server_id = '{guild_id}'")
			database.commit()
			await ctx.send(f'For Guild: {ctx.guild.name} updated level from {sql_level} to {level} for role: {role}')
		else:
			sql.execute(f"INSERT INTO roles VALUES (?, ?, ?)", (f'{role}', f'{level}', f'{guild_id}'))
			database.commit()
			await ctx.send(f'For Guild: {ctx.guild.name} created role {role} for a {level} level.')

@bot.event
async def on_member_join(member):
		channel = bot.get_channel( 800254100407189508 )
		WriteToLog(f'Member join: {member.name} join the server')


		sql.execute(f"SELECT user_id FROM users WHERE server_id,user_id = '{member.guild.id}','{member.id}'")
		if sql.fetchone() is None:
			sql.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", (member.id, 0, 1, member.guild.id, 1000, 0, member.name))
			database.commit()

			print(f'Зарегистрирован {member.name} c ID: {member.id}')
		else:
			print('Данный участник существует')


		for i in sql.execute(f"SELECT auto_role FROM servers WHERE server_id = '{member.guild.id}'"):
			roledb = i[0]
			role = discord.utils.get( member.guild.roles, name = roledb )
			await member.add_roles(role)

		#await member.add_roles(role)
		await channel.send( embed = discord.Embed( description = f'Привет, ``{member.name}``, пасеба что залетел к нам nxthing!', 
							color = 0x0c0c0c) )


@bot.event
async def on_message(message):
		WriteToLog(f'Message from {message.author.name}: {message.content}')

		user_id = message.author.id
		guild_id = message.guild.id

		sql.execute(f"SELECT messages FROM users WHERE user_id  = '{user_id}' AND server_id = '{guild_id}'")
		messages = sql.fetchone()

		if messages:
			messages = messages[0]
			print( int(messages)+1 )
			sql.execute(f"SELECT level FROM users WHERE user_id = '{user_id}' AND server_id = '{guild_id}'")
			level = sql.fetchone()

			for x in MLP:
				if messages == x:
					print('message in mlp')
					
					if level:
						level = int(level[0])
						next_level = level+1
						
						print( f'Next level is: {next_level}' )
						print( f'Level found: {level}' )
						
						for z in sql.execute(f"SELECT level FROM roles WHERE server_id = '{guild_id}'"):
							print(z[0])
							if next_level == z[0]:
								sql.execute(f"SELECT role FROM roles WHERE server_id = '{guild_id}' AND level = '{next_level}'")
								new_role = sql.fetchone()
								print(new_role)
								if new_role:
									new_role = new_role[0]
									role = discord.utils.get( message.guild.roles, name = new_role)
									await message.author.add_roles(role)
									
									sql.execute(f"UPDATE users SET level = '{next_level}' WHERE user_id = '{user_id}' AND server_id = '{guild_id}'")
									database.commit()

								else: 
									print('Не найдена роль.')
							else: 
								print(f'{level}: +1 not work')
					else: 
						print('User has not level')
				else: 
					pass
			
			sql.execute(f"UPDATE users SET messages = '{messages+1}' WHERE user_id = '{user_id}' AND server_id = '{guild_id}'")
			database.commit()


		else:
			sql.execute(f"INSERT INTO users VALUES (?,?,?,?,?,?,?)", (f'{user_id}',0,1,f'{guild_id}', 1000, 0, message.author.name))
			database.commit()
			print('Аккаунт создан.')

		await bot.process_commands(message)

bot.run(token)