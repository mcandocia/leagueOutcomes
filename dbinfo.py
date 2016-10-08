import psycopg2

password='pw'
database='leaguedb'
user='djmax'
host='localhost'
port=5432

class Database(object):
    def __init__(self):
        self.conn = psycopg2.connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cur = self.conn.cursor()
