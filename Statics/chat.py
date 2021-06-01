import asyncio
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

    async def CreateChat(self, guild, channelName, category):
        chan = None
        if str.lower(self.chat_type) == 'text':\
            chan = await guild.create_text_channel(channelName, category=category)
        if str.lower(self.chat_type) == 'voice':
            chan = await guild.create_voice_channel(channelName, category=category)
            
        self.chat_id = chan.id
