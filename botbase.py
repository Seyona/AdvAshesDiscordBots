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
emojiWhiteListFile = "emojiWhiteList.csv"
primaryClassRoles = []
primaryClassRolesFile = "primaryClassRoles.csv"
augmentClassRoles = []
augmentClassRolesFile = "augmentClassRoles.csv"

msgIds = None
msgIdsFileName = "messageIds.json"
primaryClassMsgId = 0
secondaryClassMsgId = 0
playStyleMsgId = 0
accessMsgId = 0

isReady = False
cleanBoot = False

parser = argparse.ArgumentParser()
parser.add_argument("--cleanboot", help="Something with terribly wrong, clean up the discord channel and do afresh slate", action="store_true")

args = parser.parse_args()
if args.cleanboot:
	print("Clean boot started")
	cleanBoot = True
	os.remove(emojiWhiteListFile)
	os.remove(msgIdsFileName)
	os.remove(primaryClassRolesFile)
	os.remove(augmentClassRolesFile)
else:
	with open(emojiWhiteListFile, newline='') as csvF:
		reader = csv.reader(csvF)
		emojiWhiteList = list(reader)

	with open(msgIdsFileName) as jsonFile:
		msgIds = json.load(jsonFile)
	
	with open(primaryClassRolesFile) as csvF:
		reader = csv.reader(csvF)
		primaryClassRoles = list(reader)

	with open(augmentClassRolesFile) as csvF:
		reader = csv.reader(csvF)
		augmentClassRoles = list(reader)

	isReady = True

#initialize the Gsheet api
SPREADSHEET_ID = '1kTPhqosR0DRoVzccjOpFB2b2OmT-yxj6K4j_te_qBxg'
gc = gspread.service_account()
sheet = gc.open_by_key(SPREADSHEET_ID)
rosterSheet = sheet.worksheet("Roster")

# pull classes file into memory
with open('classes.json') as json_file:
	classData = json.load(json_file)
	classNames = classData.keys()
	augmentNames = [item for innerList in classData.values() for item in innerList.values()]

# pull ids into memory
with open('discordIds.json') as json_file:
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
	global primaryClassMsgId
	global secondaryClassMsgId, playStyleMsgId, accessMsgId
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

	if cleanBoot:
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

		accessMsg = await channel.send('Do you have any early access to the game?: \n Alpha 1: {} \n Alpha 2: {} \n Beta 1: {} \n Beta2: {}')
		await channel.send(cleanLine)

		msgIds = {
			"primaryClassMsgId": primaryMsg.id,
			"secondaryClassMsgId": secondaryMsg.id,
			"playStyleMsgId": playStyleMsg.id,
			"accessMsgId": accessMsg.id,
		}

		# write ids to file
		with open(msgIdsFileName, 'w') as fp:
			json.dump(msgIds, fp)

		#construct a white list
		for emoji in guild.emojis:
			if emoji.name in classNames:
				emojiWhiteList.append(emoji)	
			elif emoji.name in discordIds.keys():
				emojiWhiteList.append(emoji)

		emojiWhiteList.sort(key= lambda x: x.name, reverse=False)

		# write emoji whitelist to file
		with open(emojiWhiteListFile, 'w', newline='') as fp:
			writer = csv.writer(fp, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
			writer.writerows(emojiWhiteList)

		for emoji in emojiWhiteList:
			if emoji.name in classNames:
				await gather(primaryMsg.add_reaction(emoji),secondaryMsg.add_reaction(emoji))

		for role in guild.roles:
			if role.name in classNames:
				primaryClassRoles.append(role)
			if role.name in augmentNames:
				augmentClassRoles.append(role)

		with open(primaryClassRolesFile, 'w', newline='') as fp:
			writer = csv.writer(fp, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for role in primaryClassRoles: writer.writerow([role])

		with open(augmentClassRolesFile, 'w', newline='') as fp:
			writer = csv.writer(fp, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for role in augmentClassRoles: writer.writerow([role])

		await gather(playStyleMsg.add_reaction(discordIds["pve"]),playStyleMsg.add_reaction(discordIds["pvp"]),playStyleMsg.add_reaction(discordIds["lifeskiller"]))

		isReady = True
	print("Setup complete")

# How the bot will handle reactions
@client.event
async def on_reaction_add(reaction,user):
	if not isReady or user.id == 735708593294147674:
		return

	reactMsgId = reaction.message.id

	if reaction.message.channel.id == 735235717558698094: #current registration channel Id
		if (reaction.emoji not in emojiWhiteList):
			await reaction.message.remove_reaction(reaction.emoji, user)
			return

		# get requested role
		for role in primaryClassRoles:
			if role.name == reaction.emoji.name:
				requestedRoleName = reaction.emoji.name
				roleSelectionString = f'<@{user.id}>, you selected the {requestedRoleName}'
				requestedRole = role
				break
		
		#First Message was clicked, assign the user a role and move on
		if reactMsgId == msgIds["primaryClassMsgId"]: 
			await SetPrimaryClassRole(user, reaction, classNames, requestedRole, roleSelectionString)
			
		#second message was clicked, make sure they have a primary class role assigned, assign an augment class role
		elif reactMsgId == msgIds["secondaryClassMsgId"]:
			#Get current role
			for role in user.roles:
				if role.name in classNames:
					currentRoleName = role.name
					break
				else:
					currentRoleName = None

			if currentRoleName is None:
				pickFromtheFirstMsg = await reaction.message.channel.send(f'<@{user.id}>, you need to select a primary class first. {discordIds["seyonirl"]}') 
				await DeleteMessageFromReaction(reaction, pickFromtheFirstMsg, 5)

			else:
				await SetAugmentingClassRole(user, reaction, currentRoleName, requestedRoleName, augmentClassRoles, roleSelectionString)

		elif reactMsgId == msgIds["playStyleMsgId"]:
			await SingleReactAndSpreadsheetEdit(user, reaction,'D', f'<@{user.id}>, your prefered play style is: {reaction.emoji.name}. Excellent choice!')

		elif reactMsgId == msgIds["accessMsgId"]:	
			await SingleReactAndSpreadsheetEdit(user, reaction, 'G',f'<@{user.id}>, we will see you in {reaction.emoji.name}? Awesome glad to have you!')

		await reaction.message.remove_reaction(reaction.emoji, user) #clean up


# Set the primary role of a given user based on the passed reaction
async def SetPrimaryClassRole(user, reaction, classNames, requestedRole, roleSelectionString):
	# remove existing role
	roleRemoved = await RemoveRole(user, classNames)
	if (roleRemoved):
		spreadsheetRemoveClass(user)

	roleConfirmMsg = await reaction.message.channel.send(f'{roleSelectionString} as your primary role. Don\'t forget to select an augmenting class!')
	await user.add_roles(requestedRole)

	await DeleteMessageFromReaction(reaction,roleConfirmMsg, 5)


#Set the augmented class role for a given user based on the passed reaction
async def SetAugmentingClassRole(user, reaction, currentRole, requestedRole, augmentClassRoles, roleSelectionString):
	selectedCombo = classData[currentRole][requestedRole]
	await RemoveRole(user, augmentNames) #remove augment class, if it exists
	#get augmenting role
	for role in augmentClassRoles:
		if role.name == selectedCombo:
			augmentClassRole = role
			break

	comboMsg = await reaction.message.channel.send(f'{roleSelectionString} as your augment role. You are a {selectedCombo.capitalize()}! {discordIds["wow"]}')
	await user.add_roles(augmentClassRole)

	spreadsheetAdd(user, currentRole, selectedCombo)

	await  DeleteMessageFromReaction(reaction, comboMsg, 5)

async def SingleReactAndSpreadsheetEdit(user, reaction, cellLetterToFill, successStr):
	cells = rosterSheet.findall(str(user))
	if len(cells) == 0:
		await reaction.message.channel.send(f'<@{user.id}>, you need to respond to the primary AND secondary class prompts before selecting this option')
	else:
		emojiName = reaction.emoji.name
		responseMsg = await reaction.message.channel.send(successStr)
		rosterSheet.update(f'{cellLetterToFill}{cells[0].row}', emojiName)
		await DeleteMessageFromReaction(reaction, responseMsg, 4)

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
async def DeleteMessageFromReaction(reaction, msg, sleepTime=0):
	time.sleep(sleepTime)
	await reaction.message.channel.delete_messages([msg])

# Remove a user's role if it is in the passed roles list
async def RemoveRole(user, rolesList):
	for role in user.roles:
			if role.name in rolesList:
				await user.remove_roles(role)
				return True
	return False

client.run(TOKEN)