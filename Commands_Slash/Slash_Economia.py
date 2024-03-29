import random, discord

from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option
from Outhers.Economi import update_bank, update_inv, open_account, open_inv, collection, collection2, reload_inv, shop, crafts
from Outhers.Random import banip, IdS, better_time

class _Ec(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def SetE(self,ctx, id: int, *, dindin = 0):
            
        if ctx.message.author.id == IdS:

            user = self.bot.get_user(id)

            await open_account(user)

            SetM = int(dindin)
                    
            await ctx.send(f'Foram dados {SetM} edinhos para <@{id}>')

            await update_bank(user, + dindin)
        else:
            return

    @commands.command()
    async def RmvE(self,ctx, id: int, *, dindin = 0):
            
        if ctx.message.author.id == IdS:

            if dindin == 0:
                await ctx.send(f'Nenhum edinho foi setado para <@{id}>')
            else:

                user = self.bot.get_user(id)

                await open_account(user)

                SetM = int(dindin)
                    
                await ctx.send(f'Foram removidos {SetM} edinhos para <@{id}>')

                await update_bank(user, - dindin)

    @cog_ext.cog_slash(
        name='Edinhos', 
        description = 'Mostra a sua quantidade de edinhos ou de um membro',
        options = [
            create_option(
                name = 'membro',
                description = 'Selecione um membro para ver a quantia',
                option_type = 6,
                required = False
            )
        ]
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _Carteira(self, ctx:SlashContext, membro: discord.Member = None):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.send('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return
            

            if membro == None:
                membro = ctx.author
            else:
                membro = membro

            await open_account(membro)

            bal = collection.find_one({"_id": membro.id})
            
            em = discord.Embed(title = f"{membro.name} Edinhos", color = discord.Color.red())
            em.add_field(name ='Edinhos', value = bal["Edinhos"])

            await ctx.send(embed = em)

    @cog_ext.cog_slash(
        name='Rolar', 
        description='Ganha edinhos entre 0 e 2000 edinhos'
    )
    @commands.cooldown(3, 7200, commands.BucketType.user)
    async def _beg(self, ctx:SlashContext):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.send('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return
             
            edinhos = random.randint(0,2000)

            await ctx.send(f'Você ganhou {edinhos} edinhos!!')

            await open_account(ctx.author)

            await update_bank(ctx.author, + edinhos)

    @cog_ext.cog_slash(
        name='transferir', 
        description='Transfere edinhos para algum membro',
        options=[
            create_option(
                name = 'membro',
                description = 'Escolha o membro para transferir',
                option_type = 6,
                required = True
            ),
            create_option(
                name = 'edinhos',
                description = 'Escolha a quantidade a transferir',
                option_type = 4,
                required = True
            )
        ]
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _Transferir(self, ctx:SlashContext, membro: discord.Member, edinhos = None):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.send('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return
            
            await open_account(ctx.author)
            await open_account(membro)
            bal = collection.find_one({"_id": ctx.author.id})

            if edinhos == None:
                await ctx.reply(f'Você precisa selecionar uma quantidade de edinho para transferir')

            dindin = int(edinhos)

            b1 = bal["Edinhos"]

            if dindin > b1:
                await ctx.reply(f'Você não tem dinheiro suficiente')
            elif dindin == 0:
                await ctx.reply('A quantia tem que ser maior que zero')
                return
            elif dindin < 0:
                await ctx.reply(f'A quantia deve ser positiva')
                return

            await update_bank(ctx.author,- dindin)
            await update_bank(membro,+ dindin)
            await ctx.reply(f'Voce transferiu {dindin} edinhos')

    @cog_ext.cog_slash(
        name='Loteria', 
        description='Aposte seus edinhos podendo quadruplicar eles',
        options = [
            create_option(
                name = 'edinhos',
                description = 'Selecione a quantia a apostar',
                option_type = 4,
                required = True
            )
        ]
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _loteria(self, ctx:SlashContext, edinhos = None):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.send('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return
            
            await open_account(ctx.author)

            if edinhos == None:
                await ctx.reply(f'Você precisa selecionar uma quantidade de edinho para Jogar')

            bal = collection.find_one({"_id": ctx.author.id})

            dindin = int(edinhos)

            if dindin > bal["Edinhos"]:
                await ctx.reply(f'Você não tem dinheiro suficiente')
                return
            elif dindin == 0:
                await ctx.send('A quantia deve ser maior que 0')
                return
            elif dindin < 0:
                await ctx.reply(f'A quantia deve ser positiva')
                return

            final = []
            for i in range(3):
                a = random.choice([':pineapple:',':grapes:',':kiwi:',])

                final.append(a)

            await ctx.reply(str(final))


            if final[0] == final[1] == final[2]:

                await update_bank(ctx.author,4*dindin)
                await ctx.reply(f'Você ganhou {4*dindin} edinhos!!')
            else:
                await update_bank(ctx.author,-1*dindin)
                await ctx.reply(f'Você perdeu {dindin} edinhos')

    @cog_ext.cog_slash(
        name='ccap', 
        description='Aposte seus edinhos no cara ou coroa podendo duplicar os seus edinhos',
        options = [
            create_option(
                name = 'edinhos',
                description = 'Selecione a quantia a apostar',
                option_type = 4,
                required = True
            ),
            create_option(
                name = 'escolha',
                description = 'escolha cara ou coroa',
                option_type = 3,
                required = True,
                choices = [
                    'cara','coroa'
                ]
            )
        ]
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _Caraoucoroaap(self, ctx:SlashContext, edinhos = int, escolha = None):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.send('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return
            
            bal = collection.find_one({"_id": ctx.author.id})

            dindin = int(edinhos)

            if dindin > bal["Edinhos"]:
                await ctx.reply(f'Você não tem dinheiro suficiente para apostar')
                return
            elif dindin < 0:
                await ctx.reply(f'A quantia deve ser positiva')
                return

            random1 = random.choice(['cara', 'coroa'])

            if random1 == escolha:
                await ctx.reply(f'Caiu {escolha}\nParabens, você ganhou {dindin*2} edinhos')
                await update_bank(ctx.author, + dindin*2)
            elif random1 != escolha:
                await ctx.reply(f'Caiu {random1}\nSad, você perdeu {dindin} edinhos')
                await update_bank(ctx.author, - dindin)

    @cog_ext.cog_slash(
        name = 'EdinhosTop',
        description = 'Mostra as pessoas mais ricas do server'
    )
    @commands.cooldown(1,5, commands.BucketType.user)
    async def _edinhostop(self, ctx:SlashContext):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.send('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return
            
            rankings = collection.find().sort("Edinhos",-1)
            i=1
            embed = discord.Embed(title = f"***Top 5 mais ricos***")
            for x in rankings:
                user_xp = x["Edinhos"]

                embed.add_field(name=f"{i}: {x['Nome']}", value=f"{user_xp}", inline=False)
                if i == 5:
                    break
                else:
                    i += 1
            embed.set_footer(text=f"{ctx.guild}", icon_url=f"{ctx.guild.icon_url}")
            await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name = 'inventario',
        description = 'Mostra seu inventario'
    )
    @commands.cooldown(1,5, commands.BucketType.user)
    async def _inv(self, ctx:SlashContext):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.send('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return
            
            await open_inv(ctx.author)
            await reload_inv(ctx.author)
            inv = collection2.find_one({"_id": ctx.author.id})

            embed = discord.Embed(
            title = 'Inventario',
            description = 
            f'''
            Picareta ferro {inv['picareta ferro']}
            Picareta de ouro {inv['picareta ouro']}
            Picareta de diamante {inv['picareta diamante']}
            Carro {inv['carro']}
            Arma {inv['arma']}
            Diamante {inv['diamante']}
            Ouro {inv['ouro']}
            Anel de casamento {inv['anel casamento']}
            Ferro {inv['ferro']}
            Madeira {inv['madeira']}
            Computador {inv['computador']}
            ''')
            await ctx.send(embed = embed)

    @cog_ext.cog_slash(
        name = 'Shop',
        description = 'Mercado de itens',
        options = [
            create_option(
                name = 'opção',
                description = 'Escolha uma opção',
                required = False,
                option_type = 3,
                choices = ['None','Buy','Sell']
            ),
            create_option(
                name = 'quantidade',
                description = 'Escolha quantos itens quer comprar',
                required = False,
                option_type = 4
            ),
            create_option(
                name = 'item',
                description = 'Escolha o item que deseja comprar',
                required = False,
                option_type = 3,
            )
        ]
    )
    @commands.cooldown(1,5, commands.BucketType.user)
    async def _Shop(self, ctx:SlashContext, opção = None, quantidade = int, *,item = None):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.send('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return
            
            embed = discord.Embed(title = 'Mercado')

            await open_inv(ctx.author)

            if opção == None:
                for i in shop:
                    name = i["Nome"]
                    compra = i["compra"]
                    venda = i["Venda"]
                    embed.add_field(name = name, value = f'Compra {compra}\n Venda {venda}')

                await ctx.send(embed = embed)
            elif opção == 'Buy':
                item_name = item.capitalize()

                await open_inv(ctx.author)

                for it in shop:
                    name = it["Nome"]
                    if name == item_name:
                        price = it["compra"]
                        break

                cost = price*quantidade

                bal = collection.find_one({"_id": ctx.author.id})

                if bal['Edinhos'] < cost:
                    await ctx.send('Você não tem edinhos suficientes')
                else:
                
                    q = None
                    if quantidade == 1:
                        q = 'unidade'
                    elif quantidade > 1:
                        q = 'unidades'

                    await ctx.send(f'Você comprou {quantidade} {q} de {item} por {cost} edinhos')
                    await update_bank(ctx.author, - cost)
                    await update_inv(ctx.author, item_name, quantidade)
            elif opção == 'Sell':
                item_name = item.capitalize()
                item_name2 = item.lower()

                await open_inv(ctx.author)

                for it in shop:
                    name = it["Nome"]
                    if name == item_name:
                        price = it["Venda"]
                        break

                cost = price*quantidade

                bal = collection2.find_one({"_id": ctx.author.id})

                if bal[f'{item_name2}'] < 1:
                    await ctx.send('Você não tem esse item para vender')
                else:
                
                    q = None
                    if quantidade == 1:
                        q = 'unidade'
                    elif quantidade > 1:
                        q = 'unidades'

                    await ctx.send(f'Você vendeu {quantidade} {q} de {item} por {cost} edinhos')
                    await update_bank(ctx.author, + cost)
                    await update_inv(ctx.author, item_name, - quantidade)
        

    @cog_ext.cog_slash(
        name = 'Minerar',
        description = 'Minera, tem chance de vir minerios'
    )
    @commands.cooldown(20,1800, commands.BucketType.user)
    async def _minerar(self, ctx:SlashContext, *,picareta = None):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.send('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return
            
            await open_inv(ctx.author)

            if picareta == None:
                picareta = 'picareta ferro'

            b1 = collection2.find_one({"_id": ctx.author.id})

            if b1[f'{picareta}'] < 1:
                await ctx.send(f'Você não tem {picareta}')
                return

            r1 = random.choice(['none','none1','none2', 'none3', 'none4', 'none5','none','none1','none2', 'none3', 'none4', 'none5', 'dima', 'ouro', 'ferro','ferro','ferro'])
            r2 = random.randint(1,5)
            r3 = random.randint(200,500)
            r4 = random.randint(1,10)

            q = None
            if r2 == 1:
                q = ''
            elif r2 > 1:
                q = 's'

            if picareta == 'picareta ferro':
                if r4 == 3 or 5:
                    await ctx.send('Sad, sua picareta de ferro quebrou')
                    await update_inv(ctx.author, 'picareta ferro', - 1)
                    return
            elif picareta == 'picareta ouro' :
                if r4 == 7 or 10:
                    await ctx.send('Sad, sua picareta de ouro quebrou')
                    await update_inv(ctx.author, 'picareta ouro', - 1)
                    return

            if r1 == 'ouro':
                await ctx.send(f'Parabens, você achou 1 ouro')
                await update_inv(ctx.author, 'ouro', 1)
                return
            elif r1 == 'dima':
                await ctx.send(f'Parabens, você achou 1 diamante')
                await update_inv(ctx.author, 'diamante', 1)
                return
            elif r1 == 'ferro':
                await ctx.send(f'Parabens, você achou {r2} ferro{q}')
                await update_inv(ctx.author, 'ferro', r2)
                return
            elif r1 == 'none' or 'none1' or 'none2' or 'none3' or 'none4' or 'none5':
                await ctx.send(f'Você não achou nada mas ganhou {r3} edinhos')
                await update_bank(ctx.author,r3)
                return
        
    @cog_ext.cog_slash(
        name = 'Craft',
        description = 'Craft de itens',
        options = [
            create_option(
                name = 'opção',
                description = 'Escolha oq fazer',
                required = False,
                option_type = 3,
                choices = ['None', 'craftar']
            ),
            create_option(
                name = 'craft',
                description = 'Escolha oq fazer',
                required = False,
                option_type = 3,
                choices = ['picareta diamante','picareta ferro','picareta ouro']
            )
        ]
    )
    @commands.cooldown(1,5, commands.BucketType.user)
    async def _craft(self, ctx:SlashContext, opção = None, *, craft = None):
            rand = random.randint(0,2)
            if rand == 1:
                await ctx.send('Sabia que Me manter está ficando dificil?\n que tal me ajudar doando algo?')
            elif ctx.author.id == banip:
                return
            

            if opção == None:
                e = discord.Embed(title = 'Crafts')

                for i in crafts:
                    name = i["Nome"]
                    compra = i["1"]
                    venda = i["2"]
                    e.add_field(name = name, value = f' {compra}\n {venda}')

                await ctx.send(embed = e)
            elif opção == 'craftar':
                item_ = craft.lower()
                b1 = collection2.find_one({"_id": ctx.author.id})

                if item_ == 'picareta diamante':
                    if b1['madeira'] < 1:
                        await ctx.send('Você não tem madeira suficiente')
                        return
                    elif b1['diamante'] < 3:
                        await ctx.send('Você não tem diamante suficiente')
                        return
                    else:
                        await update_inv(ctx.author, 'madeira', - 1)
                        await update_inv(ctx.author, 'diamante', -3)
                        await update_inv(ctx.author, 'picareta diamante', 1)
                        await ctx.send('Picareta diamante craftada com sucesso')
                
                elif item_ == 'picareta ferro':
                    if b1['madeira'] < 1:
                        await ctx.send('Você não tem madeira suficiente')
                        return
                    elif b1['ferro'] < 3:
                        await ctx.send('Você não tem ferro suficiente')
                        return
                    else:
                        await update_inv(ctx.author, 'madeira', - 1)
                        await update_inv(ctx.author, 'ferro', -3)
                        await update_inv(ctx.author, 'picareta ferro', 1)
                        await ctx.send('Picareta ferro craftada com sucesso')
            
                elif item_ == 'picareta ouro':
                    if b1['madeira'] < 1:
                        await ctx.send('Você não tem madeira suficiente')
                        return
                    elif b1['ouro'] < 3:
                        await ctx.send('Você não tem ouro suficiente')
                        return
                    else:
                        await update_inv(ctx.author, 'madeira', - 1)
                        await update_inv(ctx.author, 'ouro', -3)
                        await update_inv(ctx.author, 'picareta ouro', 1)
                        await ctx.send('Picareta ouro craftada com sucesso')

    @_beg.error
    async def beg_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            cd = round(error.retry_after)
        if cd == 0:
            cd = 1
        await ctx.reply(f'Você precisa esperar {better_time(cd)} para  usar esse comando de novo')

    @_Carteira.error
    async def beg_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            cd = round(error.retry_after)
        if cd == 0:
            cd = 1
        await ctx.reply(f'Você precisa esperar {better_time(cd)} para  usar esse comando de novo')

        if isinstance(error, commands.MemberNotFound):

            await ctx.reply('Não encontrei esse membro no server')

    @_edinhostop.error
    async def beg_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            cd = round(error.retry_after)
        if cd == 0:
            cd = 1
        await ctx.reply(f'Você precisa esperar {better_time(cd)} para  usar esse comando de novo')

    @_loteria.error
    async def beg_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            cd = round(error.retry_after)
        if cd == 0:
            cd = 1
        await ctx.reply(f'Você precisa esperar {better_time(cd)} para  usar esse comando de novo')

    @_Transferir.error
    async def beg_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            cd = round(error.retry_after)
        if cd == 0:
            cd = 1
        await ctx.reply(f'Você precisa esperar {better_time(cd)} para  usar esse comando de novo')

        if isinstance(error, commands.MemberNotFound):

            await ctx.reply('Não encontrei esse membro no server')

    @_Caraoucoroaap.error
    async def beg_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            cd = round(error.retry_after)
        if cd == 0:
            cd = 1
        await ctx.reply(f'Você precisa esperar {better_time(cd)} para  usar esse comando de novo')

def setup(bot):
    bot.add_cog(_Ec(bot))