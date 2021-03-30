import discord
import random
import math
import ast

from discord.ext import commands
from datetime import date

def BetBot(_bot):
    PLAYERBETS='PlayersBet'
    CANBET = 'CanBet'
    BOTMESSAGE = 'LastRatioMessage'
    WINNER = 'Winner'
    GUILDRAKE=0.10
    MAXBET = 10000000 
    MINBET = 100000
    bot=_bot
    bets = {}
    REGISTEROPEN='RegisterOpen'
    tournament = {}

    @bot.command(name='create_tournament')
    @commands.has_role('Krupier')
    async def create_tournament(ctx, date:str = date.today().strftime("%d_%m_%Y")):
        channel_name=f'tournament_{date}'
        existing_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        if existing_channel is None:
            roles = map_permission_on_self(ctx.guild)

            tournament[channel_name]={REGISTEROPEN:True}

            bets[channel_name]={
                CANBET:False,
                PLAYERBETS:{},
                BOTMESSAGE:''}
            channel = await create_channel_and_remove_command(ctx,channel_name,roles)
            await channel.edit(topic='Rejestracja otwarta. By się zapisać do trunieju napisz !!singin')
            await course_rate(channel)

    async def create_channel_and_remove_command(ctx,channel_name:str,roles):
        channel = await ctx.guild.create_text_channel(channel_name, overwrites=roles)
        await ctx.message.delete()
        await ctx.send(f"Utworzono kanał {channel.mention}")
        return channel

    @bot.command(name='start')
    @commands.has_role('Krupier')
    async def start_tournament(ctx):
        channel_name = ctx.channel.name
        bets[channel_name][CANBET]=True
        if channel_name.startswith('tournament_'):
            tournament[channel_name][REGISTEROPEN]=False
            await ctx.channel.edit(topic= 'Rejestracja zamknięta!')
        await ctx.send("Moża betować")
        await course_rate(ctx.channel) 

    @bot.command(name='singin')
    async def singin(ctx):
        nickname=ctx.author.display_name.lower().strip().replace(' ','')
        playerId=ctx.author.id;
        channel_name = ctx.channel.name
        if channel_name.startswith('tournament_'):
            if channel_name in tournament and tournament[channel_name][REGISTEROPEN]:
                if playerId not in tournament[channel_name]:
                    tournament[channel_name].update({playerId:nickname})
                    await ctx.send(f"Dodano do turnieju {ctx.author.mention}")
                    bets[channel_name].update({nickname:0})
                else:
                    await ctx.send(f"Jesteś już zapisany do turnieju {ctx.author.mention}")  
            else:
                await ctx.send(f"Rejestracja zamknięta!")  
        await course_rate(ctx.channel)

    @bot.command(name='add')
    @commands.has_role('Krupier')
    async def add_persons(ctx, *nicknames):
        if len(list(nicknames))==0:
            return
        channel_name = ctx.channel.name
        for nickname in list(nicknames):
            if channel_name in bets:
                if nickname.lower() not in bets[channel_name]:
                    bets[channel_name].update({nickname.lower():0})
                    print(bets[channel_name])
                else:
                    await ctx.send(f"{nickname} już jest już zapisany!")
        await ctx.send(f"Dodano do turnieju {', '.join(nicknames)}")        
        await course_rate(ctx.channel)     

    @bot.command(name='remove')
    @commands.has_role('Krupier')
    async def remove_persons(ctx, *nicknames):
        channel_name = ctx.channel.name
        if len(list(nicknames))==0:
            return
        for nickname in list(nicknames):
            if channel_name in bets:
                if nickname.lower() in bets[channel_name]:
                    bets[channel_name].pop(nickname.lower())
                    print(bets[channel_name])
                else:
                    await ctx.send(f"{nickname} nie jest zapisany!")
        await ctx.send(f"Usunięto z turnieju {', '.join(nicknames)}")        
        await course_rate(ctx.channel)     
        

    def map_permission_on_self(guild):
        perms = discord.PermissionOverwrite(read_messages=True)
        dic={guild.default_role:discord.PermissionOverwrite(read_messages=False)}
        for rola in guild.me.roles:
            if rola != guild.default_role:
                dic[rola]=discord.PermissionOverwrite(read_messages=True)
        return dic

    @bot.command(name='start_bets')
    @commands.has_role('Krupier')
    async def create_channel(ctx, player1:str, player2:str, canBet:bool=True):
        guild = ctx.guild

        roles = map_permission_on_self(guild)

        channel_name = 'bets_'+player1+'_vs_'+player2
        channel_name = channel_name.lower()
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel is None:
            print(f'Creating a new channel: {channel_name}')
            bets[channel_name]={
                CANBET:canBet,
                PLAYERBETS:{},
                BOTMESSAGE:'',
                player1.lower():0,
                player2.lower():0
            }
            print(bets)
            channel = await create_channel_and_remove_command(ctx,channel_name,roles)
            await course_rate(channel)   
        else:
            await ctx.send(f"Bets for this fight exits")

    @bot.command(name="stop_bets")
    @commands.has_role('Krupier')
    async def stop_bets(ctx):
        print("STOP BETING")
        bets[ctx.channel.name][CANBET]=False
        await ctx.send("Bets has stopped")
        await course_rate(ctx.channel)

    @bot.command(name="winner")
    @commands.has_role('Krupier')
    async def calculate_winners(ctx,player:str):
        player = player.lower()
        channel = ctx.channel.name
        keys = list(bets[channel].keys())

        fullPot = get_full_pot(channel)
        if fullPot==0:
            return
        betted = bets[channel][player]
        bets[channel][WINNER]=player;
        winnerRate=calculate_ratio(betted,fullPot)

        for better in bets[channel][PLAYERBETS]:
            if player in bets[channel][PLAYERBETS][better]:
                await ctx.send(f'<@!{better}> wygrałeś {math.floor(winnerRate*bets[channel][PLAYERBETS][better].get(player) * (1-GUILDRAKE))} silvera')

    def get_full_pot(channel: str):
        fullpot = 0
        keys = list(bets[channel].keys())
        for i in range(3,len(keys)):
            fullpot += bets[channel][keys[i]]
        return fullpot

    def calculate_ratio(betted:int,fullPot:int):
        ratio=1
        if betted==0:
            ratio = fullPot
        elif (fullPot-betted) != 0:
            ratio += 1/(betted/(fullPot-betted))
        return round(ratio,2)


    async def course_rate(channel):
        channel_name = channel.name
        keys = list(bets[channel_name].keys())
        embed=discord.Embed(title=f'DUMMY', color=0xd00606)
        if channel_name.startswith('tournament_'):
            if tournament[channel_name][REGISTEROPEN]:
                embed = discord.Embed(title=f'TOURNAMENT', description="By się zarejestrować napisz !!singin", color=0xd00606)
            else:
                embed = discord.Embed(title=f'TOURNAMENT', description="By zbetować napisz !!bet {nickname} {ilość silvera}", color=0xd00606)
        else:
            title = ""
            for i in range(3,len(keys)):
                title += keys[i]
                if (i<len(keys)-1):
                    title+=" VS "
            embed=discord.Embed(title=title, description="By zbetować napisz !!bet {nickname} {ilość silvera}", color=0xd00606)

        fullPot = get_full_pot(channel_name)
        
        for i in range(3,len(keys)):
            ratio=1
            if fullPot!=0:
                betted = bets[channel_name][keys[i]]
                ratio=calculate_ratio(betted,fullPot)
            embed.add_field(name=f'Kurs na {keys[i]}', value=ratio, inline=True)

        if bets[channel_name][BOTMESSAGE]!='':
            msg = await channel.fetch_message(bets[channel_name][BOTMESSAGE])
            await msg.delete()

        msg = await channel.send(embed=embed)
        bets[channel_name][BOTMESSAGE] = msg.id;


    @bot.command(name='delete')
    @commands.has_role('Krupier')
    async def delete_channel(ctx):
        channel_name = ctx.channel.name
        if channel_name.startswith('tournament_'):
            tournament.pop(channel_name)
        if channel_name in bets:
            bets.pop(channel_name)
            await ctx.channel.delete()

    @bot.command(name='bet')
    async def bet(ctx, player:str, bet_value:int):
        player=player.lower()
        if bet_value<MINBET:
            await ctx.send(f'Minimalny bet to {MINBET} silvera.')
            await course_rate(ctx.channel)
            return

        if bet_value>MAXBET:
            await ctx.send(f'Maksymalny bet to {MAXBET}.')
            await course_rate(ctx.channel)
            return

        better = ctx.author.id
        channel = ctx.channel.name
        if  bets[channel][CANBET] is False:
            await ctx.send(f'Betowanie jest zamknięte.')
            return
        if better in bets[channel][PLAYERBETS]:
            await ctx.send(f'Już betowałeś.')
        else:
            if player in bets[channel]:
                bets[channel][player]+=bet_value
                bets[channel][PLAYERBETS][better]={player:bet_value}
                print(bets)
                await ctx.send(f'<@!{better}> postawiłeś na {player} {bet_value} silvera')
            else:
                await ctx.send('Taki gracz nie walczy.')
        await course_rate(ctx.channel)

    @bot.command(name='summary')
    @commands.has_role('Krupier')
    async def create_tournament(ctx):
        suma = {}
        sumaa = 0
        for bet in bets:
            betlist = bets[bet][PLAYERBETS]
            for better in betlist:
                obstawa = list(betlist[better].keys())
                if better in suma:
                    suma[better]+=betlist[better][obstawa[0]]
                else:
                    suma[better]=betlist[better][obstawa[0]]
        for guildBetter in suma:
            sumaa += suma[guildBetter]
            await ctx.send(f'<@!{guildBetter}> {suma[guildBetter]} Sprawdź czy wpłaciłeś wszystkie bety, jak nie dostaniesz fine 2x tego co obstawiłeś') 
        await ctx.send(f'Dzisiejsza pula wszystkich betów to {sumaa}') 
        winnerList = {}
        for battleName in bets:
            battle = bets[battle]
            winner = battle[WINNER]
            for better in battle[PLAYERBETS]:
                if battle[PLAYERBETS][better]==winner:
                    if better in winnerList:
                        winnerList[better]=battle[PLAYERBETS][better]
                    else:
                        winnerList[better]+=battle[PLAYERBETS][better]
        for winner in winnerList:
            await ctx.send(f'<@!{winner}> Wygrałeś {winnerList[winner]} do odebrania u Liderów gildii <@!216692474372947969> <@!95492996933353472> <@!221567583596314624>')


    @bot.command(name='save')
    @commands.has_role('Krupier')
    async def save(ctx):
        f = open("betDict.txt", "w+")
        f.write(str(bets))
        f.close()

        f = open("tournamentDict.txt", "w+")
        f.write(str(tournament))
        f.close()

    @bot.event 
    async def on_ready():
        file = open("bety.txt", "r+")
        contents = file.read()
        if contents != '':
            bets = ast.literal_eval(contents)
        file.close()

        file = open("tournamentDict.txt", "r+")
        contents = file.read()
        if contents != '':
            tournament = ast.literal_eval(contents)
        file.close()