# try:
#     import urequests as requests
# except ImportError:
#     import urequestslocal as requests

import urequestslocal as requests

def live_game_events(gamePk):

    #Generate fields of interest
    field = 'liveData,plays,currentPlay,matchup,batter,pitcher,postOnFirst,postOnSecond,postOnThird,fullName,id,linescore,currentInning,currentInningOrdinal,inningState,inningHalf,isTopInning,teams,home,away,runs,hits,errors,leftOnBase,num,ordinalNum,balls,strikes,outs,offense,battingOrder,gameData,teams,away,home,name,record,leagueRecord'

    url = 'https://statsapi.mlb.com/api/v1.1/game/{}/feed/live?fields={}'.format(gamePk, field)
    # url = url + '&fields=' + field
    response = requests.get(url).json()

    output = {}   #Formatted dictionary for use in drawing

    output['home_team'] = response['gameData']['teams']['home'].get('name')
    output['away_team'] = response['gameData']['teams']['away'].get('name')
    output['home_score'] = response['liveData']['linescore']['teams']['home'].get('runs')
    output['away_score'] = response['liveData']['linescore']['teams']['away'].get('runs')
    output['balls'] = response['liveData']['linescore'].get('balls')
    output['strikes'] = response['liveData']['linescore'].get('strikes')
    output['outs'] = response['liveData']['linescore'].get('outs')
    output['batter_pos'] = response['liveData']['linescore']['offense'].get('battingOrder')
    output['inning'] = response['liveData']['linescore'].get('currentInning')
    output['inning_ordinal'] = response['liveData']['linescore'].get('currentInningOrdinal')
    output['inning_state'] = response['liveData']['linescore'].get('inningState')
    output['inning_half'] = response['liveData']['linescore'].get('inningHalf')
    output['batter'] = response['liveData']['plays']['currentPlay']['matchup']['batter'].get('fullName')
    output['batter_id'] = response['liveData']['plays']['currentPlay']['matchup']['batter'].get('id')
    output['on_first'] = False if response['liveData']['plays']['currentPlay']['matchup'].get('postOnFirst', None) == None else True
    output['on_second'] = False if response['liveData']['plays']['currentPlay']['matchup'].get('postOnSecond', None) == None else True
    output['on_third'] = False if response['liveData']['plays']['currentPlay']['matchup'].get('postOnThird', None) == None else True

    # #get batting average of current hitter and pitcher
    # hitter_id  = response['liveData']['plays']['currentPlay']['matchup']['batter'].get('id')
    # pitcher_id = response['liveData']['plays']['currentPlay']['matchup']['pitcher'].get('id')

    # field = 'liveData,boxscore,teams,away,players,seasonStats,batting,avg,pitching,pitchesThrown'
    # url = 'https://statsapi.mlb.com/api/v1.1/game/{}/feed/live?'.format(gamePk)
    # url = url + 'fields=' + field 

    # response = requests.get(url)
    # response = response.json()   

    # homeaway = 'home' if output['inning_half'] == 'Top' else 'away'
    # output['pitch_count'] = response['liveData']['boxscore']['teams'][homeaway]['players']['ID{}'.format(pitcher_id)]['seasonStats']['pitching'].get('pitchesThrown', 0)

    # homeaway = 'home' if output['inning_half'] == 'Bottom' else 'away'
    # output['hitter_average'] = response['liveData']['boxscore']['teams'][homeaway]['players']['ID{}'.format(hitter_id)]['seasonStats']['batting'].get('avg')

    return output

#returns a dict with player ID as key and batting average as value
def upcoming_game_hitters(gamePk):
    field = 'liveData,boxscore,teams,home,away,players,seasonStats,batting,avg'
    url = 'https://statsapi.mlb.com/api/v1.1/game/{}/feed/live?fields={}'.format(gamePk, field)
    # url = url + 'fields=' + field 

    response = requests.get(url).json()  

    sides = ['home','away']
    players = {}
    for side in sides:
        full_players = response['liveData']['boxscore']['teams'][side]['players']
        for id,info in full_players.items():
            players[id] = info['seasonStats']['batting'].get('avg')
    
    return players

from config import chosen_tz
def upcoming_game_events(gamePk):

    #Generate fields of interest
    field ='gameData,teams,away,home,id,record,leagueRecord,wins,losses,probablePitchers,fullName,venue,name,datetime,time,ampm,originalDate,timeZone,offset'

    url = 'https://statsapi.mlb.com/api/v1.1/game/{}/feed/live?fields={}'.format(gamePk,field)
    # url = url + '&fields=' + field
    response = requests.get(url).json()

    output = {}   #Formatted dictionary for use in drawing

    output['home_team'] = response['gameData']['teams']['home'].get('name')
    output['home_id'] = response['gameData']['teams']['home'].get('id')
    output['away_team'] = response['gameData']['teams']['away'].get('name')
    output['away_id'] = response['gameData']['teams']['away'].get('id')
    output['home_record'] = '{}-{}'.format(response['gameData']['teams']['home']['record']['leagueRecord'].get('wins'),response['gameData']['teams']['home']['record']['leagueRecord'].get('losses'))
    output['away_record'] = '{}-{}'.format(response['gameData']['teams']['away']['record']['leagueRecord'].get('wins'),response['gameData']['teams']['away']['record']['leagueRecord'].get('losses'))
    # home_pitcher = response['gameData']['probablePitchers']['home'].get('fullName')
    # away_pitcher = response['gameData']['probablePitchers']['away'].get('fullName')
    # output['home_pitcher'] = home_pitcher if home_pitcher else 'Unknown'
    # output['away_pitcher'] = away_pitcher if away_pitcher else 'Unknown'
    output['venue'] = response['gameData']['venue'].get('name')

    # Convert stadium time to device local time
    output['local_time_offset'] = response['gameData']['venue']['timeZone'].get('offset')
    offset = (-1 * output['local_time_offset']) + (chosen_tz) #both offsets are in terms of UTC (and therefore negative within the US)

    gametime_h, gametime_m = tuple(response['gameData']['datetime'].get('time').split(':',1)) 
    gametime_h, gametime_m = int(gametime_h), int(gametime_m)
    ampm = 'AM' if gametime_h + offset < 0 else response['gameData']['datetime'].get('ampm')  # Check for noon rollover
    gametime_h = (gametime_h + offset) % 12                                                   # Convert to device time zone
    if gametime_m < 10 and gametime_m > 0:
        gametime_m = '0{}'.format(gametime_m)
    elif gametime_m == 0:
        gametime_m = '00'
    output['game_time_local'] = '{}:{} {}'.format(gametime_h,gametime_m, ampm)

    #get date
    _, gametime_mo, gametime_d = tuple(response['gameData']['datetime'].get('originalDate').split('-'))
    gametime_mo, gametime_d = int(gametime_mo), int(gametime_d)
    output['game_date_local'] = '{}/{}'.format(gametime_mo, gametime_d)
    return output

def postgame_events(gamePk):

    #Generate fields of interest
    field ='liveData,linescore,teams,home,away,runs,gameData,name'

    url = 'https://statsapi.mlb.com/api/v1.1/game/{}/feed/live?fields={}'.format(gamePk, field)
    # url = url + '&fields=' + field
    response = requests.get(url).json()

    output = {}   #Formatted dictionary for use in drawing
    output['home_team'] = response['gameData']['teams']['home'].get('name')
    output['away_team'] = response['gameData']['teams']['away'].get('name')
    output['home_score'] = response['liveData']['linescore']['teams']['home'].get('runs')
    output['away_score'] = response['liveData']['linescore']['teams']['away'].get('runs')

    return output

from config import chosen_team
def schedule(team=chosen_team):
    url = 'http://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&teamId={}'.format(team)

    response = requests.get(url).json()

    output = {}
    if response.get('totalGames') > 0:
        output['gamePk'] = response['dates'][0]['games'][0].get('gamePk')
        output['game_status'] = response['dates'][0]['games'][0]['status'].get('detailedState') # 'Scheduled', 'Warmup', 'In Progress', or 'Game Over' OR 'Postponed'
        output['home_team'] = response['dates'][0]['games'][0]['teams']['home']['team'].get('name')
        output['away_team'] = response['dates'][0]['games'][0]['teams']['away']['team'].get('name')
        if response['dates'][0]['games'][0]['teams']['home']['leagueRecord'].get('wins') + response['dates'][0]['games'][0]['teams']['home']['leagueRecord'].get('losses') <= 40:
            output['home_record'] = '{}-{}'.format(response['dates'][0]['games'][0]['teams']['home']['leagueRecord'].get('wins'), response['dates'][0]['games'][0]['teams']['home']['leagueRecord'].get('losses'))
            output['away_record'] = '{}-{}'.format(response['dates'][0]['games'][0]['teams']['away']['leagueRecord'].get('wins'), response['dates'][0]['games'][0]['teams']['away']['leagueRecord'].get('losses'))
        else:
            output['home_record'] = '{}'.format(response['dates'][0]['games'][0]['teams']['home']['leagueRecord'].get('pct'))
            output['away_record'] = '{}'.format(response['dates'][0]['games'][0]['teams']['away']['leagueRecord'].get('pct'))
        if output['game_status'] == 'Postponed':
            date_field = 'rescheduleDate'
        else:
            date_field = 'gameDate'
        datetime = response['dates'][0]['games'][0].get(date_field)
        year = int(datetime[0:4])
        month = int(datetime[5:7])
        day = int(datetime[8:10])
        hour = int(datetime[11:13])
        minute = int(datetime[14:16])
        second = int(datetime[17:19])

        output['game_datetime'] = (year, month, day, hour, minute, second, 0, 0)
    else:
        output['gamePk'] = None
        output['game_status'] = None
        output['game_datetime'] = None
    
    return output

def postponed_game_events(gamePk):
    #Generate fields of interest
    field ='gameData,teams,away,home,record,leagueRecord,wins,losses,probablePitchers,fullName,venue,name,datetime,time,ampm,originalDate,timeZone,offset'

    url = 'https://statsapi.mlb.com/api/v1.1/game/{}/feed/live?fields={}'.format(gamePk,field)
    # url = url + '&fields=' + field
    response = requests.get(url).json()

    output = {}   #Formatted dictionary for use in drawing

    # Convert stadium time to device local time
    output['local_time_offset'] = response['gameData']['venue']['timeZone'].get('offset')
    offset = (-1 * output['local_time_offset']) + (chosen_tz) #both offsets are in terms of UTC (and therefore negative within the US)

    gametime_h, gametime_m = tuple(response['gameData']['datetime'].get('time').split(':',1)) 
    gametime_h, gametime_m = int(gametime_h), int(gametime_m)
    ampm = 'AM' if gametime_h + offset < 0 else response['gameData']['datetime'].get('ampm')  # Check for noon rollover
    gametime_h = (gametime_h + offset) % 12                                                   # Convert to device time zone
    if gametime_m < 10 and gametime_m > 0:
        gametime_m = '0{}'.format(gametime_m)
    elif gametime_m == 0:
        gametime_m = '00'
    output['game_time_local'] = '{}:{} {}'.format(gametime_h,gametime_m, ampm)

    #get date
    _, gametime_mo, gametime_d = tuple(response['gameData']['datetime'].get('originalDate').split('-'))
    gametime_mo, gametime_d = int(gametime_mo), int(gametime_d)
    output['game_date_local'] = '{}/{}'.format(gametime_mo, gametime_d)
    return output

def next_game(team=chosen_team):
    fields = 'hydrate=nextSchedule&fields=teams,id,teamName,nextGameSchedule,dates,date,games,gamePk,season,gameDate,teams,away,home,team,name,teamName'
    url = 'https://statsapi.mlb.com/api/v1/teams/{}?{}'.format(team,fields)

    response = requests.get(url).json()

    gamePk = response["teams"][0]["nextGameSchedule"]["dates"][0]["games"][0].get('gamePk')

    return gamePk