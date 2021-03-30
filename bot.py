import os
import discord


from betbot import BetBot
from CTABolider import CTABolider

from discord.ext import commands
from dotenv import load_dotenv

# TYLKO DLA RANGI ALBION i SOJUSZNIK

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!!')


@bot.event
async def on_ready():
    print(
        f'{bot.user} is connected to the following guild:\n'
    )
    for guild in bot.guilds:
        print(f'{guild.name}(id: {guild.id})\n')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send(f'You do not have the correct role for this command.')
    else:
        await ctx.send(error)

CTABolider(bot)
bot.run(TOKEN)
