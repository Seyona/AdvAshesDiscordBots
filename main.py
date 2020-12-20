#!/usr/bin/python3
# Discord requirements
import discord
import os
# End Discord requirements

import json
import time
import re
from Events.events import Event

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
    "events": 738276488851226715
}


# pull ids into memory
with open(baseDir + 'NonPythonFiles/discordIds.json') as json_file:
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
        await RolesManager.ReactionAdded(reaction.message, user)

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


# Delete the message from the given reaction's channel
async def DeleteMessageFromChannel(channel, msg, sleepTime=0):
    time.sleep(sleepTime)
    await channel.delete_messages([msg])


client.run(TOKEN)
