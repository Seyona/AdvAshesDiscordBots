import psycopg2
import logging
import pytz, datetime

from dbconfig import config
from helpers import baseDir
from Statics.staticsData import StaticData


class staticsDb:
    """ Contains all data reading and manipulation logic for the static based tables """

    def __init__(self):
        self.dbConf = config()
        logging.basicConfig(filename=baseDir + 'Logs/' + 'statics.log', format='%(name)s - %(levelname)s - %(message)s')

    def createNewStatic(self, static):
        """ 
            Creates a new static 
            Returns True on success, False otherwise
        """

        sql = """INSERT INTO statics (static_name, leader_name, static_size) 
        VALUES(%s, %s, %s) RETURNING static_id"""

        conn = None
        retId = None
        try:

            existingStatic = self.GetStaticData(static.static_name) #Check if a static of this name exists

            if (existingStatic):
                return False
            
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()

            cur.execute(sql, (static.static_name, static.static_lead, static.static_size))

            retId = cur.fetchone()[0]

            conn.commit()
            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when creating new static {error}')
            raise error
        finally:
            if conn is not None:
                conn.close()

        return retId

    def GetStaticData(self, static_name):
        """
            Gets Static Data
            Returns StaticData object, if exists, otherwise None
        """
        sql = f'SELECT * FROM statics WHERE static_name = \'{static_name}\''

        try:
            params =self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()
            cur.execute(sql)

            row = cur.fetchone()
            if row: # static Exists
                data = StaticData()
                data.from_query(row)
                return data
            else:
                return None
                
        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when fetching static {static_name} :: {error}')
            raise error
        finally:
            if conn is not None:
                conn.close()

    def GetUserStaticData(self, username):
        """
            Gets User static data 
            Returns Tuple (discord_name, static_id), if user exists, else None
        """
        
        sql = f'SELECT username, static_id FROM static_users WHERE discord_name = \'{username}\''

        try:
            params =self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()
            cur.execute(sql)

            row = cur.fetchone()
            if row: # User Exists
                return (row[0],row(1))
            else:
                return None
                
        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when fetching user data for {username} :: {error}')
            raise error
        finally:
            if conn is not None:
                conn.close()

    def IsInAStatic(self, username):
        """
            Checks if a user is in any static
        """

        user = self.GetUserStaticData(username)
        if user:
            return True
        else:
            return False

    def IsInGivenStatic(self, username, static_name):
        """
            Checks if a user is in a given static
        """
        user = self.GetUserStaticData(username)
        if user[1] == static_name:
            return True
        else:
            return False

    def StaticHasSpace(self, static_name):
        """ Checks if a static has space for members """
        static = self.GetStaticData(static_name)
        if static:
            return static.static_size < 8
        else:
            return False

    def dropStatic(self, static_name):
        """ Drops the passed static """
        static = self.GetStaticData(static_name)
        if static:
            if static.static_size > 1:
                return 'Static should be empty before deleting'
            else:
                sql = f'DELETE from statics where static_name = \'{static_name}\''
                try:
                    params = self.dbConf
                    conn = psycopg2.connect(**params)

                    cur = conn.cursor()

                    cur.execute(sql)

                    conn.commit()
                    cur.close()

                except(Exception, psycopg2.DatabaseError) as error:
                    logging.warning(f'Error when Deleting {static_name} :: {error}')
                    raise error
                finally:
                    if conn is not None:
                        conn.close()
                return ""

        else:
            return 'Static \'{static_name}\' does not exist'

    def UpdateStaticRow(self, sqlSet, static_id):
        """ Updates row based on the passed sqlSet str """ 
        conn = None
        sql = f'UPDATE statics {sqlSet} WHERE static_id = \'{static_id}\''
        try:
      
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()

            cur.execute(sql)

            conn.commit()
            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when updating static data for {static_id} :: {error}')
            raise error
        finally:
            if conn is not None:
                conn.close()

        return True

    def AddUserToStatic(self, discordName, static_name):
        """ creates a user in the static_users table """

        sql = """INSERT INTO static_users (discord_name, static_id) 
        VALUES(%s, %s) RETURNING player_id"""

        conn = None

        try:

            static = self.GetStaticData(static_name) #Check if a static of this name exists

            if not (static):
                return "Static does not exist"

            if self.IsInGivenStatic(discordName, static_name):
                return "You are already in the static"

            if self.IsInAStatic(discordName):
                return "You are already in a static"
            
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()
            cur.execute(sql, (discordName, static_name)) 

            conn.commit()
            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when adding user:{discordName} to static {static_name} :: {error}')
            raise error
        finally:
            if conn is not None:
                conn.close()

        return ""
