#!/usr/local/bin/python3.8
# Discord requirements
import discord
import asyncio
import datetime
import os
import sys
#End Discord requirements

#Gsheet stuff
import gspread
#end Gsheet stuff

import json
import csv
import time
import argparse

from asyncio import gather
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv("DISCORD_GUILD")

client = discord.Client()

emojiWhiteList = []
primaryClassRoles = []
augmentClassRoles = []
msgIds = None
isReady = False
cleanBoot = False

summaryDict = {}

#initialize the Gsheet api
SPREADSHEET_ID = '1kTPhqosR0DRoVzccjOpFB2b2OmT-yxj6K4j_te_qBxg'
gc = gspread.service_account()
sheet = gc.open_by_key(SPREADSHEET_ID)
rosterSheet = sheet.worksheet("Roster")

# pull classes file into memory
with open('/repositories/AdvAshesDiscordBots/classes.json') as json_file:
	classData = json.load(json_file)
	classNames = classData.keys()
	augmentNames = [item for innerList in classData.values() for item in innerList.values()]

# pull ids into memory
with open('/repositories/AdvAshesDiscordBots/discordIds.json') as json_file:
	discordIds = json.load(json_file)

summStr    = f'❖ Summoner {discordIds["summoner"]}'
bardStr    = f'❖ Bard             {discordIds["bard"]}'
clericStr  = f'❖ Cleric           {discordIds["cleric"]}'
fighterStr = f'❖ Fighter         {discordIds["fighter"]}'
mageStr    = f'❖ Mage           {discordIds["mage"]}'
rangerStr  = f'❖ Ranger         {discordIds["ranger"]}'
rogueStr   = f'❖ Rogue          {discordIds["rogue"]}'
tankStr    = f'❖ Tank            {discordIds["tank"]}'

# On ready prep function
@client.event
async def on_ready():
	#global calls so we can modify these variables
	global msgIds
	global emojiWhiteList
	global isReady
	global primaryClassRoles
	global augmentClassRoles

	print(f'{client.user} has connected to Discord')
	
	for guild in client.guilds:
		if guild.name == GUILD:
			break

	for channel in guild.text_channels:
		if channel.name == "class-registration":
			break

	await channel.purge()

	await channel.send(f'Welcome to the guild! Before you can tagged up as a () You\'ll need to complete this form. It\'s pretty quick, just react to each message and once you\'re done you\'ll be entered into the guild!')

	cleanLine = "━━━━━━━━━━━━━━━◦❖◦━━━━━━━━━━━━━━━"
	classSelection = f"""
{bardStr}
{clericStr}
{fighterStr}
{mageStr}
{rangerStr}
{rogueStr}
{summStr}
{tankStr}
"""

	await channel.send(cleanLine)
	primaryMsg = await channel.send(f"What is your Primary class: {classSelection}")

	await channel.send(cleanLine)
	secondaryMsg = await channel.send(f'What is your Secondary class: {classSelection}')
	await channel.send(cleanLine)

	playStyleMsg = await channel.send(f'Select your Main playstyle (Select only 1): \n PVE: {discordIds["pve"]} \n PVP: {discordIds["pvp"]} \n Lifeskiller: {discordIds["lifeskiller"]} \n')
	await channel.send(cleanLine)

	accessMsg = await channel.send(f'Do you have any early access to the game?: \n \
	Alpha 1: {discordIds["alpha1"]} \n \
	Alpha 2: {discordIds["alpha2"]} \n \
	Beta 1: {discordIds["beta1"]} \n \
	Beta 2: {discordIds["beta2"]} \n \
	No Access {discordIds["noaccess"]}')
	await channel.send(cleanLine)

	msgIds = {
		"primaryClassMsgId": primaryMsg.id,
		"secondaryClassMsgId": secondaryMsg.id,
		"playStyleMsgId": playStyleMsg.id,
		"accessMsgId": accessMsg.id,
	}

	#construct a white list
	for emoji in guild.emojis:
		if emoji.name in classNames:
			emojiWhiteList.append(emoji)	
		elif emoji.name in discordIds.keys():
			emojiWhiteList.append(emoji)

	emojiWhiteList.sort(key= lambda x: x.name, reverse=False)

	for emoji in emojiWhiteList:
		if emoji.name in classNames:
			await gather(primaryMsg.add_reaction(emoji),secondaryMsg.add_reaction(emoji))

	for role in guild.roles:
		if role.name in classNames:
			primaryClassRoles.append(role)
		if role.name in augmentNames:
			augmentClassRoles.append(role)

	await gather(playStyleMsg.add_reaction(discordIds["pve"]),playStyleMsg.add_reaction(discordIds["pvp"]),playStyleMsg.add_reaction(discordIds["lifeskiller"]))
	
	await gather(accessMsg.add_reaction(discordIds["alpha1"]),\
		accessMsg.add_reaction(discordIds["alpha2"]),\
		accessMsg.add_reaction(discordIds["beta1"]),\
		accessMsg.add_reaction(discordIds["beta2"]),\
		accessMsg.add_reaction(discordIds["noaccess"]))

	isReady = True
	print("Setup complete")

# How the bot will handle reactions
@client.event
async def on_reaction_add(reaction,user):
	if not isReady or user.id == 735708593294147674:
		return

	global summaryDict
	reactMsgId = reaction.message.id

	currentUser = str(user)
	if currentUser not in summaryDict.keys():
		summaryDict.update( {currentUser : {
			"primary" : "",
			"secondary" : "",
			"playstyle" : "",
			"alpha":""
		}})


	if reaction.message.channel.id == 735235717558698094: #current registration channel Id
		if (reaction.emoji not in emojiWhiteList):
			await reaction.message.remove_reaction(reaction.emoji, user)
			return

		# get requested role
		for role in primaryClassRoles:
			if role.name == reaction.emoji.name:
				requestedRoleName = reaction.emoji.name
				requestedRole = role
				break
		
		#First Message was clicked, assign the user a role and move on
		if reactMsgId == msgIds["primaryClassMsgId"]: 
			await SetPrimaryClassRole(user, reaction, classNames, requestedRole, requestedRoleName)
			
		#second message was clicked, make sure they have a primary class role assigned, assign an augment class role
		elif reactMsgId == msgIds["secondaryClassMsgId"]:
			#time.sleep(2) #sleep command because people don't like to click slowly...
			#Get current role
			for role in user.roles:
				if role.name in classNames:
					currentRoleName = role.name
					break
				else:
					currentRoleName = None

			if currentRoleName is not None:
				await SetAugmentingClassRole(user, reaction, currentRoleName, requestedRoleName, augmentClassRoles)

		elif reactMsgId == msgIds["playStyleMsgId"]:
			#time.sleep(2) #sleep command because people don't like to click slowly...
			await SingleReactAddToDict(user, reaction, "playstyle")

		elif reactMsgId == msgIds["accessMsgId"]:	
			#time.sleep(2) #sleep command because people don't like to click slowly...
			await SingleReactAddToDict(user, reaction, "alpha")

		await reaction.message.remove_reaction(reaction.emoji, user) #clean up

@client.event
async def on_message(message):
	if(message.content.startswith('!summary')):
		channel = message.channel
		if channel.id == 735235717558698094:
			msgSender = str(message.author)
			innerdict = summaryDict[msgSender]
			errors = "None"
			response = f'Summary for {msgSender}: \n \
				Class: {innerdict["secondary"].capitalize()} \n \
				Base Class: {innerdict["primary"].capitalize()} \n \
				Playstyle: {innerdict["playstyle"].capitalize()} \n \
				Access: {innerdict["alpha"].capitalize()} \n\n \
				Issues: {errors}'

			msg = await channel.send(response)
			await DeleteMessageFromChannel(channel, msg, 4)
			await DeleteMessageFromChannel(channel, message)
			#send data to spreadsheet


# Set the primary role of a given user based on the passed reaction
async def SetPrimaryClassRole(user, reaction, classNames, requestedRole, requestedRoleName):
	# remove existing role
	roleRemoved = await RemoveRole(user, classNames)
	summaryDict[str(user)]['primary'] = requestedRoleName
	await user.add_roles(requestedRole)
	
	#if (roleRemoved):
	#	spreadsheetRemoveClass(user)


#Set the augmented class role for a given user based on the passed reaction
async def SetAugmentingClassRole(user, reaction, currentRole, requestedRole, augmentClassRoles):
	selectedCombo = classData[currentRole][requestedRole]
	await RemoveRole(user, augmentNames) #remove augment class, if it exists
	#get augmenting role
	for role in augmentClassRoles:
		if role.name == selectedCombo:
			augmentClassRole = role
			break

	summaryDict[str(user)]['secondary'] = selectedCombo
	await user.add_roles(augmentClassRole)

	#spreadsheetAdd(user, currentRole, selectedCombo)

async def SingleReactAddToDict(user, reaction, dictKey):
	summaryDict[str(user)][dictKey] = reaction.emoji.name
	#rosterSheet.update(f'{cellLetterToFill}{cells[0].row}', emojiName)


def spreadsheetAdd(user, currentRole, selectedCombo):
	cells = rosterSheet.findall(str(user))

	if (len(cells) == 0): #user does not exist in sheet yet fill in some non changing information
		row = nextAvailableRow(rosterSheet)
		rosterSheet.update(f'A{row}', user.name)
		rosterSheet.update(f'F{row}', str(user))
		rosterSheet.update(f'H{row}', str(datetime.date.today()))
	else :
		row = cells[0].row
	
	modifyClassCols(rosterSheet, row, currentRole, selectedCombo)

# removes the classes from the user entry in the spreadsheet
def spreadsheetRemoveClass(user):
	cells = rosterSheet.findall(str(user))
	if (len(cells) != 0):
		modifyClassCols(rosterSheet, cells[0].row, '','')

def modifyClassCols(worksheet, row, baseClass, augClass):
	worksheet.update(f'B{row}', augClass)
	worksheet.update(f'C{row}', baseClass)


def nextAvailableRow(worksheet):
	str_list = list(filter(None, worksheet.col_values(1)))
	return str(len(str_list)+1)

# Delete the message from the given reaction's channel
async def DeleteMessageFromChannel(channel, msg, sleepTime=0):
	time.sleep(sleepTime)
	await channel.delete_messages([msg])

# Remove a user's role if it is in the passed roles list
async def RemoveRole(user, rolesList):
	roleRemoved = False
	for role in user.roles:
			if role.name in rolesList:
				await user.remove_roles(role)
				roleRemoved = True
	return roleRemoved

client.run(TOKEN)