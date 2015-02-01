import pymongo
import time

# table header:
# league, apm, hotkeys, minimap, supply, mannered, unique, ami, avi, aum, auv, sq, workers

def main():

    mongodb_uri = 'mongodb://localhost:27017'
    db_name = 'test'
    
    try:
        connection = pymongo.Connection(mongodb_uri)
        database = connection[db_name]
    except:
        print('Error: Unable to connect to database.')
        connection = None
        
    cursor = database.replays.find()
    
    file = open('data.tab', 'w')
    file.write("league\tapm\thotkeys\tminimap\tsupply\tmannered\tunique\tami\tavi\taum\tauv\tsq\tworkers\n")
    file.write("d\tc\tlow medium high\tc\tc\tc\tc\tc\tc\tc\tc\tc\tc\n")
    file.write("class\n")
    
    counts = { '1':0, '2':0, '3':0, '4':0, '5':0, '6':0, '7':0 }
    
    for d in cursor:
        data = []
        p = d['player']
        s = d['stats']
        r = d['resources']
        l = d['length']
        
        league = p['league']
        league_str = str(league)
        counts[league_str] = counts[league_str] + 1
        minutes = l['minutes']
        if counts[league_str] >= 0:
        
            data.append(league)
        
            '''
            if league == 1 or league == 2:
                data.append("Bronze.Silver")
            if league == 3 or league == 4 or league == 5:
                data.append("Gold.Platinum.Diamond")
            if league == 6 or league == 7:
                data.append("Master.GrandMaster")
            '''
            
            data.append(s['apm'])
            
            hotkeys = s['hotkeys']
            if hotkeys <= 3 :
                data.append("low")
            elif hotkeys <= 7:
                data.append("medium")
            else:
                data.append("high")
            
            data.append(s['minimap'])
            data.append(s['supply_capped'])
            data.append(s['mannered'])
            data.append(s['unique_units'])
            data.append(r['ami'])
            data.append(r['avi'])
            data.append(r['aum'])
            data.append(r['auv'])
            data.append(r['sq'])
            data.append(r['workers_rate'])
            
            count = 0
            for d in data:
                if count == len(data) - 1:
                    file.write(str(d))
                else:
                    file.write(str(d) + '\t')
                count += 1
            file.write('\n')
        
if __name__ == '__main__':
    main()
