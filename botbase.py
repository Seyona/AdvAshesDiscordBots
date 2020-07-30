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
msgIds = None
isReady = False
cleanBoot = False
guildMemberRole = None

summaryDict = {}

chanIds = {
	"registration": 735235717558698094,
	"update": 735729573865586708
}

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
	global guildMemberRole

	print(f'{client.user} has connected to Discord')
	
	for guild in client.guilds:
		if guild.name == GUILD:
			break

	registrationChan = None
	updateChan = None

	for channel in guild.text_channels:
		if channel.name == "class-registration":
			registrationChan = channel
		if channel.name == "update-roster"
			updateChan = channel

	await registrationChan.purge()
	await updateChan.purge()

	await registrationChan.send(f'Welcome to the guild! Before you can tagged up as a {discordIds["guildmembers"]} You\'ll need to complete this form. It\'s pretty quick, just react to each message once (start from the top!). If everything looks good you\'ll be entered into the guild!')
	await registrationChan.send(f'Do not panic if your reaction goes away it has been recorded!')

	await updateChan.send('To update your roster information click a reaction from each reaction set. You will be given a brief message to confirm your entry has been updated.')

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

	await registrationChan.send(cleanLine)
	await updateChan.send(cleanLine)

	primClassStr = f'What is your Primary class: {classSelection}'
	primaryMsg = await registrationChan.send(primClassStr)
	updatePrimMsg = await updateChan.send(primClassStr)

	await registrationChan.send(cleanLine)
	await updateChan.send(cleanLine)

	updateSecStr = f'What is your Secondary class: {classSelection}'
	secondaryMsg = await registrationChan.send(updateSecStr)
	updateSecMsg = await updateChan.send(updateSecStr)

	await registrationChan.send(cleanLine)
	await updateChan.send(cleanLine)

	playStyleStr = f'Select your Main playstyle (Select only 1): \n'+
	f'❖ PVE:           {discordIds["pve"]} \n' +
	f'❖ PVP:           {discordIds["pvp"]} \n '+
	f'❖ Lifeskiller: {discordIds["lifeskiller"]} \n'

	playStyleMsg = await registrationChan.send(playStyleStr)
	updatePlyMsg = await updateChan.send(playStyleStr)

	await registrationChan.send(cleanLine)
	await updateChan.send(cleanLine)

	accessStr = f'Do you have any early access to the game?: \n' +
		f'❖ Alpha 1:      {discordIds["alpha1"]} \n' +
		f'❖ Alpha 2:     {discordIds["alpha2"]} \n' +
		f'❖ Beta 1:         {discordIds["beta1"]} \n' +
		f'❖ Beta 2:        {discordIds["beta2"]} \n' +
		f'❖ No Access {discordIds["noaccess"]}'

	accessMsg = await registrationChan.send(accessStr)
	updateAccMsg = await updateChan.send(accessStr)

	await registrationChan.send(cleanLine)
	await updateChan.send(cleanLine)

	msgIds = {
		"primaryClassMsgId": primaryMsg.id,
		"updatePrimaryMsgId": updatePrimMsg.id,
		"secondaryClassMsgId": secondaryMsg.id,
		"updateSecondaryMsgId": updateSecMsg.id,
		"playStyleMsgId": playStyleMsg.id,
		"updatePlayStyleMsgId": updatePlyMsg.id,
		"accessMsgId": accessMsg.id,
		"updateAccessMsgId": updateAccMsg.id
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
		if role.name == discordIds["guildmembersRoleName"]:
			guildMemberRole = role

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
			"baseClassMsg" : None,
			"secondary" : "",
			"secondaryClassMsg" : None,
			"playstyle" : "",
			"playstyleMsg" : None,
			"alpha":"",
			"alphaMsg" : None
		}})


	chanId = reaction.message.channel.id
	if chanId == chanIds["registration"] or chanId == chanIds["update"]: 
		if (reaction.emoji not in emojiWhiteList):
			await reaction.message.remove_reaction(reaction.emoji, user)
			return

		# get requested role
		for role in primaryClassRoles:
			if role.name == reaction.emoji.name:
				requestedRoleName = reaction.emoji.name
				requestedRole = role
				break

		for react in reaction.message.reactions:
			async for reacter in react.users():
				if str(reacter) == str(user) and react.emoji.name != reaction.emoji.name:
					await reaction.message.remove_reaction(react.emoji, reacter)
		
		#First Message was clicked, assign the user a role and move on
		if reactMsgId == msgIds["primaryClassMsgId"] or reactMsgId == msgIds["updatePrimaryMsgId"]: 
			await SetPrimaryClassRole(user, reaction.emoji.name)
			summaryDict["baseClassMsg"] = reaction
			
		#second message was clicked, make sure they have a primary class role assigned, assign an augment class role
		elif reactMsgId == msgIds["secondaryClassMsgId"] or reactMsgId == msgIds["updateSecondaryMsgId"]:
			#Get base class
			try:
				baseClass = summaryDict[currentUser]["primary"]

				if baseClass != "":
					await SetAugmentingClassRole(user, baseClass, reaction.emoji.name)
					summaryDict["secondaryClassMsg"] = reaction
				else:
					await reaction.message.remove_reaction(reaction.emoji, user)

			except KeyError:
				print(f'{currentUser} attempting to select a secondary class when entry is not in dictionary. (probably spamming)')

		elif reactMsgId == msgIds["playStyleMsgId"] or reactMsgId == msgIds["updatePlayStyleMsgId"]:
			summaryDict[str(user)]["playstyle"] = reaction.emoji.name
			summaryDict["playstyleMsg"] = reaction

		elif reactMsgId == msgIds["accessMsgId"] or reactMsgId == msgIds["updateAccessMsgId"]:
			summaryDict[str(user)]["alpha"] = reaction.emoji.name
			success = await submit(reaction.message.channel, user)
			if success:
				old = summaryDict["secondaryClassMsg"]
				await old.message.remove_reaction(old.emoji,user)
				old = summaryDict["baseClassMsg"]
				await old.message.remove_reaction(old.emoji,user)
				old = summaryDict["playstyleMsg"]
				await old.message.remove_reaction(old.emoji,user)
				await user.add_roles(guildMemberRole)

			await reaction.message.remove_reaction(reaction.emoji, user) #clean up

		

# Discord channel and user
async def submit(channel, user): 
	success = False
	if chanId == chanIds["registration"] or chanId == chanIds["update"]:
		submitter = str(user)
	
		innerdict = summaryDict[submitter]
		missingItems = []
		errors = ""
		
		classStr = innerdict["secondary"].capitalize()
		baseClass = innerdict["primary"].capitalize()
		playstyle = innerdict["playstyle"].capitalize()
		alpha = innerdict["alpha"].capitalize()

		response = f'Summary for <@{user.id}>: \n'

		if classStr == '':
			missingItems.append("Secondary Class")
		if baseClass == '':
			missingItems.append("Primary class")
		if playstyle == '':
			missingItems.append("Play style")
		if alpha == '':
			missingItems.append("Access level")

		response += ( f'Class: {classStr} \n'+
		f'Base Class: {baseClass} \n'+
		f'Playstyle: {playstyle} \n'+
		f'Access: {alpha} \n\n')
		
		if len(missingItems) != 0 :
			errors = "Missing: " + ', '.join(missingItems)
			response = response + errors

		if errors == "": # No problem run spreadsheet update
			SendDictToSpreadsheet(innerdict, user)
			success = True # maybe new respond message depending what channel they are in

		msg = await channel.send(response)
		await DeleteMessageFromChannel(channel, msg, 5)
		return success


@client.event
async def on_message(message):
	chanId = message.channel.id
	if (chanId == chanIds["registration"] or chanId == chanIds["update"]) and message.author.id != 735708593294147674:
		await DeleteMessageFromChannel(message.channel, message)


def SendDictToSpreadsheet(personInfo, user):
	discordNameWithTag = str(user)
	cells = rosterSheet.findall(discordNameWithTag)

	if len(cells) == 0: #new entry
		row = nextAvailableRow(rosterSheet)
		rosterSheet.update(f'A{row}', user.name)
		rosterSheet.update(f'G{row}', discordNameWithTag)
		rosterSheet.update(f'H{row}', str(datetime.date.today()))
	else:
		row = cells[0].row

	if personInfo['secondary'] != '':
		rosterSheet.update(f'B{row}', personInfo['secondary'])

	if personInfo['primary'] != '':
		rosterSheet.update(f'C{row}', personInfo['primary'])

	if personInfo['playstyle'] != '':
		rosterSheet.update(f'E{row}', personInfo['playstyle'])

	if personInfo['alpha'] != '':
		rosterSheet.update(f'F{row}', personInfo['alpha'])

	if discordNameWithTag in summaryDict:
		del summaryDict[discordNameWithTag]


# Set the primary role of a given user based on the passed reaction
async def SetPrimaryClassRole(user, requestedRoleName):
	summaryDict[str(user)]['primary'] = requestedRoleName

#Set the augmented class role for a given user based on the passed reaction
async def SetAugmentingClassRole(user, currentRole, requestedRole):
	selectedCombo = classData[currentRole][requestedRole]
	summaryDict[str(user)]['secondary'] = selectedCombo

async def SingleReactAddToDict(user, reaction, dictKey):
	summaryDict[str(user)][dictKey] = reaction.emoji.name

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