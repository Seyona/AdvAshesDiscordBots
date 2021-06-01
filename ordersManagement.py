import discord 
import asyncio
from Statics.staticsDb import staticsDb
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
            
            errorMsg = 'Error while creating text chat'
            await text_chat.CreateChat(guild, new_chan_name, category)
            
            errorMsg = 'Error while creating voice chat'
            await voice_chat.CreateChat(guild, new_chan_name, category)

            errorMsg = 'Error while creating discord role'
            role = await guild.create_role(name=role_name)
            order.discord_id = role.id

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

