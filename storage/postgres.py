import logging
import os
import time

import psycopg2
from psycopg2.extras import DictCursor


class DB:
    def __init__(self,
                 user: str,
                 password: str,
                 host: str,
                 port: str,
                 database: str,
                 reconnect: bool = True,
                 limit_reties: int = 0):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.database = database

        self.reconnect = reconnect
        self.limit_reties = limit_reties

        self._connection = None

        self.init()

    def connect(self, retry_counter=0):
        if not self._connection:
            try:
                self._connection = psycopg2.connect(user=self.user, password=self.password, host=self.host,
                                                    port=self.port, database=self.database, connect_timeout=3, )
                retry_counter = 0
                self._connection.autocommit = True
                return self._connection
            except psycopg2.OperationalError as error:
                if not self.reconnect or retry_counter >= self.limit_reties:
                    raise error
                else:
                    retry_counter += 1
                    logging.error("Got error {}. Reconnecting {}.".format(str(error).strip(), retry_counter))
                    time.sleep(5)
                    self.connect(retry_counter)
            except (Exception, psycopg2.Error) as error:
                raise error

    def execute(self, query, vars=None, retry_counter=0):
        try:
            with self._connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, vars)
                if cursor.description:
                    result = cursor.fetchall()
                    return result
                return []
        except (psycopg2.DatabaseError, psycopg2.OperationalError) as error:
            logging.error(f'Error during SQL request: {query} {vars}')
            logging.exception(error)
            if retry_counter >= self.limit_reties:
                raise error
            else:
                retry_counter += 1
                logging.error("Got error {}. Retrying {}.".format(str(error).strip(), retry_counter))
                time.sleep(1)
                self.reset()
                return self.execute(query, vars, retry_counter)
        except (Exception, psycopg2.Error) as error:
            raise error

    def reset(self):
        self.close()
        self.connect()

    def close(self):
        if self._connection:
            self._connection.close()
            logging.info("PostgreSQL connection is closed.")
        self._connection = None

    def init(self):
        self.connect()


db = DB(os.environ["POSTGRES_USER"],
        os.environ["POSTGRES_PASSWORD"],
        os.environ["POSTGRES_HOST"],
        os.environ["POSTGRES_PORT"],
        os.environ["POSTGRES_DB"])
