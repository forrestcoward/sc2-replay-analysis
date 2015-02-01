import sys
import math
import re
import sc2reader
import os
import pymongo
import shutil
import bnet_league_scrapper
from stats import sc2_player_stats
from stats import Invalid1v1Stats
from sc2reader.plugins.replay import APMTracker
sc2reader.register_plugin('Replay',APMTracker())

class ReplayValidateException(Exception):
    pass
             
def validate_unit(name):
    if name is None: return False
    return not re.match(r'(.*)Beacon(.*)', name)
    
def validate_replay(replay):
    if not hasattr(replay, 'tracker_events'):
        raise ReplayValidateException('skipping replay: no tracker events')
        
    if replay.winner is None:
        raise ReplayValidateException('skipping replay: no winner')
    
    if replay.length.mins <= 9:
        raise ReplayValidateException('skipping replay: duration too short')
     
    if len(replay.players) <= 1:
        raise ReplayValidateException('skipping replay: less than 1 player')
    
def process_replay(replay, replays_collection, leagues_collection):
    
    print replay.filename, replay.release_string
    validate_replay(replay)
        
    winner_pid = replay.winner.players[0].pid
    stats = { }  
    for player in replay.players:
        pid = player.pid
        
        cursor = leagues_collection.find({ "_id" : player.url })
        if cursor.count() == 0:
            print 'parsing league from bnet:', player.url
            leagues = bnet_league_scrapper.get_leagues(player.url)
            
            if leagues == None:
                print 'skipping replay: could not get league of', player.url
                error = { '_id' : player.url, 'error' : 1 }    
                leagues_collection.insert(error)       
                return
            else:
                leagues['_id'] = player.url
                leagues_collection.insert(leagues)
        else:
            leagues = cursor[0]
            if 'error' in leagues:
                raise ReplayValidateException('skipping replay: no league for', player.url)
            
        league = max(leagues['current'], leagues['best'])
        if league == -1 or league == 0:
            raise ReplayValidateException('skipping replay: no league for', player.url)
            
        won = 1 if pid == winner_pid else 0
        stats[pid] = sc2_player_stats(replay, player, league, won)
    
    stats[1].set_opponent(stats[2])
    stats[2].set_opponent(stats[1])
    
    # Extract relevant tracket events. 
    for event in replay.tracker_events:
        if event.name == 'UnitDoneEvent':
            unit = event.unit
            if not unit is None and not unit.owner is None:
                if validate_unit(unit.name):
                    if unit.is_building:
                        stats[unit.owner.pid].structure_done(unit, event.frame)
                    elif unit.is_army:
                        stats[unit.owner.pid].unit_done(unit, event.frame)
                    elif unit.is_worker:
                        # Can this happen? A worker is army. 
                        pass

        elif event.name == 'UnitBornEvent':
            unit = event.unit
            if not unit is None and not event.unit_controller is None:
                if validate_unit(event.unit.name):
                    if unit.is_building:
                        stats[event.control_pid].structure_done(unit, event.frame)
                    elif unit.is_army or unit.is_worker:
                        stats[event.control_pid].unit_done(unit, event.frame)
            
        elif event.name == 'PlayerStatsEvent':
            stats[event.pid].stats_event(event)
            
        elif event.name == 'UnitDiedEvent':
            unit = event.unit
            if not unit is None and not unit.owner is None:
                if unit.name == 'SCV' \
                or unit.name == 'Probe' \
                or unit.name == 'Drone':
                    stats[unit.owner.pid].worker_died(unit)
            
        elif event.name == 'UnitInitEvent':
            pass
            

    # Extract relevant game events. 
    for player in replay.players:
        s = stats[player.pid]
        for event in player.events:
            if event.name == 'SetToHotkeyEvent' or event.name == 'GetFromHotkeyEvent':
                s.hotkey_event(event)
            if event.name == 'LocationAbilityEvent':
                s.location_event(event);
          
    for key, value in stats.iteritems():
        value.compute()
        value.validate()
        
    cursor = replays_collection.find({ "_id" : stats[1].hash() })
    if cursor.count() == 0:
        replays_collection.insert(stats[1].mongoize())
        
    cursor = replays_collection.find({ "_id" : stats[2].hash() })
    if cursor.count() == 0:
        replays_collection.insert(stats[2].mongoize())

def main():
    path = sys.argv[1]
    replays = sc2reader.load_replays(path, load_level=4)
    
    mongodb_uri = 'mongodb://localhost:27017'
    db_name = 'test'
    
    try:
        connection = pymongo.Connection(mongodb_uri)
        database = connection[db_name]
    except:
        print('Error: unable to connect to database.')
        sys.exit()
        
    replays_collection = database.replays
    leagues_collection = database.leagues
        
    for replay in replays:
        
        id = hash((replay.end_time, replay.players[0].url))
        cursor = replays_collection.find({ "_id" : id })
        
        if cursor.count() == 0:     
            try:
                process_replay(replay, replays_collection, leagues_collection)
            except ReplayValidateException:
                #error = { '_id' : id, 'error' : 1 }
                print 'skipping: invalid replay'
                #database.replays.insert(error)
            except Invalid1v1Stats:
                #error = { '_id' : id, 'error' : 1 }
                print 'skipping: invalid 1v1 statistics'
                #database.replays.insert(error)
        else:    
            print replay.filename    
            print "already processed"
        print
        
        # Move replay to processed folder. 
        split = replay.filename.split('\\');
        dir = split[0] + '\\' + split[1] + ".processed"
        dest = dir + "\\" + split[2]
        
        if not os.path.exists(dir):
            os.makedirs(dir)
        shutil.move(replay.filename, dest)
        
        
if __name__ == '__main__':
    main()


