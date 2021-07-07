from machine import Pin, I2C
import official1306 as SSD1306 
from fdrawer import FontDrawer
from gfx import GFX
from config import screen
# from ustats import live_game_events

#Initialize required display stuff
def init_display(addr=0x3C, scl=22, sda=21):
    i2c = I2C(0, scl=Pin(scl), sda=Pin(sda), freq=400000)                     #also supports an ID parameter which might be useful for multiple displays
    s = SSD1306.SSD1306_I2C(screen['oled_width'], screen['oled_height'], i2c, addr=addr) #initialize screen
    fd = FontDrawer( frame_buffer=s, font_name = 'dejav_m15' )                #initialize font library
    ar = FontDrawer( frame_buffer=s, font_name = 'arrows_15')
    g = GFX(screen['oled_width'],screen['oled_height'],s.pixel)               #initialize GFX library
    return s,fd,ar,g

def live_scoreboard(stats, hitter_stats, s, fd, ar, g):
    #Top line - batter ordinal, name, batting average
    if (stats['inning_state'] == 'Top') or (stats['inning_state'] == 'Bottom'):
        fd.print_str('{}.'.format(stats['batter_pos']), 2, 1)
        scalable_text(sep_last_name(stats['batter']), 16, 1, s)
        try:
            hitter_average = hitter_stats['ID{}'.format(stats['batter_id'])]
            fd.print_str('{}'.format(hitter_average), 95, 1)
        except KeyError:
            pass

    #Team name and score display - home on top
    # fd.print_str(sep_last_name(stats['home_team'],last_word_length=3), 2, 17)
    scalable_text(sep_last_name(stats['home_team'],last_word_length=3), 2, 17, s, max_width = 66)
    fd.print_str(str(stats['home_score']), 69, 17)
    # fd.print_str(sep_last_name(stats['away_team'],last_word_length=3), 2, 33)
    scalable_text(sep_last_name(stats['away_team'],last_word_length=3), 2, 33, s, max_width = 66)
    fd.print_str(str(str(stats['away_score'])), 69, 33)

    #bottom line - inning state, outs, pitch count
    if (stats['inning_state'] == 'Top') or (stats['inning_state'] == 'Bottom'):
        print_arrow(stats['inning_state'],7,45,ar)
        fd.print_str('{}'.format(stats['inning']), 19, 49)
        fd.print_str('{} out{}'.format(stats['outs'], '' if stats['outs'] == 1 else 's'), 40, 49)
        if (stats['balls'] < 4) and (stats['strikes'] < 3): #check valid count
            fd.print_str('{}-{}'.format(stats['balls'], stats['strikes']), 98, 49)
        elif stats['balls'] == 4: #display walk
            fd.print_str('BB', 98, 49)
        elif stats['strikes'] == 3: #display strikeout
            fd.print_str('K', 103, 49)
    elif stats['inning_state'] == 'Middle':
        fd.print_str('{} {}'.format(stats['inning_state'], stats['inning']), 28, 49)
    else:
        if stats['inning'] >= 9 and stats['home_score'] != stats['away_score']: #check if game is over
            fd.print_str('Final', 40, 49)
        else:
            fd.print_str('{} {}'.format(stats['inning_state'], stats['inning']), 42, 49)

    # Bases line drawing
    if (stats['inning_state'] == 'Top') or (stats['inning_state'] == 'Bottom'):
        x, y = 105, 20
        s.line(x, y, x-16, y+16, 1)
        s.line(x-16, y+16, x-8, y+24, 1)
        s.line(x-8, y+24, x, y+16, 1)
        s.line(x, y+16, x-8, y+8, 1)

        s.line(x, y, x+16, y+16, 1)
        s.line(x+16, y+16, x+8, y+24, 1)
        s.line(x+8, y+24, x, y+16, 1)
        s.line(x, y+16, x+8, y+8, 1)

        #first base
        if stats['on_first']:
            g.fill_triangle(x+15,y+16,x+8,y+8,x+8,y+24,1)
            g.fill_triangle(x+2,y+16,x+8,y+8,x+8,y+24,1)

        #second base
        if stats['on_second']:
            g.fill_triangle(x-6,y+8,x,y+16,x,y,1)
            g.fill_triangle(x+7,y+8,x,y+16,x,y,1)

        #third base
        if stats['on_third']:
            g.fill_triangle(x-14,y+16,x-8,y+8,x-8,y+24,1)
            g.fill_triangle(x-1,y+16,x-8,y+8,x-8,y+24,1)

def pregame_scoreboard(stats, daily_schedule, s,fd,ar,g, immediate_pregame=False):
    if immediate_pregame:
        pass
        # fd.print_str('Game starts soon..', 2, 1)

    home = '{} ({}) vs'.format(sep_last_name(daily_schedule['home_team'], last_word_length=3), daily_schedule['home_record'])
    fd.print_str(home, 2, 17)
    away = '{} ({})'.format(sep_last_name(daily_schedule['away_team'], last_word_length=3), daily_schedule['away_record'])
    fd.print_str(away, 2, 33)

    bottom_line = '{}'.format(stats['game_time_local'])
    fd.print_str(bottom_line,38,49)

def postgame_scoreboard(stats, s, fd, ar, g):
    # fd.print_str(sep_last_name(stats['home_team'],last_word_length=3), 2, 17)
    scalable_text(sep_last_name(stats['home_team'],last_word_length=3), 2, 17, s, max_width = 66)
    fd.print_str(str(stats['home_score']), 69, 17)
    # fd.print_str(sep_last_name(stats['away_team'],last_word_length=3), 2, 33)
    scalable_text(sep_last_name(stats['away_team'],last_word_length=3), 2, 33, s, max_width = 66)
    fd.print_str(str(str(stats['away_score'])), 69, 33)
    
    fd.print_str('Final', 40, 49)    

def postponement_scoreboard(stats, daily_schedule, s, fd, ar, g):
    fd.print_str('Game postponed', 2, 1)

    home = '{} ({}) vs'.format(sep_last_name(daily_schedule['home_team'], last_word_length=3), daily_schedule['home_record'])
    fd.print_str(home, 2, 17)
    away = '{} ({})'.format(sep_last_name(daily_schedule['away_team'], last_word_length=3), daily_schedule['away_record'])
    fd.print_str(away, 2, 33)

    bottom_line = '{} {}'.format(stats['game_date_local'], stats['game_time_local'])
    fd.print_str(bottom_line,14,49)

from config import chosen_team, team_abbreviations
def no_game_scoreboard(stats, s, fd, ar, g):
    opposing_id = int(stats['away_id'] if stats['home_id'] == chosen_team else stats['home_id'])
    opposing_team = team_abbreviations[opposing_id]

    fd.print_str('No game today :(', 2, 17)
    fd.print_str('Next game: {}'.format(stats['game_date_local']), 2, 33)
    fd.print_str('vs {}, {}'.format(opposing_team, stats['game_time_local']), 2, 49)


def scalable_text(text,xpos,ypos,frame_buffer,max_width=79):
    fd_variable = FontDrawer(frame_buffer=frame_buffer, font_name = 'dejav_m15')
    if len(text) * 9 >= max_width:
        if len(text) * 6 >= (max_width - 7):
            text = text[:8] + '..'
        elif len(text) * 8 >= max_width:
            fd_variable = FontDrawer(frame_buffer=frame_buffer, font_name = 'dejav_m12')
            ypos = ypos + 2
        else:
            fd_variable = FontDrawer(frame_buffer=frame_buffer, font_name='dejav_m10')
            ypos = ypos + 5
        
    fd_variable.print_str(text, xpos, ypos)


def sep_last_name(name,last_word_length=2):
    name = name.strip('.')
    name_parts = name.split(' ')
    if len(name_parts) > 2 and len(name_parts[-1]) <= last_word_length:
        return name_parts[-2] + ' ' + name_parts[-1]
    else:
        return name_parts[-1]

def print_arrow(state,xpos,ypos,arrow_driver):
    if state == 'Top':
        arrow_driver.print_char('S',xpos,ypos)
    elif state == 'Bottom':
        arrow_driver.print_char('T',xpos,ypos)