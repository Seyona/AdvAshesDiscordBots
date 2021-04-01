from Statics.staticsDb import staticsDb
from Statics.staticsData import StaticData

class Static:
    def __init__(self, data: StaticData = StaticData()):
        self.id = data.id
        self.static_name = data.static_name
        self.static_lead = data.static_lead
        self.static_colead = data.static_colead
        self.discord_id = data.discord_id
        self.chat_id = data.chat_id
        self.static_size = data.static_size

    def from_creation_request(self, message: str, discord_name):
        """ 
            Sets fields to values parsed from the given messsage 
            Message should contain the order name, that is all
        """

        msg_split = [x.strip() for x in message.split(' ', 1)]
        self.id = None
        self.static_name = msg_split[1]
        self.static_lead = discord_name
        self.static_size += 1

    def static_exists(self):
        """ Checks if the current static exists in the database """
        db = staticsDb()

        data = db.GetStaticData(self.static_name)
        if (data):
            return True
        else:
            return False
    
    def Update(self):
        """ Requests to update table entry for static """
        db = staticsDb()
        setStr = (f'static_name = {self.static_name},'
            f'leader_name = {self.static_lead},'
            f'colead_name = {self.static_colead},'
            f'discord_id = {self.discord_id},'
            f'chat_id = {self.chat_id},'
            f'static_size = {self.static_size}')
        db.UpdateStaticRow(setStr, self.id)
