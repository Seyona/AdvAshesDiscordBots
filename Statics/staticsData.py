class StaticData:
    """ Object for static data transfer """
    def __init__(self):
        self.id = 0
        self.static_name = ""
        self.static_lead = ""
        self.static_colead = None
        self.discord_id = None
        self.chat_id = None
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