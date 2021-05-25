# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import webrepl
webrepl.start()

from config import WLAN
import network

sta_if = network.WLAN(network.STA_IF)
def do_connect(ssid, password, sta_if):
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

do_connect(WLAN['ssid'],WLAN['password'], sta_if)