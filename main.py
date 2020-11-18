#!/usr/bin/python3
# Discord requirements
import discord
import os
# End Discord requirements

import json
import time
import re
from classRolesManagement import AshesRolesManager
from spreadsheet import Spreadsheet

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
    "events": 738276488851226715
}

# Events stored by ID mapping to a string.
# Users will react to the message and the message ID will add them to a spreadsheet
events = {}

eventsFile = 'events.json'

# pull ids into memory
with open('/discordBot/AdvAshesDiscordBots/discordIds.json') as json_file:
    discordIds = json.load(json_file)

RolesManager = None
googleSheet = None


# On ready prep function
@client.event
async def on_ready():
    # global calls so we can modify these variables
    global isReady
    global RolesManager
    global googleSheet

    loadEventsFromFile()

    print(f'{client.user} has connected to Discord')

    for guild in client.guilds:
        if guild.name == GUILD:
            break

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
        RolesManager.ReactionAdded(reaction.message, user)

    elif chanId == chanIds["events"]:
        return


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
                eventName = ''.join(eventSplit[1:(lenOfSplit - 2)])

                properFormat = "!create Event Name mm/dd hhmm (military time)"

                timeErrStr = f'Time is invalid or non-existent :: {properFormat}'
                if not re.match(r"^[0-2][0-3][0-5][0-9]$", timeOfEvent):
                    await message.channel.send(timeErrStr)
                    return

                eventTimeAsInt = int(timeOfEvent)

                if not re.match(r"^\d{1,2}\/\d{1,2}", dateOfEvent):
                    await message.channel.send(f'Date is invalid or non-existent :: {properFormat}')
                    return

                events[message.id] = eventName
                #eventsWorksheet = sheet.add_worksheet(title=eventName, rows=500, cols=7)
                #eventsWorksheet.update('A1:F1', ['DiscordTag', 'Attended', 'Date', dateOfEvent, 'Time', eventTimeAsInt])

                writeEventsToFile()  # save the current events dict to file in case of program crash
                await message.channel.send(
                    f'An event called <{eventName}> has been scheduled for {dateOfEvent} at {eventTimeAsInt}')
            else:
                await message.channel.send("There is already an event of that name created")

        elif message.content.startswith('!events'):
            return
        elif message.content.startswith('!startevent'):
            return


# Delete the message from the given reaction's channel
async def DeleteMessageFromChannel(channel, msg, sleepTime=0):
    time.sleep(sleepTime)
    await channel.delete_messages([msg])


# removes an existing events.json file and replaces it with an updated version of the events dictionary
def writeEventsToFile():
    os.remove(f'/discordBot/AdvAshesDiscordBots/{eventsFile}')
    with open(eventsFile, 'w') as file:
        json.dump(events, file)


def loadEventsFromFile():
    global events
    if os.path.isfile(eventsFile):
        with open(eventsFile) as file:
            events = json.load(file)
    else:
        print("No event file found")


client.run(TOKEN)
