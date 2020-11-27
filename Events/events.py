class EventData:
    """ Object for event data transfer """
    def __init__(self):
        self.id = 0
        self.event_name = ""
        self.event_date = None
        self.recurring = False
        self.recurrence_rate = 0
        self.description = ""


class Event:
    def __init__(self, data: EventData = EventData()):
        self.id = data.id
        self.event_name = data.event_name
        self.event_date = data.event_date
        self.recurring = data.recurring
        self.recurrence_rate = data.recurrence_rate
        self.description = data.description

    def isValid(self):
        valid = self.id != 0 and self.event_name != "" and self.event_date is not None and self.description != ""
        if not self.recurring:
            return valid
        else:
            return valid and self.recurrence_rate != 0


