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

WEATHERURL = 'https://api.openweathermap.org/data/2.5/forecast'
WEATHERAPI = '76287def41b8cc17812bb8652394362f'

FLEETURL = 'https://fleet.badger-technologies.com/api/web/v1/'
FLEETUSR = 'josh_steinbach@jabil.com'
FLEETPASS = '#JSBach4171997'

#not neccessary butam just using to look at individual bots in testing
botRequest = requests.get(FLEETURL+'robots', auth=(FLEETUSR, FLEETPASS))
botsJson = botRequest.json()
BOTS = {}
for bot in botsJson:
    BOTS[bot['name']] = bot

storeRequest = requests.get(FLEETURL+'stores', auth=(FLEETUSR, FLEETPASS))
storesJson = storeRequest.json()
STORES = {}
ZIPS = {}
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
#wr = requests.get('{}?zip={},us&appid={}'.format(WEATHERURL, '01007', WEATHERAPI))
#pprint(wr.json())
#wr = requests.get('{}?zip={},us&appid={}'.format(WEATHERURL, '01007', WEATHERAPI)).json()

clouds = {}
so_far = 0
for key in ZIPS.keys():
    wr = requests.get('{}?zip={},us&appid={}'.format(WEATHERURL, key, WEATHERAPI)).json()
    if 'list' in wr:
        segments = wr['list']
        for seg in segments:
            dateUnix = seg['dt_txt']
            tmp = {}
            tmp['percentage']
            if dateUnix not in clouds.keys():
                clouds[dateUnix] = seg['clouds']['all']*ZIPS[key]
            else:
                clouds[dateUnix] += seg['clouds']['all']*ZIPS[key]
        so_far += ZIPS[key]
    print(so_far)
    sleep(1.1)

pprint(clouds)

for key in clouds.keys():
    clouds[key] = clouds[key]/so_far

pprint(clouds)


#pprint(STORES[BOTS['BAR144']['store_id']])
