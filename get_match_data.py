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

def main(*args, **kwargs):
    watcher = riotwatcher.RiotWatcher(API_KEY)
    conn = psycopg2.connect(
        database='leaguedb',
        user='djmax',
        password='pw',
        host='localhost',
        port=5432
    )
    cur = conn.cursor()
    fetcher_conn = psycopg2.connect(
        database='leaguedb',
        user='djmax',
        password='pw',
        host='localhost',
        port=5432
    )
    fetcher_cur = fetcher_conn.cursor()
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
    fetcher_cur.execute("""
    SELECT game_id FROM gameinfo WHERE game_id NOT IN 
    (SELECT game_id FROM matchinfo) AND
    subtype = ANY('{RANKED_TEAM_5x5,
    RANKED_SOLO_5x5,RANKED_TEAM_3x3}'::text[])
    ;--ORDER BY timestamp;"""
    )
    game_id_set = set()
    while True:
        timestamp = datetime.now()
        game_id = fetcher_cur.fetchone()[0]
        if game_id in game_id_set:
            continue
        try:
            time.sleep(24.8)
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
            print 'added game id: %d' % game_id
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
            print 'game id~~~%d' % game_id
            if e.error == "Game data not found":
                continue
            time.sleep(60)
    conn.close()
    fetcher_conn.close()
     

if __name__=='__main__':    
    main(sys.argv[1:])