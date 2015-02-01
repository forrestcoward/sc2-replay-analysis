import math
from collections import defaultdict

class Invalid1v1Stats(Exception):
    pass
             
class sc2_player_stats(object):
    
    def __init__(self, replay, player, league, won):
        self.replay = replay
        self.player = player
        self.league = league
        self.pid = player.pid
        self.race = player.pick_race[0]
        self.apm = player.avg_apm
        self.won = won
        self.mineral_income = []
        self.vespene_income = []
        self.minerals = []
        self.vespene = []
        self.workers = 0
        self.current_workers = 0
        self.idle_workers_total = 0
        self.current_workers_total = 0
        self.hotkeys = set()
        self.minimap_clicks = 0
        self.supply_block_time = 0
        self.units = defaultdict(list) 
        self.mannered = 0
        self.total_seconds = 3600 * self.replay.length.hours + 60 * self.replay.length.mins + self.replay.length.secs
        self.unique_units = set()
        self.base_location = None
        self.structs_built = 0
        self.proxy = 0
        self.proxy_struct = None
        self.proxy_distance = 0

        for message in replay.messages:
            if message.pid == self.pid:
                if message.text == 'gg' \
                or message.text == 'gg wp':
                    self.mannered = 1
                
    def unit_done(self, unit, frame):
        name = unit.name

        if(self.race == 'Z'):
            if name == 'Egg'\
            or name == 'Locust'\
            or name == 'Larva'\
            or 'Broodling' in name\
            or 'Changeling' in name:
                return
                
            if "Burrowed" in name:
                name = name.replace("Burrowed", "")
            
        elif(self.race == 'T'):
            if name == 'MULE' \
            or name == 'ReaperPlaceHolder':
                return
                
            if name == 'WidowMineBurrowed':
                name = 'WidowMine'
            elif name == 'SiegeTankSieged':
                name = 'SiegeTank'
            elif name == 'VikingFighter' or name == 'VikingAssault':
                name = 'Viking'
                
        elif(self.race =='P'):
            if name == 'WarpPrismPhasing'\
            or name == 'Interceptor':
                return
                
        if(unit.is_worker):
            self.current_workers += 1
            
        self.unique_units.add(name)
                
        self.units[name].append(
        {
            'start' : frames_to_second(unit.started_at),
            'finish' : frames_to_second(unit.finished_at)
        })
        
    def worker_died(self, worker):
        self.current_workers -= 1
        
    def structure_done(self, struct, frame):    
        name = struct.name
        if name == 'SupplyDepotLowered':
            name = 'SupplyDepot'
        if "Flying" in name:
            name = name.replace("Flying", "")
            
        if self.base_location is None:
            if is_base(name):
                self.base_location = struct.location
                
        if not self.base_location is None and self.structs_built <= 10 and self.proxy != 1:
            if not is_not_proxy(name):
                location = struct.location
                dist = distance(self.base_location, location) 
                if dist >= 75 and frame <= 8300:
                    self.proxy = 1
                    self.proxy_struct = name
                    self.proxy_distance = dist
                    self.proxy_location = {
                        'x' : struct.location[0],
                        'y' : struct.location[1]
                    }
            
        self.structs_built += 1
        self.units[name].append(
        {
            'start' : frames_to_second(struct.started_at),
            'finish' : frames_to_second(struct.finished_at)
        })
        
    def location_event(self, event):
        
        if(event.name == 'LocationAbilityEvent'):
            flags = event.flags
            queued = (flags & 2) != 0
            right_click = (flags & 8) != 0
            wireframe_click = (flags & 0x20) != 0
            toggle_ability = (flags & 0x40) != 0
            enable_auto_cast = (flags & 0x80) != 0
            ability_used = (flags & 0x100) != 0
            wireframe_unload = (flags & 0x200) != 0
            wireframe_cancel = (flags & 0x400) != 0
            minimap_click = (flags & 0x10000) != 0
            ability_failed  = (flags & 0x20000) != 0
            
            if(minimap_click):
                self.minimap_clicks += 1
                
    def hotkey_event(self, event):
        if event.name == 'SetToHotkeyEvent':
            self.hotkeys.add(event.control_group)
        
    # Stats events appears to fire every 160 frames (10 seconds)
    def stats_event(self, event):
        self.mineral_income.append(event.minerals_collection_rate)
        self.vespene_income.append(event.vespene_collection_rate)
        self.minerals.append(event.minerals_current)
        self.vespene.append(event.vespene_current)  
        self.current_workers_total += self.current_workers
        self.idle_workers_total += self.current_workers - event.workers_active_count
        
        supply_cap = event.food_made / 4096
        supply = event.food_used / 4096
        
        if supply_cap == supply and supply != 200:
            self.supply_block_time += 10 
            
                
    def set_opponent(self, opponent):
        self.opponent = opponent
               
    def compute(self):
        
        if self.race == 'T':
            self.workers = len(self.units['SCV'])
        elif self.race == 'P':
            self.workers = len(self.units['Probe'])
        elif self.race == 'Z':
            self.workers = len(self.units['Drone'])
            
        self.average_mineral_income = average(self.mineral_income)
        self.average_vespene_income = average(self.vespene_income)
        self.average_unspent_minerals = average(self.minerals)
        self.average_unspent_vespene = average(self.vespene)
        self.resource_collection_rate = self.average_mineral_income + self.average_vespene_income
        self.average_unspent_resources = self.average_unspent_minerals + self.average_unspent_vespene
        self.spending_quotient = spending_quotient(self.resource_collection_rate, self.average_unspent_resources)
        # TODO: Figure out an accurate way to calculate idle workers. 
        # self.idle_worker_percentage = 100 * (float(self.idle_workers_total) / float(self.current_workers_total))
        self.workers_per_minute = 60*(float(self.workers) / float(self.total_seconds))
        self.supply_cap_percent = 100 * float(self.supply_block_time) / float(self.total_seconds)
        
    def hash(self):     
        return hash((self.replay.end_time, self.player.url))
        
    def validate(self):
        
        if self.base_location is None:
            raise Invalid1v1Stats
            
        if self.average_unspent_minerals > 13000:
            raise Invalid1v1Stats
            
        if self.workers_per_minute < 0:
            raise Invalid1v1Stats
        
        
    def mongoize(self):

        player = {   
            'name': self.player.name,
            'race' : self.race,
            'league' : self.league,
            'url' : self.player.url
        }
        
        resources = {
            'workers_built' : self.workers-6,
            'workers_rate': self.workers_per_minute,
            'ami' : self.average_mineral_income,
            'avi' : self.average_vespene_income,
            'aum' : self.average_unspent_minerals,
            'auv' : self.average_unspent_vespene,
            'sq' : self.spending_quotient
        }
        
        
        stats = {
            'apm' : self.apm,
            'supply_capped': self.supply_cap_percent,
            'unique_units': len(self.unique_units),
            'hotkeys' : len(self.hotkeys),
            'minimap' : self.minimap_clicks,
            'mannered' : self.mannered,
            'spawn_location' : {
                'x' : self.base_location[0],
                'y' : self.base_location[1]
            }
        }         
        
        if self.proxy == 1:
            proxy = {
                'struct' : self.proxy_struct,
                'location' : self.proxy_location,
                'distance' : self.proxy_distance
            }
            
            stats['proxy'] = proxy       
                                
        opponent = {
            'name' : self.opponent.player.name,
            'race' : self.opponent.race,
            'league' : self.opponent.league,
            'hash' : self.opponent.hash(),
        }
        
        length = {
            'seconds' : self.replay.length.secs,
            'minutes' : self.replay.length.mins,
            'hours' : self.replay.length.hours
        }
        
        entry = { 
            '_id' : self.hash(),
            'file' : self.replay.filename,
            'player' : player,
            'length' : length,
            'resources' : resources,
            'stats' : stats,
            'opponent' : opponent,
            'won' : self.won,
            'build' : self.units    
        }
        
        return entry
        
def is_base(name):
    if name == 'CommandCenter' \
    or name == 'OrbitalCommand' \
    or name == 'Nexus' \
    or name == 'Hatchery' \
    or name == 'Lair' \
    or name == 'Hive':
        return True
    return False
        
def is_not_proxy(name):
    if name == 'SupplyDepot' \
    or name == 'Pylon' \
    or name == 'Extractor' \
    or name == 'EngineeringBay' \
    or name == 'CreepTumorBurrowed' \
    or is_base(name):
        return True
    return False
        
def distance(a, b):
    return math.sqrt(math.pow(b[0]-a[0],2) + math.pow(b[1]-a[1],2))
        
def frames_to_second(frames):
    return frames / 16
    
def frames_to_minute(frames):
    seconds = frames / 16
    minutes = seconds / 60
    partial_minute = seconds % 60

def average(o):
    return sum(o) / float(len(o))
    
def spending_quotient(c, u):
    return 35*(0.00137*c - math.log(u)) + 240
    