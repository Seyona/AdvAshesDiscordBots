# Discord requirements
import discord
import asyncio
import datetime
import os
import sys
#End Discord requirements

import json
import time
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv("DISCORD_GUILD")

client = discord.Client()

discordEmojis = []
primaryClassMsgId = 0
secondaryClassMsgId = 0
isReady = False

with open('classes.json') as json_file:
	classData = json.load(json_file)
	classEmojisNames = classData.keys()

@client.event
async def on_ready():
	#global calls so we can modify these variables
	global primaryClassMsgId
	global secondaryClassMsgId
	global discordEmojis

	print(f'{client.user} has connected to Discord')
	
	for guild in client.guilds:
		if guild.name == GUILD:
			break

	for channel in guild.text_channels:
		if channel.name == "class-registration":
			break

	await channel.purge()

	primaryMsg = await channel.send("Pick yo class fool")
	secondaryMsg = await channel.send("Pick yo Second class fool")

	primaryClassMsgId = primaryMsg.id
	secondaryClassMsgId = secondaryMsg.id

	for emoji in guild.emojis:
		if emoji.name in classEmojisNames:
			discordEmojis.append(emoji)
			await primaryMsg.add_reaction(emoji)
			await secondaryMsg.add_reaction(emoji)
			if discordEmojis.count == 8: # 8 classes no more lookup required
				break
	
	time.sleep(0.5) # let the awaits finish up
	global isReady
	isReady = True

@client.event
async def on_reaction_add(reaction,user):
	if not isReady:
		return

	print(discordEmojis.count)
	print(discordEmojis[0])
	print(reaction.emoji)
	print(reaction.emoji.name)
	print(reaction.emoji not in discordEmojis)

	reactMsgId = reaction.message.id

	if (reaction.emoji not in discordEmojis):
		await reaction.message.remove_reaction(reaction.emoji, user)

	if reactMsgId == primaryClassMsgId:
		x =""
	elif reactMsgId == secondaryClassMsgId:
		x = ""

client.run(TOKEN)
