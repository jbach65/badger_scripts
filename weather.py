#!/usr/bin/env python3

import requests
from argparse import ArgumentParser
from os.path import expanduser
from pe_tools.pkgs.remote_client_connection import RemoteClientConnection
from paramiko.ssh_exception import SSHException
from time import sleep
from pprint import pprint
import datetime
import json
from tqdm import tqdm

WEATHERURL = 'https://api.openweathermap.org/data/2.5/forecast'
WEATHERAPI = '76287def41b8cc17812bb8652394362f'

#hard coded for now # TODO: pull from ~/.fleetapi/
FLEETURL = 'https://fleet.badger-technologies.com/api/web/v1/'
FLEETUSR = 'josh_steinbach@jabil.com'
FLEETPASS = '#JSBach4171997'

#not neccessary but am just using to look at individual bots in testing
botRequest = requests.get(FLEETURL+'robots', auth=(FLEETUSR, FLEETPASS))
botsJson = botRequest.json()
BOTS = {}
for bot in botsJson:
    BOTS[bot['name']] = bot

#pulling list of stores
storeRequest = requests.get(FLEETURL+'stores', auth=(FLEETUSR, FLEETPASS))
storesJson = storeRequest.json()
STORES = {}
ZIPS = {}
#looping through list of stores to get zip codes and generating dictionary of
for store in storesJson:
    STORES[store['id']] = store
    if store['solutions'] != None:
        if 'inspect' in store['solutions'] and 'insight' not in store['solutions'] and store['country_code'].lower() == 'us':
            if store['zip_code'] not in ZIPS.keys():
                ZIPS[store['zip_code']] = 1
            else:
                ZIPS[store['zip_code']] += 1
#remove entries with no zipcode
ZIPS.pop(None)


#loop through zips
clouds = {}
so_far = 0
for key in tqdm(ZIPS.keys()):
    wr = requests.get('{}?zip={},us&appid={}'.format(WEATHERURL, key, WEATHERAPI)).json()
    if 'list' in wr:
        segments = wr['list']
        for seg in segments:
            dateUnix = int(seg['dt']) - 14400 #simplest way in this case to convert from utc to est just subtract 4 hours in seconds
            if dateUnix not in clouds.keys(): #only used on first entry to initialize dictionary
                clouds[dateUnix] = seg['clouds']['all']*ZIPS[key]
            else:
                clouds[dateUnix] += seg['clouds']['all']*ZIPS[key] #the multiplying by number of stores in zip code to weight properly
        so_far += ZIPS[key] #increment accounting for weights
    sleep(1.1) #because I am on the free version of the weather api I only have 60 calls per minute so I program in a wait time so I don't exceed that

#divide the sum of percentages by the total number of percentages to get the average for each time block
for key in clouds.keys():
    clouds[key] = clouds[key]/so_far

#convert from unix time to human readable and print percentage average
for key in clouds.keys():
    print("{}:\t{}".format(datetime.datetime.utcfromtimestamp(int(key)).strftime('%Y-%m-%d %H:%M:%S'), clouds[key]))
