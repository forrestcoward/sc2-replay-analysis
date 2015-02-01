import urllib2
from bs4 import BeautifulSoup

def fetch(url, params=None, soup=True):
    try:
        f = urllib2.urlopen(url, params)
    except IOError, exc:
        print "Unable to connect to", url
        return None
    response = f.read()
    f.close()
    if soup:
        return BeautifulSoup(response)
    else:
        return response
    
def parse_replay_page(doc, directory):
    links = doc.find_all('a', class_='btn success')
    for link in links:
        download = link['href']
        if download != '#':
            download = 'http://drop.sc' + download
            number = download.split('/')[3]
            print number
            print download
            replay = fetch(download, soup=False)
            file = open('../' + directory + '/' + number + '.SC2Replay', 'wb')
            file.write(replay)
            file.close()
            
def get_page(page):
    return "http://drop.sc/search?commit=Apply+filters&game_format=1v1&gateway=&league=&map=&matchup=&order=date_played&page=" + str(page) + "&player=&time=&utf8=%E2%9C%93&version=2.0.8.25604"      
            
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print 'Usage: [low] [high] [directory]'
        sys.exit()
        
    try:
        low = int(sys.argv[1])
    except ValueError:
        print 'Excepting integer argument got "' + sys.argv[1] + '"'
        sys.exit()
        
    try:
        high = int(sys.argv[2])
    except ValueError:
        print 'Excepting integer argument got "' + sys.argv[2] + '"'
        sys.exit()
        
    directory = sys.argv[3]
    
    
    for i in range(low, high+1):
        print i
        url = get_page(i)
        parse_replay_page(fetch(url), directory)
    