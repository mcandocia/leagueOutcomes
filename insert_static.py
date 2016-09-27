import psycopg2
from api_info import API_KEY
from riotwatcher.riotwatcher import RiotWatcher

def main():
    conn = psycopg2.connect(
        database='leaguedb',
        user='djmax',
        password='pw',
        host='localhost',
        port=5432
    )
    cur = self.conn.cursor()
    watcher = RiotWatcher(API_KEY)
    data = watcher.static_get_champion_list()['data']
    cur.execute
    cur.execute('''CREATE TABLE static_champions
        (key VARCHAR(30), name VARCHAR(30), id INTEGER, title VARCHAR(40));''')
    for key, entry in d.iteritems():
        cur.execute("""INSERT INTO static_champions(key, name, id, title) 
        VALUES(%s, %s, %s, %s);""", 
                    (entry['key'], entry['name'], entry['id'], entry['title']))
    conn.commit()
    print 'entered champion info to database'

if __name__=="__main__":
    main()
