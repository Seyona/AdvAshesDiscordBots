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
    
    for emoji in guild.emojis:
        if emoji.name == 'seyonirl':
            break

    await channel.purge()
    await channel.send("bitches")
    msg = channel.last_message
    await msg.pin()
    await msg.add_reaction(emoji)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    #add some checks to what channel it is in....

    user = await client.fetch_user(message.author.id)
    await message.channel.send(f'Hi {user}')


client.run(TOKEN)
