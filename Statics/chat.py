import asyncio
from discord import PermissionOverwrite  
from discord.utils import get 
class Chat:
    def __init__(self, chat_type):
        # Discord Chat Id
        self.chat_id = None
        # Type of chat (Text/Voice)
        self.chat_type = chat_type
        # Name of the Static the chat belongs to
        self.static_name = None
    
    def from_query(self, queryData):
        """ Takes an array of data from a query and sets the values to the object """
        self.chat_id = queryData[0]
        self.chat_type = queryData[0]
        self.static_name = queryData[0]

    async def CreateChat(self, guild, channelName, category, discordRole):
        chan = None
        cultistRole = get(guild.roles, name="Cultist")

        if str.lower(self.chat_type) == 'text':

            chan = await guild.create_text_channel(channelName, category=category)
            
            # Set Permissions for the channel
            # List of Permissions can be found here (they are the attributes): https://discordpy.readthedocs.io/en/stable/api.html?highlight=permissionoverwrite#discord.Permissions
            role_overwrite = PermissionOverwrite()
            role_overwrite.view_channel = True
            role_overwrite.read_messages = True
            role_overwrite.send_messages = True

            await chan.set_permissions(discordRole, overwrite=role_overwrite)

            cultist_overwrite = PermissionOverwrite()
            cultist_overwrite.view_channel = False

            await chan.set_permissions(cultistRole, overwrite=cultist_overwrite)

        if str.lower(self.chat_type) == 'voice':
            chan = await guild.create_voice_channel(channelName, category=category)
            await chan.set_permissions(discordRole, view_channel=True, speak=True, stream=True, connect=True)
            await chan.set_permissions(cultistRole, view_channel=True, connect=False, speak=True) # By default they cannot join, but can see who is in it

        self.chat_id = chan.id
