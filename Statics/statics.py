class StaticData:
    """ Object for static data transfer """
    def __init__(self):
        self.id = 0
        self.static_name = ""
        self.static_lead = ""
        self.static_colead = ""
        self.discord_id = ""
        self.chat_id = ""
        self.static_size = 0

    def from_query(self, query_data):
        """ Sets fields from the query data tuple """
        self.id = query_data[0] # Cannot be null
        self.static_name = query_data[1] # Cannot be null
        self.static_lead = query_data[2] # Cannot be null
        self.static_colead = query_data[3]
        self.discord_id = query_data[4] # Discord role Id
        self.chat_id = query_data[5] # Discord Chat Id
        self.static_size = query_data[6] # Current size of static, currently limited to 8. Cannot be null

class Static:
    def __init__(self, data: StaticData = StaticData()):
        self.id = data.id
        self.static_name = data.static_name
        self.static_lead = data.static_lead
        self.static_colead = data.static_colead
        self.discord_id = data.discord_id
        self.chat_id = data.chat_id
        self.static_size = data.static_size