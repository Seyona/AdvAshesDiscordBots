import psycopg2
import logging
import pytz, datetime

from dbconfig import config
from helpers import baseDir


class eventsDb:
    """ Contains all data reading and manipulation logic for the event based tables """

    def __init__(self):
        self.dbConf = config()
        logging.basicConfig(filename=baseDir + 'Logs/' + 'eventdb.log', format='%(name)s - %(levelname)s - %(message)s')

    def create_new_event(self, event):
        """ Creates a new event """

        sql = """INSERT INTO events (event_name, event_date, recurring, recurrence_rate, description) 
        VALUES(%s, %s, %s, %s, %s, %s) RETURNING event_id """

        conn = None
        eventId = None

        try:
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()

            utc_eventdt = event.event_date.astimezone(pytz.utc)

            cur.execute(sql, (event.event_name, utc_eventdt, event.recurring,
                              event.recurrence_rate, event.description))

            eventId = cur.fetchone()[0]

            conn.commit()
            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            raise error
        finally:
            if conn is not None:
                conn.close()

        return eventId
