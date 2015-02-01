import pymongo
import time

def main():

    #client = MongoClient('dbh55.mongolab.com', 27557)
    #client = MongoClient()
    #db = client['sc2-replay-data']
    #replays = client.replays
    #db.authenticate('forrest.coward', 'fmc3Microsoft')
    
    mongodb_uri = 'mongodb://localhost:27017'
    db_name = 'test'
    
    try:
        connection = pymongo.Connection(mongodb_uri)
        database = connection[db_name]
    except:
        print('Error: Unable to connect to database.')
        connection = None       
    print
    
    collection = database.replays

    '''
    #c1 = make_constraint('Marine', 10, '$gte', 10000000)
    c2 = make_constraint('Reaper', 0, '$gte', 10000000) 
    constraints = [c2]
   
    start = time.clock()
    result = do_constraint_query(database, 'T', 'Z', constraints)
    print len(result['win'])
    print result['win']
    print
    print len(result['loss'])
    print result['loss']
    print
    
    finish = time.clock() - start
    print finish
    '''
    q = create_league_group_query()   
    response = collection.aggregate(q)['result']
    for r in response:
        print r['_id'], r['count']
        print 'apm', r['apm']
        print 'sq', r['sq']
        print 'ami', r['ami']
        print 'avi', r['avi']
        print 'aum', r['aum']
        print 'auv', r['auv']
        print 'hotkey', r['hotkeys']
        print 'minimap', r['minimap']
        print 'supply', r['supply']
        print 'unique', r['unique']
        print 'workers', r['workers']
        print 'mannered', r['mannered']
        print
    print response
    

def make_constraint(unit, target, comparison, finish):
    return {
        'unit' : unit,
        'target' : target,
        'comparison' : comparison,
        'finish_by' : finish
    }
    
''' Alternative query method to aggregate query that passes javascript in the $where clause. '''
def do_find_query(database, race, opponent_race, func):

    matches = database.replays.find({
        'player.race' : race,
        'opponent.race' : opponent_race,
        '$where' : func 
    })
    
    wins = 0
    losses = 0
    for match in matches:
        if(match['won'] == 1):
            wins += 1
        else:
            losses += 1
    
    print 'wins:', wins
    print 'losses:', losses
    
''' Makes the row filtering function for the find query. Can only satisfy one constraint. '''
def make_comparison_function(unit, target, finish, comparison): 
    replace = {
        'unit' : unit,
        'target' : target,
        'finish_by' : finish,
        'comparison' : comparison,
        '@' : '{',
        '#' : '}'
    }
    
    return '''
        function() {@}
            if(this.build.hasOwnProperty("{unit}")) {@}
                var i;
                var count = 0
                for(i = 0; i < this.build["{unit}"].length; i++) {@}
                    var ts = this.build["{unit}"][i];
                    if(ts.finish < {finish_by} || {finish_by} == -1)  {@}
                        count += 1;
                    {#}
                {#}
                return count {comparison} {target};
            {#}
            return false
        {#}
        '''.format(**replace)
    
''' Runs a query on the database. '''
'''
    Each query specifies a race and opponent race. All games that do match are not considered.
    Additionally, a list of constraints on the build are supplied.
    Each constraint is of the form:
    {
        'unit' : unit
        'target' : amount of unit
        'comparison' : { $lt, $lte, $eq, $gt, $gte }
        'finish_by' : the time the constraint must be met by
    }
    
    For example, if unit = SCV, target = 40, comparison = $gt and finish_by = 6000, then the constraint
    is that the player must have created more than 40 SCVs by the 6000th frame.
    
    For each constraint a query is ran and the results are intersected. 
'''
def do_constraint_query(database, race, opponent_race, constraints):

    op = opponent_race
    if(opponent_race == None):
        op = 'A'
    print race + 'v' + op
    for constraint in constraints:
        print constraint
    print
    first = True

    for constraint in constraints:   
        query = create_constraint_aggregate_query(race, opponent_race, constraint)
        response = database.replays.aggregate(query)
        
        if response['ok'] != 1.0:
            raise Exception("Query did not complete successfully")
            
        results = response['result']
        
        # TODO: if the query has 0 wins or 0 losses there will be no associated entry. 
        if first:
            first = False
            wins = set(results[0]['ids'])
            losses = set(results[1]['ids'])
        else:
            wins = wins & set(results[0]['ids'])
            losses = losses & set(results[1]['ids'])
        
        if len(wins) == 0 and len(losses) == 0:
            break
        
    return { 'win' : wins, 'loss' : losses }
    
def create_league_group_query():
    query = []
    group = { '$group' : 
    {
    '_id' : '$player.league',
    'apm' : { '$avg' : '$stats.apm' },
    'sq' : { '$avg' : '$resources.sq' },
    'ami' : { '$avg' : '$resources.ami' },
    'avi' : { '$avg' : '$resources.avi' },
    'aum' : { '$avg' : '$resources.aum' },
    'auv' : { '$avg' : '$resources.auv' },
    'hotkeys' : { '$avg' : '$stats.hotkeys' },
    'minimap' : { '$avg' : '$stats.minimap' },
    'supply' : { '$avg' : '$stats.supply_capped'},
    'unique' : { '$avg' : '$stats.unique_units'},
    'workers' : { '$avg' : '$resources.workers_rate'},
    'mannered' : { '$avg' : '$stats.mannered'},
    'count' : { '$sum' : 1}
    }}     
    
        
    query.append(group)  
    return query
    
    
''' Creates a query of the form: '''
'''
    [
        { '$match' : 
            { 
                'build.unit' : { '$exists' : True },
                'player.race' : 'race',
                'opponent.race' : 'opponent_race'
            } 
        },
        { '$project' : 
            { 
            'build.unit' : 1,
            'won' : 1
            } 
        },
        { '$unwind' :  '$build.unit' },
        { '$match' : 
            { 
                'build.unit.finish' : { '$lt' : finish_by } 
            } 
        },
        { '$group' : 
            {
            '_id' : '$_id',
            'won' : { '$max' : '$won' },
            'num' : { '$sum' : 1 }
            }
        },
        { '$match' :
           {
                'num' : { 'comparison ($gte, $lt etc.)' : target }
           }    
        },
        { '$group' :
            {
                '_id' : '$won',
                'ids' : { '$push' : '$_id' },
                'count' : { '$sum' : 1 }    
            }
        }      
    ]
'''    
def create_constraint_aggregate_query(race, opponent_race, constraint):
    query = []
    
    # Filter race and opponent race, if specified. 
    match_races = { }
    match_races['player.race'] = race
    if(opponent_race != None):
        match_races['opponent.race'] = opponent_race    
    # match_races['build.' + constraint['unit']] = { '$exists' : True }
    query.append({ '$match' : match_races})
    
    # Only project the array of the constraint unit. We do not care about any other data.
    project_units = { 
        'won' : 1,
        'build.' + constraint['unit'] : 1
    }
    query.append({ '$project' : project_units })   

    # Unwind the constraint unit build time array.
    unwind = { '$unwind' : '$build.' + constraint['unit']}
    query.append(unwind)    
    
    # Filter unit build time array by finish time.
    match_finish = { 
        'build.' + constraint['unit'] + '.finish' : {'$lt' : constraint['finish_by'] }
    }
    query.append({ '$match' : match_finish })
       
    # Group the results.
    group = { '$group' : 
        {
        '_id' : '$_id',
        'won' : { '$max' : '$won' },
        'num' : { '$sum' : 1 }
        }}    
    query.append(group)
  
    # Filter if we pass target comparison.
    match_number = { 
        'num' : { constraint['comparison'] : constraint['target'] }
    }
    query.append({ '$match' : match_number })
    
    # Finally group by wins/loss.
    group =  { '$group' :
        {
            'ids' : { '$push' : '$_id' },
            '_id' : '$won',
            'count' : { '$sum' : 1 }    
        }}   
    query.append(group)
    
    return query
       
if __name__ == '__main__':
    main()