import uasyncio

''' ----------------------------
------SCHEDULING FUNCTIONS------
-----------------------------'''

from ustats import schedule
async def gameday_state(datetime, lock, log, max_retries=5, wait_time=60):
    # pre-game (using datetime) live updates -> during game (using global stats) -> postgame (static)
    global daily_schedule
    daily_schedule = {}
    
    while True:
        await lock.acquire()
        log.info('Gameday state function acquired schedule lock')
        try:
            game_data = schedule()
        except Exception as e:
            log.error('Failed to get game schedule data. Retrying in {} seconds.'.format(wait_time))
            log.error(e)
            log.info('Gameday state function released schedule lock')
            lock.release()
            continue

        # if game_data['game_status'] == 'Scheduled' and old_status == 'Postgame':
        #     from machine import reset 
        #     reset()
        if game_data['game_status'] != None:
            daily_schedule['is_baseball'] = True
            daily_schedule['game_datetime'] = game_data['game_datetime']
            daily_schedule['gamePk'] = game_data['gamePk']
            daily_schedule['game_status'] = game_data['game_status']
            daily_schedule['home_team'] = game_data['home_team']
            daily_schedule['away_team'] = game_data['away_team']
            daily_schedule['home_record'] = game_data['home_record']
            daily_schedule['away_record'] = game_data['away_record']
        else:
            daily_schedule['is_baseball'] = False

        if daily_schedule.get('is_baseball'):
            try:
                gmt_mo,gmt_d,h,m = datetime.get_datetime_gmt()[1:5]
            except TypeError:
                log.error('Failed to get date/time. Retrying in {} seconds.'.format(wait_time))
                log.info('Gameday state function released schedule lock')
                lock.release()
                continue
            current_time_min = (60*h) + m + (24 * 60 * gmt_d) + (24 * 60 * 30 * gmt_mo)
            log.info('Current time GMT: {}:{}, day: {}, minute-form: {}'.format(h,m,gmt_d,current_time_min))

            game_mo,game_d,h,m = daily_schedule['game_datetime'][1:5]
            game_time_min = (60*h) + m + (24 * 60 * game_d) + (24 * 60 * 30 * game_mo)
            log.info('Game time GMT: {}:{}, day: {}, minute-form: {}'.format(h,m, game_d,game_time_min))


            if (current_time_min < (game_time_min - 10)) and (daily_schedule['game_status'] != 'Postponed'):
                log.info('state = pregame')
                daily_schedule['gameday_state'] = 'Pregame'
                
            else:
                
                if daily_schedule['game_status'] == 'Scheduled' or daily_schedule['game_status'] == 'Warmup':
                    log.info('state = immediate pregame')
                    daily_schedule['gameday_state'] = 'Immediate Pregame'
                elif daily_schedule['game_status'] == 'In Progress':
                    log.info('state = in progress')
                    daily_schedule['gameday_state'] = 'In Progress'
                elif daily_schedule['game_status'] == 'Game Over':
                    log.info('state = game over/postgame')
                    daily_schedule['gameday_state'] = 'Postgame'
                elif daily_schedule['game_status'] == 'Postponed':
                    log.info('state = game postponed')
                    daily_schedule['gameday_state'] = 'Postponed'
                else:
                    log.warning('state unknown, reverting to postgame')
                    daily_schedule['gameday_state'] = 'Postgame'

        log.info('Gameday state function released schedule lock')
        lock.release()
        old_status = game_data['game_status']
        await uasyncio.sleep(wait_time)
        
        
''' ----------------------------
---------SYSTEM FUNCTIONS-------
-----------------------------'''

import gc
async def collect_garbage(freq=60):
    while True:
        gc.collect()
        gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
        print('Garbage collected')
        print('Memory allocated: {}'.format(gc.mem_alloc()))
        print('Memory free: {}'.format(gc.mem_free()))
        await uasyncio.sleep(freq)


import ntptime
from config import time_settings
ntptime.host = time_settings['host']
try:
    import time as utime
except:
    import utime
class Time:
    def __init__(self):
        self.offset = self.get_offset()

    def get_offset(self):
        time_offset = 25200

        return time_offset
    
    def get_datetime(self):
        self.set_time()

        now = self.get_network_time()
        return self.local_time(now - self.offset)
        #year, month, day, hour, minute, second, weekday, yearday
    
    def get_datetime_gmt(self):
        self.set_time()
        now = self.get_network_time()
        return self.local_time(now)
        #year, month, day, hour, minute, second, weekday, yearday

    def set_time(self):
        try:
            ntptime.settime()
        except OSError:
            pass
        except OverflowError:
            pass
    
    @staticmethod
    def get_network_time(max_retries=30):
        for i in range(max_retries):
            try:
                return ntptime.time()
            except OSError:
                utime.sleep(5)
                print('Network time check failed, retrying...')
                if i > (max_retries // 2):
                    do_connect(WLAN['ssid'],WLAN['password'])
                continue
    
    @staticmethod
    def local_time(time, max_retries=5):
        for i in range(max_retries):
            try:
                # return utime.localtime(time)
                # stole this line from https://github.com/micropython/micropython/issues/6456#issuecomment-820364533
                return utime.localtime(time if time < 0x80000000 else time - 0x100000000)
            except OverflowError:
                utime.sleep(5)
                print('Local time check failed, retrying...')
                continue


from config import WLAN
import network
#Async network function
async def check_connection(sta_if):
    if not sta_if.isconnected():
        do_connect(WLAN['ssid'],WLAN['password'], sta_if)
    await uasyncio.sleep(60)

#Synchronous network function
def do_connect(ssid, password, sta_if):
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())


async def periodic_reset():
    while True:
        hour = 60*60
        await uasyncio.sleep(hour) #This is at the beginning of the function to prevent a boot loop

        from machine import reset
        reset()

import logging
def logger():
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("Main")
    logging.getLogger().addHandler(Handler())
    return log

#borrowed from https://github.com/micropython/micropython-lib/blob/master/python-stdlib/logging/example_logging.py
class Handler(logging.Handler):
    def emit(self, record):
        print("%(levelname)s: %(message)s" % record.__dict__)



''' ----------------------------
--------DISPLAY FUNCTIONS-------
-----------------------------'''
from display import init_display
async def display_initializer(lock):
    await lock.acquire()
    print('Display initializer acquired display lock.')
    s,fd,ar,g = init_display()

    lock.release()
    print ('Display initializer released display lock.')
    return s,fd,ar,g

from display import live_scoreboard, pregame_scoreboard, postgame_scoreboard, postponement_scoreboard, no_game_scoreboard
from ustats import live_game_events, upcoming_game_events, postgame_events, upcoming_game_hitters, postponed_game_events, next_game
async def display_update_loop(s, fd, ar, g, schedule_lock, display_lock, log, max_retries=5):
    global daily_schedule
    hitter_stats = {}
    stats = {}

    while True:
        await display_lock.acquire()
        log.info('Display buffer acquired display lock.')
        await schedule_lock.acquire()
        log.info('Display buffer acquired schedule lock.')
        if daily_schedule.get('is_baseball'):
            if daily_schedule.get('gameday_state') == 'In Progress':

                s.fill(0) #empty the display buffer

                for i in range(max_retries):
                    try:
                        gc.collect()
                        stats = live_game_events(daily_schedule['gamePk']) #retrieve game stats
                        break 
                    except MemoryError:
                        log.error('Not enough memory for HTTP requests, collecting garbage...')
                        gc.collect()
                    except OSError:
                        log.error('Error retrieving game information, retrying...')
                        await uasyncio.sleep(1)
                    except IndexError as e:
                        log.error('Error retrieving game information, retrying...')
                        log.error(e)
                        await uasyncio.sleep(1)
                    except Exception as e:
                        log.error('Unspecified error retrieving game stats, retrying')
                        log.error(e)
                        break

                for i in range(max_retries):
                    if not hitter_stats.get('ID{}'.format(stats['batter_id'])):       #fallback retrieve hitter stats, should only run once
                        try:
                            log.info('Retrieving pregame hitter stats')
                            gc.collect()
                            hitter_stats = upcoming_game_hitters(daily_schedule['gamePk'])
                            gc.collect()
                            break
                        except MemoryError:
                            log.error('Not enough memory for HTTP requests, collecting garbage...')
                            gc.collect()
                        except OSError:
                            log.error('Error retrieving hitter information, retrying...')
                            await uasyncio.sleep(1)
                        except Exception:
                            log.error('Unspecified error retrieving hitter stats, retrying')
                            break
                
                if not stats:
                    await uasyncio.sleep(15)
                    display_lock.release()
                    log.info('Display buffer released display lock.')
                    schedule_lock.release()
                    log.info('Display buffer released schedule lock.')
                    continue

                for i in range(max_retries):
                    try:
                        live_scoreboard(stats,hitter_stats,s,fd,ar,g) #fill buffer
                        break
                    except MemoryError:
                        log.error('Display buffer out of memory, collecting garbage...')
                        gc.collect()
                    except Exception as e:
                        log.error('Unspecified error writing to display buffer, retrying')
                        log.error(e)
                        break

                s.show() #push buffer to display, should change to another function later

            elif (daily_schedule.get('gameday_state') == 'Pregame') or (daily_schedule.get('gameday_state') == 'Immediate Pregame'):
                # stats = {}
                s.fill(0) #empty the display buffer

                for i in range(max_retries):
                    try:
                        gc.collect()
                        stats = upcoming_game_events(daily_schedule['gamePk']) #retrieve game stats
                        if (daily_schedule.get('gameday_state') == 'Immediate Pregame') and not hitter_stats: #retrieve dictionary of hitter stats, should only run once
                            gc.collect()
                            hitter_stats = upcoming_game_hitters(daily_schedule['gamePk'])
                            gc.collect()
                        break 
                    except MemoryError:
                        log.error('Not enough memory for HTTP request, collecting garbage...')
                        gc.collect()
                    except OSError:
                        log.error('Error retrieving game information, retrying...')
                        await uasyncio.sleep(1)
                    except Exception as e:
                        log.error('Unspecified error retrieving pregame stats, retrying')
                        log.error(e)
                        break

                for i in range(max_retries):
                    try:
                        pregame_scoreboard(stats,daily_schedule,s,fd,ar,g,immediate_pregame=(daily_schedule.get('gameday_state') == 'Immediate Pregame')) #fill buffer
                        break
                    except MemoryError:
                        log.error('Display buffer out of memory, collecting garbage...')
                        gc.collect()
                    except Exception as e:
                        log.error('Unspecified error writing to display buffer, retrying')
                        log.error(e)
                        break
                
                s.show() #push buffer to display, should change to another function later

            elif daily_schedule.get('gameday_state') == 'Postgame':
                hitter_stats = {}
                stats = {}
                s.fill(0) #empty the display buffer

                for i in range(max_retries):
                    try:
                        gc.collect()
                        stats = postgame_events(daily_schedule['gamePk']) #retrieve game stats
                        break 
                    except MemoryError:
                        log.error('Not enough memory for HTTP request, collecting garbage...')
                        gc.collect()
                    except OSError:
                        log.error('Error retrieving game information, retrying...')
                        await uasyncio.sleep(1)
                    except Exception as e:
                        log.error('Unspecified error retrieving postgame stats, retrying')
                        log.error(e)
                        break

                for i in range(max_retries):
                    try:
                        postgame_scoreboard(stats,s,fd,ar,g) #fill buffer
                        break
                    except MemoryError:
                        log.error('Display buffer out of memory, collecting garbage...')
                        gc.collect()
                    except Exception as e:
                        log.error('Unspecified error writing to display buffer, retrying')
                        log.error(e)
                        break
                
                s.show() #push buffer to display, should change to another function later
            
            elif daily_schedule.get('gameday_state') == 'Postponed':
                stats = {}
                s.fill(0)
                
                for i in range(max_retries):
                    try:
                        gc.collect()
                        stats = postponed_game_events(daily_schedule['gamePk']) #retrieve game stats
                        break 
                    except MemoryError:
                        log.error('Not enough memory for HTTP request, collecting garbage...')
                        gc.collect()
                    except OSError:
                        log.error('Error retrieving game information, retrying...')
                        await uasyncio.sleep(1)
                    except Exception as e:
                        log.error('Unspecified error retrieving postgame stats, retrying')
                        log.error(e)
                        break
                for i in range(max_retries):
                    try:
                        postponement_scoreboard(stats, daily_schedule,s,fd,ar,g) #fill buffer
                        break
                    except MemoryError:
                        log.error('Display buffer out of memory, collecting garbage...')
                        gc.collect()
                    except Exception as e:
                        log.error('Unspecified error writing to display buffer, retrying')
                        log.error(e)
                        break
                
                s.show() #push buffer to display, should change to another function later

        else: #If no game that day
            s.fill(0)

            stats = upcoming_game_events(next_game())
            no_game_scoreboard(stats, s, fd, ar, g)

            s.show()
            
        display_lock.release()
        log.info('Display buffer released display lock.')
        schedule_lock.release()
        log.info('Display buffer released schedule lock.')
        await uasyncio.sleep(15)

''' ----------------------------
----------MAIN FUNCTION---------
-----------------------------'''

from uasyncio import Lock
from boot import sta_if
async def main():
    log = logger()

    datetime = Time()                # Initialize time object
    schedule_lock = uasyncio.Lock()  # Initialize schedule lock object
    display_lock  = uasyncio.Lock()  # Initialize display lock object (prevent access to display until it has initialized)

    s,fd,ar,g = await display_initializer(lock=display_lock)

    loop = uasyncio.get_event_loop() # Create event loop
    # loop.create_task(get_gameday(datetime=datetime, lock=schedule_lock)) 
    loop.create_task(gameday_state(datetime=datetime, lock=schedule_lock, log=log))
    loop.create_task(display_update_loop(s, fd, ar, g, schedule_lock=schedule_lock, display_lock=display_lock, log=log))
    loop.create_task(collect_garbage())
    loop.create_task(check_connection(sta_if))
    loop.create_task(periodic_reset())
    await loop.run_forever()

def run():
    try:
        uasyncio.run(main())
    finally:
        uasyncio.new_event_loop()

if __name__ == '__main__':
    # pass
    run()