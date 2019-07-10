#!/usr/bin/env python3

import os
import sys
import signal
import time

import urllib.request
import xml.etree.ElementTree as ET
from matplotlib import pyplot as plt

import pandas as pd
from pandas.io.json import json_normalize
import json
import datetime
import random

import twitterer
from daemoner import Daemon, log

from plots import *
from credentials import *

workingdir = '/home/msj/vanbusbot/'
nhours = 6 # number of tweets per day

def g():
    twitterer.warning("@vanbusbot is shutting down")


def vanbusbot():
    
    hour = datetime.datetime.now().hour
    day = datetime.datetime.now().day
    hours = list(range(24))
    todayhours = hours
    
    while True:
        
        # Load data file or create empty dataframe    
        try:
            df = pd.read_csv(f'{workingdir}/hourly_buses.csv')
            df.RecordedTime = pd.to_datetime(df.RecordedTime)
            log("Loaded hourly_buses.csv")
        except:
            df = pd.DataFrame()
            log("Created new hourly_buses.csv")
            
            
        # Once a day get a list of hours to tweet
        if day != datetime.datetime.now().day:
            day = datetime.datetime.now().day
            todayhours = random.shuffle(hours)[:nhours]
            log(f"Today's tweet will be at: {todayhours}")
            
        #Once and hour
        if hour != datetime.datetime.now().hour:
            hour = datetime.datetime.now().hour
            
            if hour in todayhours:
                log("Making plots...")
                plot = BusPlot(f'{workingdir}/hourly_buses.csv')
                plot.trim()

                plot.make_ani(f'{workingdir}/ani_current.gif')
                plt.close('all')
                del plot

                try:
                    copyfile(f'{workingdir}/ani_current.gif', f'{workingdir}/ani_lasthour.gif')
                except:
                    pass
            
            
                if hour in todayhours:
                    try:
                        log("Tweeting plot...")
                        twitterer.tweet('VanBusBot',"",media=[f'{workingdir}/ani_current.gif'])
                        log("Tweeted ani_current.gif")
                    except Exception as e:
                        log("Tweet failed due to the following exception:")
                        log(str(e))
                    try:
                        os.remove(f'{workingdir}/ani_current.gif')
                    except:
                        pass

            # Trim df so it only contains data from the last hour
            now = datetime.datetime.now()
            thishour = now.strftime('%Y-%m-%d %H:00:00')
            thishour = datetime.datetime.strptime(thishour,'%Y-%m-%d %H:%M:%S')
            lasthour = (now - datetime.timedelta(hours=1)).strftime('%Y-%m-%d %H:00:00')
            lasthour = datetime.datetime.strptime(lasthour,'%Y-%m-%d %H:%M:%S')
            df = df[df.RecordedTime>lasthour]

        log("query...")
        # Query Translink API
        u = f"http://api.translink.ca/rttiapi/v1/buses?apikey={translink_api_key}"

        attnames = ['VehicleNo','TripId','RouteNo',
                'Direction','Pattern','RouteMap','Latitude','Longitude','RecordedTime','Href']

        ## Try to query
        try:
            with urllib.request.urlopen(u) as url:
                data = url.read().decode()
        except Exception as e:
            log("Unable to query Translink due to the following exception:")
            log(e)
            continue
            
        buses = ET.fromstring(data)
        ndf = pd.DataFrame()
        for bus in buses:
            atts = [att.text for att in bus]
            atts = {name:att for name,att in zip(attnames,atts)}
            ndf = ndf.append(atts,ignore_index=True)


        ndf.RecordedTime = pd.to_datetime(ndf.RecordedTime)

        ##########################
        # This is necessary because just after midnight, RecordedTime values will be
        # on both sides of midnight. The translink data only provides time not date info,
        # so pd.to_datetime assigns the current date instead of yesterday's date.
        now = datetime.datetime.now()
        ndf.RecordedTime = ndf.RecordedTime.map(lambda x: x - datetime.timedelta(1) if x > now else x )
        #########################

        ndf.Latitude = ndf.Latitude.astype(float)
        ndf.Longitude = ndf.Longitude.astype(float)
        ndf = ndf[ndf.Latitude!=0]  # Drop lats/long == 0
        ndf['QueryTime'] = datetime.datetime.now()

        df = df.append(ndf)
        df = df.drop_duplicates()

        
        df.to_csv(f'{workingdir}/hourly_buses.csv',index=False)
        
        del df
        del ndf
        del data
        del buses
        del url
        
#         from pympler import asizeof
#         for name, obj in locals().items():
#             if name != 'asizeof':
#                 log(name)
#                 log(asizeof.asizeof(obj) / 1024)
                
        time.sleep(55)
        

d = Daemon(f=vanbusbot,pidfilename=f'{workingdir}/daemon.pid',g=g)
d.run() 
