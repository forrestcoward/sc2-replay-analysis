import urllib2
from bs4 import BeautifulSoup

def fetch(url, params=None):
    try:
        f = urllib2.urlopen(url, params)
    except IOError, exc:
        print "Unable to connect to", url
        return None
    response = f.read()
    f.close()
    return BeautifulSoup(response)
    
def parse_current_league(doc):
    # Use find instead of find_all because by the strucutre of the data the result we want is always the first one.
    try:
        league = doc.find(id='season-snapshot').find('div', class_='module-body').find('div', class_='badge-item').find('div', class_='badge').find('span')['class'][1]
    except AttributeError:
        return None   
    return league
    
def parse_best_league(doc):
    try:
        league = doc.find('div', attrs={ 'data-tooltip' : '#best-finish-SOLO' }).find('div', class_='badge').find('span')['class'][1]
    except AttributeError:
        return None
    return league
   
def league_to_num(league):
    if league == 'badge-grandmaster': return 7
    if league == 'badge-master' : return 6
    if league == 'badge-diamond' : return 5
    if league == 'badge-platinum' : return 4
    if league == 'badge-gold' : return 3
    if league == 'badge-silver' : return 2
    if league == 'badge-bronze' : return 1
    if league == 'badge-none' : return 0
    return -1
    
def get_leagues(url):
    doc = fetch(url)
    current_league = parse_current_league(doc)
    best_league = parse_best_league(doc)
    
    if(current_league == None or best_league == None):
        return None
    
    return {
        'current' : league_to_num(current_league),
        'best' : league_to_num(best_league)
    }
    
if __name__ == "__main__":
    import sys
    url = sys.argv[1]
    doc = fetch(url)
    current_league = parse_current_league(doc)
    best_league = parse_best_league(doc)
    
    if(current_league == None or best_league == None):
        print "Invalid url:", url
        sys.exit()
        
    print url
    print current_league
    print league_to_num(current_league)
    print best_league
    print league_to_num(best_league)
    