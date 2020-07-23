# Discord requirements
import discord
import asyncio
import datetime
import os
import sys
#End Discord requirements

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv("DISCORD_GUILD")

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord')
    
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    for channel in guild.text_channels:
        if channel == "botfuckery":
            break
    
    await channel.purge()
    await channel.send("bitches")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user = await client.fetch_user(message.author.id)
    await message.channel.send(f'Hi {user}')


client.run(TOKEN)
