import re
from helpers import eventFormatMessage

class EventData:
    """ Object for event data transfer """
    def __init__(self):
        self.id = 0
        self.event_name = ""
        self.event_date = None
        self.recurring = False
        self.recurrence_rate = 0
        self.description = ""
        self.disc_messageId = 0

    def from_query(self, query_data):
        """ Sets fields from the query data tuple """
        self.id = query_data[0]
        self.event_name = query_data[1]
        self.event_date = query_data[2]
        self.recurring = query_data[3]
        self.recurrence_rate = query_data[4]
        self.description = query_data[5]
        self.disc_messageId = query_data[6]


class Event:
    def __init__(self, data: EventData = EventData()):
        self.id = data.id
        self.event_name = data.event_name
        self.event_date = data.event_date
        self.recurring = data.recurring
        self.recurrence_rate = data.recurrence_rate
        self.description = data.description
        self.disc_messageId = data.disc_messageId

    def from_message(self, message):
        """ Sets fields to values parsed from the given message """

        errors = []
        eventSplit = message.content.split(' ')
        lenOfSplit = len(eventSplit)

        timeOfEvent = eventSplit[lenOfSplit - 1]
        dateOfEvent = eventSplit[lenOfSplit - 2]
        eventName = ''.join(eventSplit[1:(lenOfSplit - 2)])

        if not re.match(r"^[0-2][0-3][0-5][0-9]$", timeOfEvent):
            errors.append("Time")

        if not re.match(r"^\d{1,2}\/\d{1,2}", dateOfEvent):
            errors.append("Date")

        if errors:
            return "Issue parsing: " + ','.join(errors) + f'\n make sure you are using the proper format {eventFormatMessage}'
        else:
            self.event_name = eventName
            return ""

    def isValid(self):
        valid = self.event_name != "" and self.event_date is not None and self.description != ""
        if not self.recurring:
            return valid
        else:
            return valid and self.recurrence_rate != 0


