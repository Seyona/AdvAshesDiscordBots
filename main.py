#!/usr/bin/python3
# Discord requirements
import discord
import os
# End Discord requirements

import json
import time
import re
import asyncio
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
        manager = StaticsManagement()

        if message.content.startswith('!help'): #display commands and 
            await message.channel.send("Here is a list of valid commands: \n"
                                        f'Create: {createStaticEx} \n'
                                        f'Join: {joinStaticEx} \n'
                                        f'------------------------------ \n'
                                        f'Disband [Order leader only]: {disbandEx}\n'
                                        f'Promote Lead [Order leader only]: {promoteLeaderEx} \n'
                                        f'Add Colead [Order leader only]: {promoteColeadEx} \n')

        elif message.content.startswith('!startorder'):
            
            db = staticsDb()
            static = Static()
            static.from_creation_request(message.content, str(message.author))
             
            games = db.GetGames()
            game = None

            if games == []:
                await message.channel.send("Error when fetching games. Contact Seyon")
                return 

            await message.channel.send(f'What game is this order for? \n' + "\n".join(games))

            def check(m):
                return m.content in games and m.channel == message.channel

            try:
                msg = await client.wait_for('message', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await message.channel.send('Operation has timed out. You will need to start the creation process.')
                return
            else:
                if msg.content in games:
                    game = msg.content
                    static.game_id = game
                    await message.channel.send('Starting creation')
                else:
                    await message.channel.send('Game is not in the list. If this is an error contact Seyon or Tockz.')
                    return
                
            try:           
                if db.IsInAStatic(userStr, static.game_id):
                    await message.channel.send("You cannot create an order while already in one")
                    return
            except(Exception, DatabaseError) as error:
                await message.channel.send("There was an error while checking your order status.  Contact Seyon")
                return

           
            if static.static_exists():
                await message.channel.send("An Order with this name already exists")
            else:
                try:
                    static.create()
                    manager.setStaticInfo(static)
                except(Exception, DatabaseError) as error:
                    await message.channel.send("There was an error when creating your Order. Contact Seyon")
                    return
                
                # Create new role and channels for static
                global discordG 
                category = discord.utils.get(discordG.categories, name='◇──◇Orders◇──◇')

                role_name = f'{static.static_name}~{static.game_id}'
                new_chan_name = f'{static.static_name}~{static.game_id}'
                await discordG.create_role(name=role_name)
                await discordG.create_text_channel(new_chan_name, category=category)
                await discordG.create_voice_channel(new_chan_name, category=category)

                # fetch an updated instance of the discord server 
                
                discordG = await client.fetch_guild(discordG.id) 

                newRole = discord.utils.get(discordG.roles, name=role_name)
                static.discord_id = newRole.id

                manager.initRoles(discordIds, discordG, newRole, static.static_name)
                await manager.AddLeaderRole(message.author)
                await manager.AddStaticRole(message.author)
                await manager.AddDiscordRole(message.author)
                await manager.RemoveBasicTag(message.author)

                # Fetch new Channel ID
                chans = await discordG.fetch_channels()
                newChan = discord.utils.get(chans, name=f'{str.lower(new_chan_name.replace(" ","-"))}')
                static.chat_id = newChan.id

                # Fetch new Voice Channel Id
                newVChan = discord.utils.get(dchans, name=new_chan_name)
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
            staticName = [x.strip() for x in message.content.split(' ', 1)][1]
            data = db.GetStaticDataByName(staticName)
            manager.setStaticInfo(Static(data))
            manager.initRoles(discordIds, discordG)

            outputMsg = 'You have successfully joined {staticName}'

            if data:
                if db.StaticHasSpace(staticName):         
                    if not db.IsInAStatic(userStr):
                        if not db.IsInGivenStatic(userStr, staticName):
                            db.AddUserToStatic(userStr, staticName)
                            await manager.RemoveBasicTag(msgUser)
                            await manager.AddDiscordRole(msgUser)
                            await manager.AddStaticRole(msgUser)
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
            new_colead = [x.strip() for x in message.content.split(' ', 1)][1]

            coleadHasProperFormat = re.match(r".*#\d{4}$", new_colead)
            if coleadHasProperFormat:
                try:
                    new_coleadData = db.GetUserStaticData(new_colead)
                    userData = db.GetUserStaticData(msgUser)

                    if userData[1] == new_coleadData[1]: # Same static 
                        data = db.GetStaticDataByName(userData[1])
                        manager.setStaticInfo(Static(data))
                        manager.initRoles(discordIds, discordG)
                        current_colead = None

                        if data.static_colead != 'None':
                            splitname = data.static_colead.split('#')
                            current_colead = discord.utils.get(discordG.members, name=splitname[0], discriminator=splitname[1])
                            manager.RemoveColeadRole(current_colead)

                        if db.IsInGivenStatic(new_colead, userData[1]):
                            data.static_colead = new_colead
                            staticObj = Static(data)
                            staticObj.Update()
                            manager.AddColeadRole(msgUser)
                        else:
                            await message.channel.send(f'User: {userStr} is not in the order \'{staticName}\' and cannot be promoted to Knight')
                    else:
                        await message.channel.send(f'User: {new_colead} is not in Order: {userData[1]}')
                        
                except(Exception, DatabaseError) as error:
                    await message.channel.send("There was an error when promoting Colead. Contact Seyon")
                    return
            else:
                await message.channel.send(f'User {new_colead}, is not formatted properly. Proper Format: {promoteColeadEx}')

        elif message.content.startswith('!disbandorder'):
            db = staticsDb()
            staticName = [x.strip() for x in message.content.split(' ', 1)][1]

            try:
                static_data = db.GetStaticDataByName(staticName)
                manager.setStaticInfo(Static(static))
                manager.initRoles(discordIds, discordG)
                
                if userStr == static_data.static_lead:
                    static_users = db.GetAllUsersInStatic(staticName)

                    if static_users:
                        for user in static_users:
                            db.DropUserFromStatic(staticName, user)
                            splitname = user.split('#')
                            discUser = discord.utils.get(discordG.members, name=splitname[0], discriminator=splitname[1])
                            
                            manager.AddBasicTag(discUser)
                            # Don't really care what tags they may or may not have, just remove all possible tags
                            manager.RemoveLeaderRole(discUser)
                            manager.RemoveColeadRole(discUser)
                            manager.RemoveStaticRole(discUser)
                            manager.RemoveDiscordRole(discUser)

                        db.dropStatic(staticName)
                    else:
                        await message.channel.send(f'Order: {staticName}, has no users')

                else:
                    await message.channel.send(f'You need to be the leader of the order to disband.')

            except(Exception, DatabaseError) as error:
                await message.channel.send("There was an error when disbanding Order by. Contact Seyon")
                return

        elif message.content.startswith('!promotelead'):
            db = staticsDb()
            new_lead = [x.strip() for x in message.content.split(' ', 1)][1]

            leadHasProperFormat = re.match(r".*#\d{4}$", new_lead)

            if leadHasProperFormat:
                try:
                    new_leadData = db.GetUserStaticData(new_lead)
                    userData = db.GetUserStaticData(msgUser)

                    if userData[1] == new_leadData[1]: # Same static

                        data = db.GetStaticDataByName(new_leadData[1])
                        manager.setStaticInfo(Static(data))
                        manager.initRoles(discordIds, discordG)

                        data.static_lead = new_lead
                        splitname = new_lead.split('#')
                        discUser = discord.utils.get(discordG.members, name=splitname[0], discriminator=splitname[1])

                        staticObj = Static(data)
                        staticObj.Update() # Make sure update is successful before updating roles
                        manager.AddLeaderRole(discUser)
                        manager.RemoveLeaderRole(msgUser)
                    else:
                        await message.channel.send(f'User: {new_lead} is not in Order: {userData[1]}')

                except(Exception, DatabaseError) as error:
                    await message.channel.send("There was an error when promoting a new lead. Contact Seyon")
                    return
            else:
                 await message.channel.send(f'User {new_lead}, is not formatted properly. Proper Format: {promoteLeaderEx}')


# Delete the message from the given reaction's channel
async def DeleteMessageFromChannel(channel, msg, sleepTime=0):
    time.sleep(sleepTime)
    await channel.delete_messages([msg])


client.run(TOKEN)
