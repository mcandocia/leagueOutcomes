import psycopg2

class Database(object):
    def __init__(self):
        self.conn = psycopg2.connect(
            database='leaguedb',
            user='djmax',
            password='notapassword',
            host='localhost',
            port=5432
        )
        self.cur = self.conn.cursor()
