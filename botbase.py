# Discord requirements
import discord
import asyncio
import datetime
import os
import sys
#End Discord requirements

import json
import time

from asyncio import gather
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv("DISCORD_GUILD")

client = discord.Client()

discordEmojis = []
discordRoles = []
primaryClassMsgId = 0
secondaryClassMsgId = 0
isReady = False

with open('classes.json') as json_file:
	classData = json.load(json_file)
	classNames = classData.keys()

@client.event
async def on_ready():
	#global calls so we can modify these variables
	global primaryClassMsgId
	global secondaryClassMsgId
	global discordEmojis
	global isReady
	global discordRoles

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
		if emoji.name in classNames:
			discordEmojis.append(emoji)
			await gather(primaryMsg.add_reaction(emoji),secondaryMsg.add_reaction(emoji))

	for role in guild.roles:
		if role.name in classNames:
			discordRoles.append(role)

	isReady = True
	print("Setup complete")

@client.event
async def on_reaction_add(reaction,user):
	if not isReady or user.id == 735708593294147674:
		return

	reactMsgId = reaction.message.id

	if reactMsgId not in [primaryClassMsgId,secondaryClassMsgId]: #lock it to the channel the message are in
		return

	if (reaction.emoji not in discordEmojis):
		await reaction.message.remove_reaction(reaction.emoji, user)
		return

	# get requested role
	for role in discordRoles:
		if role.name == reaction.emoji.name:
			requestedRoleName = reaction.emoji.name
			roleConfirmMsg = await reaction.message.channel.send(f'<@{user.id}> You selected the {requestedRoleName}')
			break

	if reactMsgId == primaryClassMsgId:
		await user.remove_roles(discordRoles)
		await user.add_roles(requestedRoleName)

		time.sleep(1)
		await reaction.message.channel.delete_messages([roleConfirmMsg])
	elif reactMsgId == secondaryClassMsgId:
		x = ""

	await reaction.message.remove_reaction(reaction.emoji, user) #clean up
	
client.run(TOKEN)
