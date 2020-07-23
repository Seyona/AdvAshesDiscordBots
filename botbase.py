# Discord requirements
import discord
import asyncio
import datetime
import os
import sys
#End Discord requirements

import json
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv("DISCORD_GUILD")

client = discord.Client()

discordEmojis = []

with open('classes.json') as json_file:
	classData = json.load(json_file)
	classEmojisNames = classData.keys()

@client.event
async def on_ready():
	print(f'{client.user} has connected to Discord')
	
	for guild in client.guilds:
		if guild.name == GUILD:
			break

	for channel in guild.text_channels:
		if channel.name == "class-registration":
			break

	await channel.purge()
	await channel.send("Pick yo class fool")
	msg = channel.last_message

	for emoji in guild.emojis:
		if emoji.name in classEmojisNames:
			discordEmojis.append(emoji)
			await msg.add_reaction(emoji)
			if discordEmojis.count == 8: # 8 classes no more lookup required
				break


@client.event
async def on_message(message):
	if message.author == client.user:
		return
	#add some checks to what channel it is in....

	user = await client.fetch_user(message.author.id)
	await message.channel.send(f'Hi {user}')


client.run(TOKEN)
