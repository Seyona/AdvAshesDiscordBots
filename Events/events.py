import dateparser
from helpers import eventFormatMessage
import pytz


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

        eventSplit = message.content.split(',')

        recurrenceRate = None
        recurring = False
        if str.lower(eventSplit[3]) == "yes":
            recurring = True
            if len(eventSplit) != 5:
                return (f'No Rate of recurrence was given. Please reference the message format and try again. \n ' \
                        f'Format: {eventFormatMessage}')
            if eventSplit[4].isdigit():
                recurrenceRate = int(eventSplit[4])
            else:
                return f'Rate of recurrence is not a number. Double check your message format {eventFormatMessage}'

        datetimeStr = eventSplit[2]
        eventName = eventSplit[0].split(' ')[1]  # remove the !create from the original split
        # dateparser can be a little slow so we do this last
        eventDt = dateparser.parse(datetimeStr, settings={'TIMEZONE': 'US/Central'})

        if eventDt == "":
            return f'Event date could not be parsed double check your message format {eventFormatMessage}'

        self.event_name = eventName
        self.description = eventSplit[1]
        self.disc_messageId = message.id
        # Store event date as utc
        self.event_date = eventDt.datetime.astimezone(pytz.utc)
        self.recurring = recurring
        self.recurrence_rate = recurrenceRate

        return ""

    def isValid(self):
        valid = self.event_name != "" and self.event_date is not None and self.description != ""
        if not self.recurring:
            return valid
        else:
            return valid and self.recurrence_rate != 0
