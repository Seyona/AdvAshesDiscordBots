import psycopg2
import logging
import pytz, datetime

from dbconfig import config
from helpers import baseDir
from Events.events import EventData


class eventsDb:
    """ Contains all data reading and manipulation logic for the event based tables """

    def __init__(self):
        self.dbConf = config()
        logging.basicConfig(filename=baseDir + 'Logs/' + 'eventdb.log', format='%(name)s - %(levelname)s - %(message)s')

    def create_new_event(self, event):
        """ Creates a new event """

        sql = """INSERT INTO events (event_name, event_date, recurring, recurrence_rate, description, disc_messageId) 
        VALUES(%s, %s, %s, %s, %s, %s) RETURNING event_id """

        conn = None
        eventId = None

        try:
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()

            utc_eventdt = event.event_date.astimezone(pytz.utc)

            cur.execute(sql, (event.event_name, utc_eventdt, event.recurring,
                              event.recurrence_rate, event.description, event.disc_messageId))

            eventId = cur.fetchone()[0]

            conn.commit()
            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            raise error
        finally:
            if conn is not None:
                conn.close()

        return eventId

    def get_events_by_name_and_date(self, name, date):
        """ Returns a list of events by the passed name and date """

        sql = """ SELECT * from events where event_name = %s  and event_date = %s """

        conn = None
        events = []
        try:
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()

            cur.execute(sql, name, date)
            eventData = cur.fetchall()
            cur.close()

            for event in eventData:
                data = EventData()
                data.from_query(event)
                events.append(data)

        except(Exception, psycopg2.DatabaseError) as error:
            raise error
        finally:
            if conn is not None:
                conn.close()