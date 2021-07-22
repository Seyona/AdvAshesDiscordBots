#!/usr/bin/python3
# Discord requirements
import discord
import os
# End Discord requirements

import json
import time
import re
import asyncio
from ordersManagement import *
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
            
            try:
                (static, role) = await StartOrder(static, discordG)

                manager.setStaticInfo(static)
                manager.initRoles(discordIds, discordG, role, static.static_name)
                await manager.AddLeaderRole(message.author)
                await manager.AddStaticRole(message.author)
                await manager.AddDiscordRole(message.author)
                await manager.RemoveBasicTag(message.author)

                JoinOrder(static.static_name, msgUser)
                await message.channel.send(f'The order {static.static_name}. The role <@&{static.discord_id}>, text channel, and voice channel were created for the Orders use')

            except(Exception, DatabaseError) as error:
                await message.channel.send(str(error))
                return              
                
        elif message.content.startswith('!joinorder'):

            db = staticsDb()
            staticName = [x.strip() for x in message.content.split(' ', 1)][1]
            data = db.GetStaticDataByName(staticName)

            if not data:
                await message.channel.send(f'Order, {staticName}, does not exist')
                return

            staticRole = discord.utils.get(discordG.roles, id=int(data.discord_id))

            try:
                JoinOrder(data.static_name, msgUser)
                manager.setStaticInfo(Static(data))
                manager.initRoles(discordIds, discordG, staticRole ,data.static_name)
                await manager.RemoveBasicTag(msgUser) # Not everyone needs this
                await manager.AddDiscordRole(msgUser) # Not everyone needs this every time
                await manager.AddStaticRole(msgUser) # Unique to the order they are joining

                await message.channel.send(f'You have successfully joined {data.static_name}.')

            except(Exception, DatabaseError) as error:
                await message.channel.send(str(error))
                return

        elif message.content.startswith('!addcolead'):
            db = staticsDb()
            # split on space, get the 2nd item (everything after the command) split on the first comma
            splitString = [x.strip() for x in message.content.split(' ',1)[1].split(',',1)] 
            new_colead = splitString[0]
            order_name = splitString[1]

            try:
                data = db.GetStaticDataByName(order_name)
                if not data: 
                    await message.channel.send(f'Order, {order_name}, does not exist')

                staticRole = discord.utils.get(discordG.roles, id=int(data.discord_id))
                manager.setStaticInfo(Static(data))
                manager.initRoles(discordIds, discordG, staticRole, data.static_name)

                await PromoteCoLead(data, new_colead, userStr, False, discordG, manager) 
            except(Exception) as error:
                await message.channel.send(str(error))
                return

        elif message.content.startswith('!disbandorder'):
            return True
            db = staticsDb()
            staticName = [x.strip() for x in message.content.split(' ', 1)][1]

            # Get the game that the static is for before deleting
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
                if msg.content in games:
                    game = msg.content
                    await message.channel.send('Processing....')
                else:
                    await message.channel.send('Game is not in the list. If this is an error contact Seyon or Tockz.')
                    return
            except asyncio.TimeoutError:
                await message.channel.send('Operation has timed out. You will need to start the creation process.')
                return

            try:
                static_data = db.GetStaticDataByName(staticName, game)

                if static_data is not None:
                    manager.setStaticInfo(Static(static_data))
                    staticRole = discord.utils.get(discordG.roles, id=static_data.discord_id)

                    manager.initRoles(discordIds, discordG, staticRole, static_data.static_name)
                else:
                    await message.channel.send(f'Unable to delete static, {staticName}, does not exist for game, {game}')
                    return 

                if userStr == static_data.static_lead:
                    static_users = db.GetAllUsersInStatic(staticName, static_data.game_id)

                    if static_users:
                        for user in static_users:
                            db.DropUserFromStatic(staticName, user)
                            splitname = user.split('#')
                            discUser = discord.utils.get(discordG.members, name=splitname[0], discriminator=splitname[1])
                            
                            try:
                                inAnyStatic = db.GetUsersStatics(str(discUser))
                                if not inAnyStatic: # No order, add basic discord tag
                                    manager.AddBasicTag(discUser)
                                
                            except Exception as Error:
                                await ("There was an error when checking static data")
                                return

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

    elif chanId == chanIds["orderDisplay"]:
        if message.content.startswith('!report'):

            message_hist = await message.channel.history().flatten()
            for msg in message_hist:
                if str(msg.author) != 'Tockz#0001': #Put in limited time exception to deleting tockz old messages
                    await DeleteMessageFromChannel(message.channel,msg)

            db = staticsDb()
            orders_list = db.FetchAllMembersList()
            for order in orders_list:
                members = None
                if order[3] is not None:
                    members = order[3].split(",")
                
                co_lead = "No Colead"
                if order[2] is not None:
                    co_lead = order[2]

                out_message = (f'** {order[0].capitalize()} ** \n'
                            f'```\n'
                            f'RED [Captain]\n'
                            f'{order[1]}\n'
                            f'RED [Knight]\n'
                            f'{co_lead}\n'
                            f'RED [Members]\n'
                )

                if members is not None:
                    for member in members:
                        out_message += f'{member} \n'
                else:
                    out_message += "No Members \n"

                out_message += '__________________'
                out_message += '```'
                await message.channel.send(out_message)
        return

# Delete the message from the given reaction's channel
async def DeleteMessageFromChannel(channel, msg, sleepTime=0):
    time.sleep(sleepTime)
    await channel.delete_messages([msg])

async def GetGame(message, db):
    """ Fetches the game from the messages channel """
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
        if msg.content in games:
            game = msg.content
            await message.channel.send('Processing....')
        else:
            await message.channel.send('Game is not in the list. If this is an error contact Seyon or Tockz.')
            return None
    except asyncio.TimeoutError:
        await message.channel.send('Operation has timed out. You will need to start the creation process.')
        return None



client.run(TOKEN)
