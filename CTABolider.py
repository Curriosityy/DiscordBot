import discord
import random
import math
import ast
import asyncio
import pickle

from datetime import datetime
from datetime import time

from discord.utils import get
from enum import Enum

from discord.ext import commands

nl = '\n'
plToBool = {"tak": True, "nie": False}
boolToPL = {True: "Tak", False: "Nie"}

class SetType(Enum):
    NOTYPE = 0
    TANK = 1
    SUPPORT = 2
    HEAL = 3
    MDPS = 4
    RDPS = 5

class Hammer(Enum):
    NOTYPE = 0
    Yes = 1
    No = 2

class Status(Enum):
    NOTYPE = 0
    MASSING = 1
    ONGOING = 2
    DONE = 3

class CtaComposition(Enum):
    NOTYPE = 0
    NEEDMORE = 1
    GOOD = 2
    TOOMUCH = 3

class SetComposition(Enum):
    NOTYPE = 0
    NEED = 1
    GOOD = 2

class Set:
    name: str
    type: SetType
    emoji: discord.Emoji
    counter: int

    def __init__(self, setName: str, setType: SetType, emoji: discord.Emoji):
        self.name = setName
        self.type = setType
        self.emoji = emoji
        self.counter = 0

class Player:
    nickName: str
    pickedSet: Set
    discordCode: int
    emoji: discord.Emoji
    removedByBot: bool

    def __init__(self, nick: str, pset: Set, dCode: int, emoji: discord.Emoji):
        self.nickName = nick
        self.pickedSet = pset
        self.discordCode = dCode
        self.emoji = emoji
        self.removedByBot = False

    def ChaneSet(self, set: Set):
        self.pickedSet = set

    def GetMention(self):
        return f"<@{self.discordCode}>"

colorByStatus = {Status.MASSING: 0x29757f,
                 Status.ONGOING: 0x04ff00, Status.DONE: 0xff0f4b}

def GetSetsByType(sets: [Set], type: SetType):
    value = []

    for set in sets:
        if set.type == type:
            value.append(set)

    return value

def PrintSets(sets: [Set], players:[Player]):
    value = f""

    if len(sets) == 0:
        value = f"Brak"

    for set in sets:
        set2: Set = set
        value += f"{nl}{set2.name} {set2.emoji} {sum(1 for player in players if player.pickedSet.name is set2.name)}"

    return value

class CTA:
    players: {int: Player}
    hammers: bool
    status: Status
    ctaTimer: datetime.time
    guildID: int
    channelID: int
    messageID: int
    counter: [int]
    sets: [Set]

    def __init__(self, needHammers: bool, timerH: int, timerM: int, guild: int, channel: int, sets: [Set]):
        self.hammers = needHammers
        self.ctaTimer = time(timerH, timerM, 0)
        self.players = {}
        self.status = Status.MASSING
        self.guildID = guild
        self.channelID = channel
        self.sets = sets

    def AddPlayers(self, playerToAdd: Player):
        self.players[playerToAdd.discordCode] = playerToAdd

    def RemovePlayer(self, playerToRemove: Player):
        if playerToRemove.removedByBot:
            playerToRemove = False
        else:
            del self.players[playerToRemove.discordCode]

    def GetEmbed(self):
        embed = discord.Embed(title=f"CTA {self.status.name} {self.ctaTimer} Młotki: {boolToPL[self.hammers]}",
                              description="Bot do rejestracji na CTA! Wybieramy broń, jaką idziemy.", color=colorByStatus[self.status])
        embed.add_field(name="Obecność",
                        value=f"LICZBA : {len(self.players)}", inline=True)
        embed.add_field(name="Tu będzie status kompozycji",
                        value="------------------", inline=False)
        embed.add_field(
            name="Tank", value=f"LICZBA : {sum(1 for player in self.players.values() if player.pickedSet.type is SetType.TANK)}", inline=True)
        embed.add_field(
            name="Sety", value=f"{PrintSets(GetSetsByType(self.sets,SetType.TANK), self.players.values())}", inline=True)
        embed.add_field(name="Tu będzie status kompozycji",
                        value="------------------", inline=False)
        embed.add_field(
            name="Heal", value=f"LICZBA : {sum(1 for player in self.players.values() if player.pickedSet.type is SetType.HEAL)}", inline=True)
        embed.add_field(
            name="Sety", value=f"{PrintSets(GetSetsByType(self.sets,SetType.HEAL), self.players.values())}", inline=True)
        embed.add_field(name="Tu będzie status kompozycji",
                        value="------------------", inline=False)
        embed.add_field(
            name="Support", value=f"LICZBA : {sum(1 for player in self.players.values() if player.pickedSet.type is SetType.SUPPORT)}", inline=True)
        embed.add_field(
            name="Sety", value=f"{PrintSets(GetSetsByType(self.sets,SetType.SUPPORT), self.players.values())}", inline=True)
        embed.add_field(name="Tu będzie status kompozycji",
                        value="------------------", inline=False)
        embed.add_field(
            name="Range", value=f"LICZBA : {sum(1 for player in self.players.values() if player.pickedSet.type is SetType.RDPS)}", inline=True)
        embed.add_field(
            name="Sety", value=f"{PrintSets(GetSetsByType(self.sets,SetType.RDPS), self.players.values())}", inline=True)
        embed.add_field(name="Tu będzie status kompozycji",
                        value="------------------", inline=False)
        embed.add_field(
            name="Melee", value=f"LICZBA : {sum(1 for player in self.players.values() if player.pickedSet.type is SetType.MDPS)}", inline=True)
        embed.add_field(
            name="Sety", value=f"{PrintSets(GetSetsByType(self.sets,SetType.MDPS), self.players.values())}", inline=True)
        embed.set_footer(text="Developer MSc Curriosityy #8105")
        return embed

    def GetPlayersMention(self):
        value = ""

        for player in self.players.values():
            value += player.GetMention()+" "

        return value

def CTABolider(_bot):
    bot: discord.ext.commands.Bot = _bot
    ctas = {}
    closed = {}
    sets: [Set] = []
    mainChannel = {566961779163267115: 804014484023672933}
    fetchedMessages = {}
    rolesIDs = [573968475551432705, 706268409830309990,
                566961993471361042, 591402939063730184]
    closeCTAReactionName = "🔴"

    @bot.event
    async def on_message(message):

        await bot.process_commands(message)

    async def my_background_task():
        await bot.wait_until_ready()
        while not bot._closed:
            for cta in ctas.values():
                cta: CTA

                if cta.status != Status.DONE:

                    if cta.messageID not in fetchedMessages:
                        print("Fetching message")
                        message = await bot.get_guild(cta.guildID).get_channel(cta.channelID).fetch_message(cta.messageID)
                    else:
                        message = fetchedMessages[cta.messageID]

                    if cta.status == Status.MASSING:
                        currentTime = datetime.now().time()

                        if currentTime >= cta.ctaTimer:
                            cta.status = Status.ONGOING

                    await message.edit(embed=cta.GetEmbed())

            await asyncio.sleep(3)
    
    def save():
        a_file = open("sets.pkl", "wb")
        pickle.dump(sets, a_file)
        a_file.close()
        print("SAVED")

    def load():
        with open("sets.pkl", "rb") as a_file:
            loaded = pickle.load(a_file)
            a_file.close()

            for set in loaded:
                sets.append(set)

            print(f"LOADED {sets}")
    
    load()
    bot.loop.create_task(my_background_task())

    @bot.command(name='createCTA', help='!!createCTA <Młotki> <Timer>')
    @commands.has_any_role(573968475551432705, 706268409830309990, 566961993471361042, 591402939063730184)
    async def createCTA(ctx, needHammer: str, TimerH: int, TimerM: int = 0):
        if needHammer not in plToBool:
            await ctx.send(f"Error")
            return

        if TimerH < 0 or TimerH > 24:
            return

        if TimerM < 0 or TimerM > 60:
            return

        async with ctx.typing():
            cta = CTA(plToBool[needHammer], TimerH, TimerM,
                      ctx.guild.id, ctx.channel.id, sets)
            await ctx.send("@everyone")
            ctaMessage = await ctx.send(embed=cta.GetEmbed())
            cta.messageID = ctaMessage.id
            ctas[ctaMessage.id] = cta
            fetchedMessages[ctaMessage.id]=ctaMessage;
            for set in sets:
                await ctaMessage.add_reaction(set.emoji)

            await ctaMessage.add_reaction(closeCTAReactionName)

    @bot.command(name='AddSet')
    @commands.has_any_role(573968475551432705, 706268409830309990, 566961993471361042, 591402939063730184)
    async def AddSet(ctx, setName: str, type: str, emoji):

        if not HasSet(setName):
            sets.append(Set(setName, SetType[type.upper()], emoji))
            await ctx.send(f"Set added {setName}")
        else:
            await ctx.send(f"Set exist {setName}")
        
        save()

    @bot.command(name='RemoveSet')
    @commands.has_any_role(573968475551432705, 706268409830309990, 566961993471361042, 591402939063730184)
    async def RemoveSet(ctx, setName: str):

        if HasSet(setName):
            filters =  list(filter(lambda x: x.name == setName, sets))
            sets.remove(filters[0])
            await ctx.send(f"Set removed {setName}")
        else:
            await ctx.send(f"Set not exist {setName}")
        
        save()

    @bot.command(name='GenerateAttendance')
    @commands.has_any_role(573968475551432705, 706268409830309990, 566961993471361042, 591402939063730184)
    async def GenerateAttendance(ctx, ciufaIndex: int, ctaIndex: int):
        if ctaIndex in ctas:
            user = ctx.author
            message = f"$addPlayers {str(ciufaIndex)} {ctas[ctaIndex].GetPlayersMention()}"
            await user.send(message)

    @bot.event
    async def on_reaction_add(reaction, user):
        if user.bot:
            return

        if reaction.message.id in ctas:
            cta: CTA = ctas[reaction.message.id]

            if cta.status is cta.status.DONE:
                return

            if reaction.emoji == closeCTAReactionName and HaveRole(user.roles):
                cta.status = Status.DONE
                message = await bot.get_guild(cta.guildID).get_channel(cta.channelID).fetch_message(cta.messageID)
                await message.edit(embed=cta.GetEmbed())
            else:
                if reaction.emoji not in [set.emoji for set in sets]:
                    return
                if user.id in cta.players:
                    await UserClickedDiferentEmote(reaction, cta.players[user.id], cta, user)
                else:
                    filters =  list(filter(lambda x: x.emoji == reaction.emoji, sets))
                    cta.AddPlayers(
                        Player(user.name, filters[0], user.id, reaction.emoji))

    @bot.event
    async def on_raw_reaction_remove(payload):
        if payload.message_id in ctas:
            cta: CTA = ctas[payload.message_id]
            if cta.status is not Status.DONE:
                if payload.user_id in cta.players:
                    cta.RemovePlayer(cta.players[payload.user_id])

    def HaveRole(roles: []):
        value = False

        for role in roles:

            if role.id in rolesIDs:
                value = True
                break

            if value:
                break

        return value

    async def UserClickedDiferentEmote(reaction: discord.Reaction, user: Player, cta: CTA, member: discord.User):
        prevoiosEmoji = user.emoji
        user.emoji = reaction.emoji
        filters =  list(filter(lambda x: x.emoji == reaction.emoji, sets))
        user.pickedSet = filters[0]
        user.removedByBot = True

        await reaction.message.remove_reaction(prevoiosEmoji, member)

    def HasSet(setName: str):
        hasSet = False

        for set in sets:
            if set.name == setName:
                hasSet = True
                break

        return hasSet