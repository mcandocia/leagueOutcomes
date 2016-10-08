import psycopg2
from api_info import API_KEY
from riotwatcher.riotwatcher import RiotWatcher
from dbinfo import Database
def main():
    db = Database()
    conn = db.conn
    cur = db.cur
    watcher = RiotWatcher(API_KEY)
    data = watcher.static_get_champion_list()['data']
    cur.execute("DROP TABLE IF EXISTS static_champions;")
    conn.commit()
    cur.execute('''CREATE TABLE static_champions
        (key VARCHAR(30), name VARCHAR(30), id INTEGER, title VARCHAR(40));''')
    for key, entry in data.iteritems():
        cur.execute("""INSERT INTO static_champions(key, name, id, title) 
        VALUES(%s, %s, %s, %s);""", 
                    (entry['key'], entry['name'], entry['id'], entry['title']))
    conn.commit()
    print 'entered champion info to database'

if __name__=="__main__":
    main()
