import psycopg2
import logging
import pytz, datetime

from dbconfig import config
from helpers import baseDir
from Statics.staticsData import StaticData


class staticsDb:
    """ Contains all data reading and manipulation logic for the database """

    def __init__(self):
        self.dbConf = config()
        logging.basicConfig(filename=baseDir + 'Logs/' + 'statics.log', format='%(name)s - %(levelname)s - %(message)s')

    def createNewStatic(self, static):
        """ 
            Creates a new static 
            Returns True on success, False otherwise
        """

        sql = """INSERT INTO statics (static_name, lead_name, static_size) 
        VALUES(%s, %s, %s) RETURNING static_id"""

        conn = None
        retId = None
        try:

            existingStatic = self.GetStaticDataByName(static.static_name) #Check if a static of this name exists

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

    def GetStaticDataByName(self, static_name):
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

    def GetUserStaticData(self, username, static_name):
        """
            Gets User static data 
            Returns Tuple (discord_name, static_name), if user exists, else None
        """
        
        sql = f'SELECT discord_name, static_name FROM static_users WHERE discord_name = \'{username}\' and static_name = \'{static_name}\''

        try:
            params =self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()
            cur.execute(sql)

            row = cur.fetchone()
            if row: # User Exists
                return row[0], row[1]
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

    def GetUsersStatics(self, username):
        """ Checks if a user is in any static """
        inStatic = False
        sql = f'Select * from games where discord_name = \'{username}\''
        try: 
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()

            cur.execute(sql)
            row = cur.fetchone()

            if row != None:
                inStatic = True
                
            conn.commit()
            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when checking static status for user {username}')
            raise error
        finally:
            if conn is not None:
                conn.close()
            return inStatic


    def IsInGivenStatic(self, username, static_name):
        """
            Checks if a user is in a given static
        """
        user = self.GetUserStaticData(username, static_name)
        if user and user[1] == static_name:
            return True
        else:
            return False

    def StaticHasSpace(self, static_name):
        """ Checks if a static has space for members """
        static = self.GetStaticDataByName(static_name)
        if static:
            return static.static_size < 8
        else:
            return False

    def GetAllUsersInStatic(self, static_name):
        """ Gets a list of all users in a static 
            Returns a list of user names 
        """
        conn = None
        users = []
        sql = f'SELECT discord_name from static_users where static_name= {static_name}'
        try:
      
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()

            cur.execute(sql)
            rows = cur.fetchall()

            for row in rows:
                user = row
                users.append(user)

            conn.commit()
            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when fetching all users for static {static_name} :: {error} \n')
            raise error
        finally:
            if conn is not None:
                conn.close()

        return users

    def DropUserFromStatic(self, static_name, userName):
        """ Drops a given user from a static """
        sql = f'DELETE FROM static_users where discord_name = \'{userName}\' and static_name = \'{static_name}\''
        try:
      
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()
            cur.execute(sql)

            conn.commit()
            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when removing user, {userName},  from static {static_name} :: {error} \n')
            raise error
        finally:
            if conn is not None:
                conn.close()

        return True

    def dropStatic(self, static_name):
        """ Drops the passed static """
        static = self.GetStaticDataByName(static_name)
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
        sql = f'UPDATE statics SET {sqlSet} WHERE static_id = \'{static_id}\''
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

        usersSql = """INSERT INTO static_users (discord_name, static_name) 
        VALUES(%s, %s)"""

        updateCount = f'UPDATE statics SET static_size = static_size + 1 WHERE static_name = \'{static_name}\''

        conn = None

        try:

            static = self.GetStaticDataByName(static_name) #Check if a static of this name exists

            if not (static):
                return "Static does not exist"

            if self.IsInGivenStatic(discordName, static_name):
                return "You are already in the static"
            
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()
            cur.execute(usersSql, (discordName, static_name)) 
            cur.execute(updateCount)

            conn.commit()
            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when adding user:{discordName} to static {static_name} :: {error}')
            raise error
        finally:
            if conn is not None:
                conn.close()

        return ""

    def CheckIsCoLead(self, username):
        """ Checks if a given user is a co_lead in ANY static """
        sql = f'SELECT colead_name from statics where colead_name = \'{username}\''
        try:
            params =self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()
            cur.execute(sql)

            row = cur.fetchone()
            if row: # User Exists in some static
                return row[0], row[1]
            else:
                return None
                
        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when checking if user {username} was co_lead anywhere :: {error}')
            raise error
        finally:
            if conn is not None:
                conn.close()

    def GetGames(self):
        """ Fetches a list of active games """

        gamesSql = "Select game_name from games where active = True"
        conn = None
        activeGames = []

        try:
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()
            cur.execute(gamesSql) 
            
            rows = cur.fetchall()

            for row in rows: # Row is a tuple, 0th index is the name
                game = row[0]
                activeGames.append(game)

            conn.commit()
            cur.close()
            
            return activeGames

        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when fetching games: {error}')
            return []
        finally:
            if conn is not None:
                conn.close()
            return activeGames

    def Create_chat_channel(self, chat):
        sql = """ INSERT INTO chats(chat_id, chat_type, static_name) VALUES (%s, %s, %s) """ 
        conn = None
        try:
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()

            cur.execute(sql, (chat.chat_id, chat.chat_type, chat.static_name))

            conn.commit()
            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when creating new chat {error}')
            raise error
        finally:
            if conn is not None:
                conn.close()

    def FetchAllMembersList(self):
        """
        Fetch a list of all orders and their members
        """ 

        query = """
            select static_name, lead_name, colead_name,
            (select string_agg(discord_name, ',') as members 
                from static_users su 
                where su.static_name = s.static_name and su.discord_name <> s.lead_name and su.discord_name <> s.colead_name)
            from statics s;
        """
        conn = None
        orders = []

        try:
            params = self.dbConf
            conn = psycopg2.connect(**params)

            cur = conn.cursor()
            cur.execute(query) 
            
            orders = cur.fetchall()

            conn.commit()
            cur.close()

        except(Exception, psycopg2.DatabaseError) as error:
            logging.error(f'Error when fetching games: {error}')
            return []
        finally:
            if conn is not None:
                conn.close()
            return orders
        