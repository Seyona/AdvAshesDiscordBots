class Chat:
    def __init__(self):
        # Discord Chat Id
        self.chat_id = None
        # Type of chat (Text/Voice)
        self.chat_type = None
        # Name of the Static the chat belongs to
        self.static_name = None
    
    def from_query(self, queryData):
        """ Takes an array of data from a query and sets the values to the object"""
        self.chat_id = queryData[0]
        self.chat_type = queryData[0]
        self.static_name = queryData[0]
