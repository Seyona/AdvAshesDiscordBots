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

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord')


client.run(TOKEN)
