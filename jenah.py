#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, time, sys, math, datetime, requests, Adafruit_CharLCD as LCD
from bs4 import BeautifulSoup as BS

# settings for the display
Station = "Universität"
ReloadTime = 20
SwitchTime =  2
ExcludeList = ("")

# Raspberry Pi pin configuration:
lcd_rs        = 26
lcd_en        = 19
lcd_d4        = 13
lcd_d5        =  6
lcd_d6        =  5
lcd_d7        = 11
lcd_backlight =  4

# define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

def getStations():
    url = "https://www.nahverkehr-jena.de/index.php?eID=ajaxDispatcher&request[pluginName]=Stopsmonitor&request[controller]=Stopsmonitor&request[action]=getAllStops"
    headers = { 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }
    stations = []
    try:
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=5.0)
        raw = json.loads(r.text)        
        for i, arr in enumerate(raw):
            stations.append( arr["children"]["name"][0]["value"] )        
    except:
        return False    
    return stations
    
def getStationInfo(station="Universität"):    
    url = "https://www.nahverkehr-jena.de/fahrplan/haltestellenmonitor.html"
    values = { 'tx_akteasygojenah_stopsmonitor[stopName]': station }    
    try:
        r = requests.post(url, data=values, allow_redirects=True, timeout=5.0)
        soup = BS(r.text, 'html.parser')    
        items = soup.find("tbody").find_all("tr")   
        res = [[0 for x in range(3)] for y in range(len(items))]
        for i, item in enumerate(items):
            iitem = item.find_all("td")
            for idx, line in enumerate(iitem):
                res[i][idx] = line.text.replace("in ", "").replace("Kürze...", " 1 min").replace(" min", "'").strip()      
    except:
        return False    
    return res

def getFirstLine():
    Days = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"]
    return Days[int(time.strftime("%w"))] + " " + time.strftime("%d.%m.  %H:%M") + "\n"

if __name__ == "__main__":    
    
    # LCD initialization
    lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)
    lcd.set_backlight(1)
    lcd.clear()
    lcd.message('Initialisierung\nBitte warten...')

    # wait for Wifi
    time.sleep( 2 )

    stations = getStations()

    if ( stations == False ):
        while stations == False:
            lcd.clear()
            lcd.message('Ohoh! :-(\nkein Internet!')
            time.sleep( ReloadTime )
            stations = getStations()

    if ( Station not in stations ):
        while True:
            lcd.clear()
            lcd.message('    Station     \nnicht  gefunden!')
            time.sleep( ReloadTime )
            stations = getStations()

    TimePassed = ReloadTime 
    MultiPage = False
    s = getFirstLine() 
           
    while True:
        
        TimePassed += SwitchTime

        if ( TimePassed >= ReloadTime ):
            TimePassed = 0
            s = getFirstLine() 
            n = 0
    
            req = getStationInfo(station=Station)

            if ( req != False ):
                for i in range(len(req)):
                    if ( req[i][1] not in ExcludeList ):
                        if ( req[i][2][1] == "'" ):
                            s += ("{:>2} {:<10} {:>2}\n".format(int(req[i][0]), req[i][1][:10], req[i][2][:2]))
                        else:
                            s += ("{:>2} {:<9} {:>3}\n".format(int(req[i][0]), req[i][1][:9], req[i][2][:3]))
                        n += 1
                        if ( n >= 3 ):
                            break
            
            if ( n > 1 ):
                MultiPage = True
            else:
                MultiPage = False 
                if ( n == 0 ):
                    s += "keine Busse  :-("

            lcd.clear()
            lcd.message(s)
        
        if ( MultiPage ):
            lcd.clear()
            if ( ( TimePassed / SwitchTime ) % 2 ):
                lcd.message(s[34:])
            else:
                lcd.message(s[0:33])

        time.sleep( SwitchTime )

