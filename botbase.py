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
			requestedRole = role
			break

	if reactMsgId == primaryClassMsgId:
		# remove existing role
		for role in user.roles:
			if role.name in classNames:
				await user.remove_roles(role)

		await user.add_roles(requestedRole)

		time.sleep(1)
		await DeleteMessageFromReaction(reaction,roleConfirmMsg)

	elif reactMsgId == secondaryClassMsgId:
		#Get current role
		for role in user.roles:
			if role.name in classNames:
				currentRoleName = role.name
		
		selectedCombo = classData[currentRoleName][requestedRoleName]
		time.sleep(1)
		await DeleteMessageFromReaction(reaction,roleConfirmMsg)

		roleConfirmMsg = await reaction.message.channel.send(f'<@{user.id}> You are a {selectedCombo.capitalize()}?? HYPE')
		time.sleep(1)
		await  DeleteMessageFromReaction(reaction,roleConfirmMsg)
		# Gotta do google spreadsheet magic here....yeepie

	await reaction.message.remove_reaction(reaction.emoji, user) #clean up

async def DeleteMessageFromReaction(reaction, msg):
	await reaction.message.channel.delete_messages([msg])

client.run(TOKEN)
