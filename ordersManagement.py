import discord 
import asyncio
import re

from Statics.staticsDb import staticsDb
from Statics.statics import Static
from Statics.staticsManagement import StaticsManagement
from Statics.chat import Chat
from psycopg2 import DatabaseError

""" Class for Orders and their management """
async def StartOrder(order, guild):
    """ 
        Checks order information and creates it 
        Cannot create an order if one of the same name exists

        Returns a tuple containing the updated order and the newly created discord role object
    """
    db = staticsDb()
    text_chat = Chat('text')
    voice_chat = Chat('voice')

    errorMsg = "There was an exception while checking your Order status"
    try:
        if order.static_exists():
            raise NameError('Order already exists')
        else:
            errorMsg = 'Error when creating Order'
            order.create()
            errorMsg = 'Error when Initializing order role info'

            errorMsg = 'Error when fetching discord category'
            
            text_chat.static_name = order.static_name
            voice_chat.static_name = order.static_name

            category = discord.utils.get(guild.categories, name='◇──◇Orders◇──◇')
            role_name = f'{order.static_name}'
            new_chan_name = f'{order.static_name}'
            
            errorMsg = 'Error while creating discord role'
            role = await guild.create_role(name=role_name)
            order.discord_id = role.id

            errorMsg = 'Error while creating text chat'
            await text_chat.CreateChat(guild, new_chan_name, category, role)
            
            errorMsg = 'Error while creating voice chat'
            await voice_chat.CreateChat(guild, new_chan_name, category, role)



            # Create entries in Chat table 
            text_chat.static_name = order.static_name
            voice_chat.static_name = order.static_name

            errorMsg = 'Error while creating voice/text channel'
            db.Create_chat_channel(text_chat)
            db.Create_chat_channel(voice_chat)

            errorMsg = 'Error while updating static info'
            order.Update()
            return (order, role)

    except(Exception, DatabaseError) as error:
        raise Exception(errorMsg)

    return

def JoinGame(order_name, game_name):
    """ Adds an entry to 'Static_games' table """
    return

def JoinOrder(order_name, user):
    """ Adds a user to an order if they are not already in it"""
    db = staticsDb()

    msg = db.AddUserToStatic(str(user), order_name)

    if msg != "":
        raise Exception(msg)

async def PromoteCoLead(static_data, discord_name, adding_user, adding_user_is_officer, discData, role_manager):
    """ Promotes a user to co_lead for a given order 
        static_data: Data for the static that is being modified 
        discord_name: Name of the co_lead in discord
        adding_user: user that is attempting the prompotion, should be from the same order unless it is a discord officier
        adding_user_is_officer: boolean to siginify if the user sending the message is an officer
        discData: Discord channel data
        role_manager: Initialized role manager
    """
    db = staticsDb()

    properFormat = re.match(r".*#\d{4}$", discord_name)
    staticData = None

    if properFormat:
        colead_staticData = db.GetUserStaticData(discord_name, static_data.static_name)
        adding_userData = None 

        if not colead_staticData: # No data for the specified static was found
            raise Exception(f'User: {discord_name} is not in order {static_data.static_name} and cannot be promoted to co-lead')

        if not adding_user_is_officer: #The user making the change is not an officer in the discord
            adding_userData = db.GetUserStaticData(adding_user, static_data.static_name)
            if not adding_userData: # No data for the specific static was found...
                raise Exception(f'Cannot promote User: {discord_name} because you are not in the specified Order')

            #Check if adding user is the leader of the order and
            if staticData.static_lead != adding_user:
                raise Exception(f'Cannot promote User:{discord_name} because you are not the order\'s leader')

        static_data.static_colead = discord_name
        staticObj = Static(static_data)
        staticObj.Update()

        role_manager.AddAddColeadRole(discord_name)

        previous_colead = static_data.static_colead
        if previous_colead != 'None':
            splitname = previous_colead.static_colead.split('#')
            discord.utils.get(discData.members, name=splitname[0], discriminator=splitname[1])

            if not db.CheckIsCoLead: # User is no longer a co_lead of any static, remove their role
                role_manager.RemoveColeadRole(previous_colead)
    else:
        raise NameError("Invalid format, should be like !addcolead Seyon#1392")




