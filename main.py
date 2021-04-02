#!/usr/bin/python3
# Discord requirements
import discord
import os
# End Discord requirements

import json
import time
import re
from psycopg2 import DatabaseError
from Events.events import Event
from Statics.statics import Static
from Statics.staticsManagement import StaticsManagement
from Statics.staticsDb import staticsDb

from classRolesManagement import AshesRolesManager
from spreadsheet import Spreadsheet
from helpers import *

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv("DISCORD_GUILD")

client = discord.Client()

primaryClassRoles = []
msgIds = None
isReady = False
cleanBoot = False
guildMemberRole = None
newbieRole = None

summaryDict = {}

chanIds = {
    "roster": 735729573865586708,
    "events": 738276488851226715,
    "staticCreation":825527440452485160,
    "orderDisplay": 825527879306575902
}


# pull ids into memory
with open(baseDir + 'NonPythonFiles/discordIds.json') as json_file:
    discordIds = json.load(json_file)

RolesManager = None
googleSheet = None

discordG = None

# On ready prep function
@client.event
async def on_ready():
    # global calls so we can modify these variables
    global isReady
    global RolesManager
    global googleSheet
    global discordG

    print(f'{client.user} has connected to Discord')

    for guild in client.guilds:
        if guild.name == GUILD:
            break

    discordG = guild
    rosterChan = None
    for channel in guild.text_channels:
        if channel.id == chanIds["roster"]:
            rosterChan = channel

    googleSheet = Spreadsheet(os.getenv('SHEET_IDENTIFIER'))
    RolesManager = AshesRolesManager(rosterChan, discordIds, googleSheet)
    await RolesManager.init(discordIds, guild)

    isReady = True
    print("Setup complete")


# How the bot will handle reactions
@client.event
async def on_reaction_add(reaction, user):
    if not isReady or user.id == 735708593294147674:
        return

    global summaryDict
    global RolesManager

    chanId = reaction.message.channel.id

    if chanId == chanIds["roster"]:
        await RolesManager.ReactionAdded(reaction, user)

    elif chanId == chanIds["events"]:
        return


@client.event
async def on_message(message):
    chanId = message.channel.id
    if chanId == chanIds["roster"] and message.author.id != 735708593294147674:
        await DeleteMessageFromChannel(message.channel, message)

    elif chanId == chanIds["events"]:

        if message.content.startswith('!create'):
            event = Event()
            err = event.from_message(message)

            if err != "":
                await message.channel.send(err)

            elif not event.isValid():
                await message.channel.send("Passed data was unable to be parsed please revise your input \n"
                                           f'Format: {eventFormatMessage} \n Example: {createEventEx}')
            else:
                # Add the event to the database (and spreadsheet?)
                # eventsWorksheet = sheet.add_worksheet(title=eventName, rows=500, cols=7)
                # eventsWorksheet.update('A1:F1', ['DiscordTag', 'Attended', 'Date', dateOfEvent, 'Time', eventTimeAsInt])
                await message.channel.send(
                    f'An event called <{event.event_name}> has been scheduled')

        elif message.content.startswith('!events'):
            return
        elif message.content.startswith('!startevent'):
            return
    
    elif chanId == chanIds["staticCreation"]: 
        msgUser = message.author
        userStr = str(msgUser)

        if message.content.startswith('!help'): #display commands and 
            await message.channel.send("Here is a list of valid commands: \n"
                                        f'Create: {createStaticEx} \n'
                                        f'Join: {joinStaticEx} \n'
                                        f'Order Leader commands: \n'
                                        f'Disband: {disbandEx}\n'
                                        f'Promote Lead: {promoteLeaderEx} \n'
                                        f'Add Colead: {promoteColeadEx} \n')

        elif message.content.startswith('!startorder'):
            
            static = Static()
            static.from_creation_request(message.content, str(message.author))

            if static.static_exists():
                await message.channel.send("An Order with this name already exists")
            else:
                manager = StaticsManagement(static)

                try:
                    static.create()
                    manager.setStaticInfo(static)
                except(Exception, DatabaseError) as error:
                    await message.channel.send("There was an error when creating your Order. Contact Seyon")
                    return
                
                # Create new role for static 
                await discordG.create_role(name=f'{static.static_name}')
                newRole = discord.utils.get(discordG.roles, name=f'{static.static_name}')
                static.discord_id = newRole.id

                manager.initRoles(discordIds, discordG, static.static_name)
                await manager.AddLeaderRole(message.author)
                await manager.AddStaticRole(message.author)
                await manager.AddDiscordRole(message.author)
                # Remove Ritualist 

                # Create new channel for static under the Category
                category = discord.utils.get(discordG.categories, name='◇──◇Orders◇──◇')
                await discordG.create_text_channel(f'{static.static_name}', category=category)

                # Create new voice channel for static under the Category
                await discordG.create_voice_channel(f'{static.static_name}', category=category)

                # Fetch new Channel ID
                newChan = discord.utils.get(discordG.channels, name=f'{str.lower(static.static_name)}')
                static.chat_id = newChan.id

                # Fetch new Voice Channel Id
                newVChan = discord.utils.get(discordG.channels, name=f'{static.static_name}')
                static.voicechat_id = newVChan.id

                try:
                    static.Update()
                except(Exception, DatabaseError) as error:
                    await message.channel.send("There was an error when updating your Order. Contact Seyon")
                    return

                try:
                    db = staticsDb()
                    msg = db.AddUserToStatic(str(message.author), static.static_name)

                    if msg != "":
                        await message.channel.send(f'{msg}')
                        dropmsg = db.dropStatic(static.static_name)
                        if dropmsg != "":
                            await message.channel.send(f'{dropmsg}')
                
                except(Exception, DatabaseError) as error:
                    await message.channel.send("There was an error when linking the user to the static. Contact Seyon")
                    return
                
                await message.channel.send(f'The order {static.static_name}. The role <@&{static.discord_id}> and channel <#{static.chat_id}> were created for your use. ')

        elif message.content.startswith('!joinorder'):

            db = staticsDb()
            staticName = [x.strip() for x in message.split(' ', 1)][1]
            static = db.GetStaticDataByName(staticName)
            
            outputMsg = ""

            if static:
                if db.StaticHasSpace(staticName):         
                    if not db.IsInAStatic(userStr):
                        if not db.IsInGivenStatic(userStr, staticName):
                            db.AddUserToStatic(userStr, staticName)
                        else:
                            outputMsg = f'{userStr} is already in this Order'
                    else:
                        outputMsg = f'{userStr} is already in a Order'
                else:
                    outputMsg = f'Static is currently full (8 people)'
            else:
                outputMsg = f'Order \'{staticName}\' does not exist.'
            
            await message.channel.send(outputMsg)

        elif message.content.startswith('!addcolead'):
            db = staticsDb()
            staticName = [x.strip() for x in message.split(' ', 1)][1]
            data = db.GetStaticDataByName(staticName)

            if db.IsInGivenStatic(userStr, staticName):
                data.static_colead = userStr
                staticObj = Static(data)
                staticObj.Update()
                
            else:
                await message.channel.send(f'User: {userStr} is not in the order \'{staticName}\' and cannot be promoted to Knight')

        elif message.content.startswith('!disbandorder'):
            db = staticsDb()
            staticName = [x.strip() for x in message.split(' ', 1)][1]

            try:
                static = db.GetStaticDataByName(staticName)

                if userStr == static.static_lead:
                    try:
                        static_users = db.GetAllUsersInStatic(staticName)

                        if static_users:
                            try:
                                for user in static_users:
                                    db.DropUserFromStatic(staticName, user)

                            except(Exception, DatabaseError) as error:
                                await message.channel.send(f'There was an issue when removing user from the Order {staticName}')
                        else:
                            await message.channel.send(f'Order: {staticName}, has no users')

                    except(Exception, DatabaseError) as error:
                        await message.channel.send("There was an error when fetching static users. Contact Seyon")
                        return
                else:
                    await message.channel.send(f'You need to be the leader of the order to disband.')

            except(Exception, DatabaseError) as error:
                await message.channel.send("There was an error when fetching Order by name. Contact Seyon")
                return

        elif message.content.startswith('!promotelead'):
            return


# Delete the message from the given reaction's channel
async def DeleteMessageFromChannel(channel, msg, sleepTime=0):
    time.sleep(sleepTime)
    await channel.delete_messages([msg])


client.run(TOKEN)
