import psycopg2
import sys
import os
import re
os.chdir('/home/max/workspace/league/')
#some changes are made, so it's easier to keep the file in this sort of directory
from riotwatcher import riotwatcher
from api_info import API_KEY
from random import randint
import time
from datetime import datetime
from collections import deque
import json
from dbinfo import Database
import requests

def hilite(string, status, bold = True):
    attr = []
    if status==0:
        # green
        attr.append('42')
    elif status==1:
        # red
        attr.append('41')
    elif status==2:
        #yellow
        attr.append('43')
    if bold:
        attr.append('1')
    return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)

def main(*args, **kwargs):
    print 'initializing...'
    watcher = riotwatcher.RiotWatcher(API_KEY)
    db1 = Database()
    conn = db1.conn
    cur = db1.cur
    db2 = Database()
    fetcher_conn = db2.conn
    fetcher_cur = db2.cur
    #created new table because bug in bans extraction (duplicated 0 index)
    cur.execute("""CREATE TABLE IF NOT EXISTS matchinfo(
    queueType VARCHAR(40),
    matchVersion VARCHAR(30),
    season VARCHAR(20),
    game_id BIGINT,
    ban1 INTEGER,
    ban2 INTEGER,
    ban3 INTEGER,
    ban4 INTEGER,
    ban5 INTEGER,
    ban6 INTEGER,
    teams_data JSONB,
    participants_data JSONB,
    participants_identities JSONB,
    duration INTEGER,
    region VARCHAR(12),
    platformId VARCHAR(12),
    mapId INTEGER,
    matchMode VARCHAR(20),
    timestamp TIMESTAMP,
    PRIMARY KEY (game_id)
    );""")
    conn.commit()
    cur.execute("""CREATE INDEX IF NOT EXISTS match_gameid 
    ON matchinfo (game_id);""")
    conn.commit()
    cur.execute("""CREATE INDEX IF NOT EXISTS game_gameid 
    ON gameinfo (game_id);""")
    conn.commit()
    cur.execute("""CREATE INDEX IF NOT EXISTS game_subtype 
    ON gameinfo (subtype);""")
    conn.commit()
    print 'indexes complete'
    fetcher_cur.execute("""
    SELECT game_id FROM gameinfo as gi WHERE (NOT EXISTS
    (SELECT mi.game_id FROM matchinfo as mi WHERE 
    gi.game_id = mi.game_id)) AND
    subtype = ANY('{RANKED_TEAM_5x5,
    RANKED_SOLO_5x5,RANKED_TEAM_3x3}'::text[])
    ;--ORDER BY timestamp;"""
    )
    print 'id fetcher set'
    game_id_set = set()
    while True:
        timestamp = datetime.now()
        #game_id = randint(1,2.3e10)
        game_id = fetcher_cur.fetchone()[0]
        if game_id in game_id_set:
            continue
        try:
            time.sleep(1.5)
            match = watcher.get_match(game_id)
            input_dict = {}
            for key in ['queueType','matchVersion','season','region','mapId',
                        'matchMode','platformId']:
                input_dict[key] = match[key]
            input_dict['duration'] = match['matchDuration']
            input_dict['teams_data'] = json.dumps(match['teams'])
            input_dict['participants_data'] = json.dumps(match['participants'])
            input_dict['participants_identities'] = json.dumps(match['participantIdentities'])
            input_dict['timestamp'] = timestamp
            input_dict['game_id'] = game_id
            bans1 = match['teams'][0].get('bans', None)
            bans2 = match['teams'][1].get('bans', None)
            if bans1 and bans2:
                bans = bans1 + bans2
                for ban in bans:
                    banint = ban['pickTurn']
                    if banint in range(1,7):
                        input_dict['ban' + str(banint)] = ban['championId']
            for key in ['ban' + str(x) for x in range(1,7)]:
                input_dict[key] = input_dict.get(key, None)
            cols = input_dict.keys()
            vals_str = ', '.join(['%s'] * len(cols))
            values = [input_dict[x] for x in cols]
            cols2 = re.sub("'",'',str(cols)[1:-1])
            statement = """INSERT INTO matchinfo({cols}) VALUES({vals_str});"""\
                .format(cols=cols2, vals_str = vals_str)
            cur.execute(statement, values)
            conn.commit()
            print hilite('added game id: %d' % game_id, 0)
            game_id_set.add(game_id)
        except psycopg2.IntegrityError:
            print 'error...'
            print statement
            print sys.exc_info()
            time.sleep(0.5)
            #end transaction_block
            conn.rollback()
        except riotwatcher.LoLException as e:
            print sys.exc_info()
            print e.headers
            print e.error
            print hilite('game id~~~%d' % game_id, 1)
            if e.error == "Game data not found":
                continue
            time.sleep(0.5)
        except requests.exceptions.ConnectionError:
            print 'connection issue, sleeping for 15 seconds...'
            time.sleep(15)
    conn.close()
    fetcher_conn.close()
     

if __name__=='__main__':    
    main(sys.argv[1:])
