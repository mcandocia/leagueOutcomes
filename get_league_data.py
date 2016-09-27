import psycopg2
import sys
import os
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
    db1 = Database()
    conn = db1.conn
    cur = db1.cur
    cur = conn.cursor()
    summoner_id = randint(1,1200000)
    cur.execute("""CREATE TABLE IF NOT EXISTS gameinfo(
    summoner_id BIGINT,
    won_game BOOLEAN,
    game_timestamp TIMESTAMP,
    champion_id INTEGER,
    user_level INTEGER,
    game_id BIGINT,
    spell1 INTEGER,
    spell2 INTEGER,
    invalid BOOLEAN,
    gameMode VARCHAR(50),
    map_id INTEGER,
    ip_earned INTEGER,
    subType VARCHAR(50),
    timestamp TIMESTAMP,
    stats JSONB,
    other_players JSONB,
    PRIMARY KEY (summoner_id, game_id)
    );""")
    conn.commit()
    id_set = set()
    ids_to_try = deque()
    while True:
        if summoner_id in id_set:
            if len(ids_to_try) == 0:
                summoner_id = randint(1,51200000)
            else:
                summoner_id = ids_to_try.popleft()
            continue            
        try:
            id_set.add(summoner_id)
            #riotwatcher's timer seems to be borked..being conservative here...
            time.sleep(1.5)
            game_data = watcher.get_recent_games(summoner_id)
        except riotwatcher.LoLException as e:
            print sys.exc_info()
            print e.headers
            print e.error
            if len(ids_to_try) == 0:
                summoner_id = randint(1,51200000)
                print 'choosing new random summoner'
            else:
                summoner_id = ids_to_try.popleft()
            continue
        except:
            print 'other error' 
            time.sleep(240)
            continue
        timestamp = datetime.now()
        games = game_data['games']
        for game in games:
            game_id = game['gameId']
            champion_id = game['championId']
            user_level = game['level']
            map_id = game['mapId']
            subType = game['subType']
            invalid = game['invalid']
            ipEarned = game['ipEarned']
            try:
                fellow_players = game['fellowPlayers']
            except:
                print 'tutorial...'
                continue
            game_timestamp = datetime.fromtimestamp(
                game['createDate']/1e3)
            try:
                cur.execute("""INSERT INTO gameinfo( summoner_id, won_game, game_timestamp, champion_id, user_level, game_id, spell1, spell2, invalid, gameMode, map_id, ip_earned, subType, timestamp, stats, other_players) VALUES 
            ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                        summoner_id, 
                        game['stats']['win'],
                        game_timestamp,
                        champion_id,
                        user_level,
                        game_id,
                        game['spell1'],
                        game['spell2'],
                        invalid,
                        game['gameMode'],
                        map_id,
                        ipEarned,
                        game['subType'],
                        timestamp,
                        json.dumps(game['stats']),
                        json.dumps(fellow_players))
                )
                conn.commit()
            except:
                print 'error...'
                print game
                print sys.exc_info()
                time.sleep(0.05)
                #end transaction_block
                conn.rollback()
            for player in fellow_players:
                player_id = player['summonerId']
                if player_id not in id_set:
                    ids_to_try.append(player_id)
        print 'done with player %s' % summoner_id
        if len(ids_to_try) == 0:
            summoner_id = randint(1,51200000)
        else:
            summoner_id = ids_to_try.popleft()

if __name__=='__main__':    
    main(sys.argv[1:])
