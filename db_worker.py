import sqlite3
from datetime import datetime
from time import time

from logger import logger


class DB():

    def __init__(self, filename):
        '''
        DataBase manager
        
        :param filename - name of database file
        '''
        self.filename = filename
        logger.info('')
        
        
    def query(self, sql, iterable=()):
        '''
        Querying database

        :param sql - sql query
        :param iterable - values
        :return - list of querying rows
        '''
        logger.info('sql={}; values={}'.format(sql, iterable))
        try:
            con = sqlite3.Connection(self.filename)
            cur = sqlite3.Cursor(con)
            rows = cur.execute(sql, iterable).fetchall()
            con.commit()
            con.close()
            return rows
        except Exception as e:
            logger.exception(e)


    def is_user(self, tg_id):
        '''
        Сhecks whether the user in the DB

        :param tg_id - telegram ID
        :return - user ID or NULL
        '''
        logger.info('tg_id={}'.format(tg_id))
        try:
            user_id = self.query('SELECT id FROM Users WHERE tg_id=?', (tg_id,))
            return user_id
        except Exception as e:
            logger.exception(e)


    def add_user(self, tg_id):
        '''
        Adding user in DB

        :param tg_id - telegram ID
        :return:
        '''
        logger.info('tg_id={}'.format(tg_id))
        try:
            if not self.is_user(tg_id):
                self.query('INSERT INTO Users (tg_id) VALUES (?)', (tg_id,))
                user_id = self.is_user(tg_id)[0][0]
                self.query('INSERT INTO Settings (user_id) VALUES (?)', (user_id,))

                # sets default notifications schedule
                values = ''
                for i in range(1, 24):
                    values += f',({user_id}, {i})'
                self.query(f'INSERT INTO Notify_Time VALUES({user_id}, 0)' + values)
        except Exception as e:
            logger.exception(e)


    def get_recipients(self):
        '''
        Gets users whose schedule coincides with the current time

        :return - list of (user ID, coins number)
        '''
        logger.info('')
        try:
            h = datetime.fromtimestamp(time()).hour
            users = [row for row in self.query('''SELECT tg_id, coins_number FROM Users as u
                                                    JOIN Notify_Time as nt on u.id=nt.user_id
                                                    JOIN Settings as s on u.id=s.user_id
                                                    WHERE nt.hour=?''', (h,))]
            return users
        except Exception as e:
            logger.exception(e)


    def get_schedule(self, tg_id):
        '''
        Gets user's schedule of notifications
        
        :param tg_id - telegram ID
        :return - list of hours
        '''
        logger.info('tg_id={}'.format(tg_id))
        try:
            user_id = self.is_user(tg_id)[0][0]
            schedule = [val[0] for val in self.query('SELECT hour FROM Notify_Time WHERE user_id=? ORDER BY hour ASC', (user_id,))]
            return schedule
        except Exception as e:
            logger.exception(e)


    def get_top_coins_number(self, tg_id):
        '''
        Gets user's TOP coins number

        :param tg_id - telegram ID
        :return - number of TOP coins
        '''
        logger.info('tg_id={}'.format(tg_id))
        try:
            user_id = self.is_user(tg_id)[0][0]
            n = self.query('SELECT coins_number FROM Settings WHERE user_id=?', (user_id,))[0][0]
            return n
        except Exception as e:
            logger.exception(e)


    def save_settings(self, tg_id, field, val):
        '''
        Saves user settings

        :param tg_id - telegram ID
        :param field - table field
        :param val - new value
        :return - True/False
        '''
        logger.info('tg_id={}; field={}; value={}'.format(tg_id, field, val))
        try:
            user_id = self.is_user(tg_id)[0][0]
            self.query(f'UPDATE Settings SET {field}=? WHERE user_id=?', (val, user_id,))
            return True
        except Exception as e:
            logger.exception(e)
            return False


    def edit_schedule(self, tg_id, args):
        '''
        Edits users schedule of notifications

        :param tg_id - telegram ID
        :param args - list of hours
        '''
        logger.info('tg_id={}; args={}'.format(tg_id, args))
        try:
            user_id = self.is_user(tg_id)[0][0]
            self.query('DELETE FROM Notify_Time WHERE user_id=?', (user_id,))
            values = ''
            arg1 = args.pop()
            for n in args:
                values += f',({user_id}, {n})'
            self.query('INSERT INTO Notify_Time VALUES(?, ?)' + values, (user_id, arg1))
            return True
        except Exception as e:
            logger.exception(e)
            return False