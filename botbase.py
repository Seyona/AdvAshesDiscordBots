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
import re

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
newbieRole = None

summaryDict = {}

chanIds = {
	"roster": 735729573865586708,
	"events": 738276488851226715
}

# Events stored by ID mapping to a string. 
# Users will react to the message and the message ID will add them to a spreadsheet
events = {}

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
	global newbieRole

	print(f'{client.user} has connected to Discord')
	
	for guild in client.guilds:
		if guild.name == GUILD:
			break

	rosterChan = None

	for channel in guild.text_channels:
		if channel.id == chanIds["roster"]:
			rosterChan = channel

	await rosterChan.purge()

	await rosterChan.send('To add/update your roster information click a reaction from each reaction set. You will be given a brief message to confirm your entry has been updated.')

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

	await rosterChan.send(cleanLine)

	primClassStr = f'What is your Primary class: {classSelection}'
	rosterPrimaryMsg = await rosterChan.send(primClassStr)

	await rosterChan.send(cleanLine)

	updateSecStr = f'What is your Secondary class: {classSelection}'
	rosterSecondaryMsg = await rosterChan.send(updateSecStr)

	await rosterChan.send(cleanLine)

	playStyleStr = (f'Select your Main playstyle (Select only 1): \n'+
	f'❖ PVE:           {discordIds["pve"]} \n' +
	f'❖ PVP:           {discordIds["pvp"]} \n '+
	f'❖ Lifeskiller: {discordIds["lifeskiller"]} \n')

	rosterPlyMsg = await rosterChan.send(playStyleStr)

	await rosterChan.send(cleanLine)

	accessStr = (f'Do you have any early access to the game?: \n' +
		f'❖ Alpha 1:      {discordIds["alpha1"]} \n' +
		f'❖ Alpha 2:     {discordIds["alpha2"]} \n' +
		f'❖ Beta 1:         {discordIds["beta1"]} \n' +
		f'❖ Beta 2:        {discordIds["beta2"]} \n' +
		f'❖ No Access {discordIds["noaccess"]}')

	rosterAccMsg = await rosterChan.send(accessStr)
	await rosterChan.send(cleanLine)

	msgIds = {
		"updatePrimaryMsgId": rosterPrimaryMsg.id,
		"updateSecondaryMsgId": rosterSecondaryMsg.id,
		"updatePlayStyleMsgId": rosterPlyMsg.id,
		"updateAccessMsgId": rosterAccMsg.id
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
			await gather(rosterPrimaryMsg.add_reaction(emoji),\
				rosterSecondaryMsg.add_reaction(emoji))

	for role in guild.roles:
		if role.name == discordIds["guildmembersRoleName"]:
			guildMemberRole = role
		if role.name == discordIds["newbieRoleName"]:
			newbieRole = role

	await gather(rosterPlyMsg.add_reaction(discordIds["pve"]),rosterPlyMsg.add_reaction(discordIds["pvp"]),rosterPlyMsg.add_reaction(discordIds["lifeskiller"]))
	
	await gather(rosterAccMsg.add_reaction(discordIds["alpha1"]),\
		rosterAccMsg.add_reaction(discordIds["alpha2"]),\
		rosterAccMsg.add_reaction(discordIds["beta1"]),\
		rosterAccMsg.add_reaction(discordIds["beta2"]),\
		rosterAccMsg.add_reaction(discordIds["noaccess"]))

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

	chanId = reaction.message.channel.id
	if chanId == chanIds["roster"]: 

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
				await gather(user.add_roles(guildMemberRole), user.remove_roles(newbieRole))

			await reaction.message.remove_reaction(reaction.emoji, user) #clean up

	elif chanId == chanIds["events"]:
		return
		

# Discord channel and user
async def submit(channel, user): 
	success = False
	if channel.id == chanIds["roster"]:
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
	if chanId == chanIds["roster"] and message.author.id != 735708593294147674:
		await DeleteMessageFromChannel(message.channel, message)
	
	elif chanId == chanIds["events"]:
		global events

		if message.content.startswith('!create'):
			event = events.get(message.id)
			if event is None:
				eventSplit = message.content.split(' ')
				lenOfSplit = len(eventSplit)

				timeOfEvent = eventSplit[lenOfSplit - 1]
				dateOfEvent = eventSplit[lenOfSplit - 2]
				eventName = ''.join(eventSplit[1:(lenOfSplit-2)])

				properFormat = "!create Event Name mm/dd hhmm (military time)"

				timeErrStr = f'Time is invalid or non-existant :: {properFormat}'
				if not re.match(r"^[0-2][0-3][0-5][0-9]$", timeOfEvent):
					await message.channel.send(timeErrStr)
					return
				
				eventTimeAsInt = int(timeOfEvent)

				if not re.match(r"^\d{1,2}\/\d{1,2}", dateOfEvent):
					await message.channel.send(f'Date is invalid or non-existant :: {properFormat}')
					return


				events[message.id] = eventName 
				eventsWorksheet = sheet.add_worksheet(title=eventName, rows=500, cols=7)
				eventsWorksheet.update('A1:G1', ['DiscordTag', 'Attended', 'Date', dateOfEvent, 'Time', eventTimeAsInt])

				await message.channel.send(f'An event called <{eventName}> has been scheduled for {dateOfEvent} at {eventTimeAsInt}')
				return
			else:
				await message.channel.send("There is already an event of that name created")

		elif message.content.startswith('!events'):
			return
		elif message.content.startswith('!startevent'):
			return


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

	rosterSheet.update(f'I{row}', str(datetime.datetime.now()))

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