import psycopg2
import logging
import pytz, datetime

from dbconfig import config
from helpers import baseDir
from Statics.Statics import StaticData


class staticsDb:
    """ Contains all data reading and manipulation logic for the static based tables """

    def __init__(self):
        self.dbConf = config()
        logging.basicConfig(filename=baseDir + 'Logs/' + 'statics.log', format='%(name)s - %(levelname)s - %(message)s')

    def createNewStatic(self, static):
        """ Creates a new static """

        sql = """INSERT INTO statics (static_name, static_lead, static_colead,discord_id, chat_id, static_size) 
        VALUES(%s, %s, %s, %s, %s, %s)"""

        conn = None
        eventId = None

        try:
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()

            cur.execute(sql, (static.static_name, static.static_lead, None,
                              None, None, 0))

            eventId = cur.fetchone()[0]

            conn.commit()
            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            raise error
        finally:
            if conn is not None:
                conn.close()

        return static.static_name
