import requests
import json
from pprint import pprint

FLEETURL = 'https://fleet.badger-technologies.com/api/web/v1/'
FLEETUSR = 'josh_steinbach@jabil.com'
FLEETPASS = '#JSBach4171997'
MAX = 350
def get_version(bot):

    try:
        hb = requests.get('{}robots/{}/heartbeats?created_before=%222099-11-19T15:49:57.416Z%22&limit=1'.format(FLEETURL, bot['id']), auth=(FLEETUSR,FLEETPASS)).json()
        snaps = hb[0]['data']['snaps']
        for snap in snaps:
            if snap['name'] == 'bar-base':
                return snap['version']
        return ""
    except:
        return ""

def get_organzation(store):
    if store['organization_id'] == 1:
        return "Ahold"
    elif store['organization_id'] == 25:
        return "Woolworths"
    elif store['organization_id'] == 4:
        return "Woodmans"
    else:
        return "Other"


botRequest = requests.get(FLEETURL+'robots', auth=(FLEETUSR,FLEETPASS))
botsJson = botRequest.json()

storeRequest = requests.get(FLEETURL+'stores', auth=(FLEETUSR,FLEETPASS))
storesJson = storeRequest.json()


stores = {}
for store in storesJson:
    stores[store['id']] = store

bots = {}
for bot in botsJson:
    bots[bot['name']] = bot

count = 0
for bot in botsJson:
    #print(bot['lifecycle_state'])
    if count < MAX:
        #if bot['lifecycle_state'].lower() in ('hold_for_service', 'store_hold'):
        if bot['lifecycle_state'].lower() not in ('first_week', 'manufacturing', 'pre_install', 'install', 'service', 'maintenance', 'depot', 'internal_test', 'retired'):
        #if bot['lifecycle_state'].lower() not in ('first_week', 'manufacturing', 'pre_install', 'install', 'hold_for_service', 'service', 'maintenance', 'store_hold', 'depot', 'internal_test', 'retired'):
            if get_organzation(stores[bot['store_id']]) == "Ahold":
                if bot['solution'] == 'inspect':
                    #print(bot['name'] + ": \t" + get_version(bot))
                    if get_version(bot).split('-')[1] not in ("1.18.0", ""):
                        print(bot['name'])
                        count+=1
print("Num of bots to be updated: " + str(count))
