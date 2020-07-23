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

#@client.event
#async def on_memeber_join(member):

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user = await client.fetch_user(message.author.id)
    await message.channel.send(f'Hi {user}')


client.run(TOKEN)
