# TODO: add the following as command line arguments for more flexibility: organization, solution, acceptable lifecycle state

import requests
import json
import argparse
import sys
from pprint import pprint
from os.path import expanduser


FLEETURL = 'https://fleet.badger-technologies.com/api/web/v1/'


def get_version(bot, user, password):
    try:
        hb = requests.get('{}robots/{}/heartbeats?created_before=%222099-11-19T15:49:57.416Z%22&limit=1'.format(FLEETURL, bot['id']), auth=(user, password)).json()
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
    elif store['organization_id'] == 4:
        return "Woolworths"
    elif store['organization_id'] == 25:
        return "Woodmans"
    else:
        return "Other"

def generate_list(args):
    fleet_user = ""
    fleet_pass = ""

    if args.verbose:
        print("Reading credentials file...")

    file = args.creds
    if args.creds[0] == '~':
        home = expanduser("~")
        file = home + args.creds[1:]

    with open(file, 'r') as f:
        line = f.readline()
        fleet_user = line.split()[0]
        fleet_pass = line.split()[1]

    if args.verbose:
        print("Pulling list of bots...")


    botRequest = requests.get(FLEETURL+'robots', auth=(fleet_user, fleet_pass))
    botsJson = botRequest.json()

    if args.verbose:
        print("Pulling list of stores...")

    storeRequest = requests.get(FLEETURL+'stores', auth=(fleet_user, fleet_pass))
    storesJson = storeRequest.json()


    stores = {}
    for store in storesJson:
        stores[store['id']] = store

    bots = {}
    for bot in botsJson:
        bots[bot['name']] = bot

    if args.verbose:
        print("Checking software info on bots...")

    count = 0
    list = []
    for bot in botsJson:
        #print(bot['lifecycle_state'])
        if count < args.max_number:
            #if bot['lifecycle_state'].lower() in ('hold_for_service', 'store_hold'):
            #if bot['lifecycle_state'].lower() not in ('first_week', 'manufacturing', 'pre_install', 'install', 'service', 'maintenance', 'depot', 'internal_test', 'retired'):
            if bot['lifecycle_state'].lower() not in ('first_week', 'manufacturing', 'pre_install', 'install', 'hold_for_service', 'service', 'maintenance', 'store_hold', 'depot', 'internal_test', 'retired'):
                if get_organzation(stores[bot['store_id']]) == "Ahold":
                    if bot['solution'] == 'inspect':
                        version = get_version(bot, fleet_user, fleet_pass)
                        versionNum = version.split('-')[1]
                        if versionNum not in (args.release, ""):
                            if args.verbose:
                                sys.stderr.write(bot['name'] + ":\t" + '\x1b[1;31m' + versionNum.strip() + '\x1b[0m' + "\n")
                            else:
                                print(bot['name'])
                            #print(bot['name'] + ": \t" + version)
                            list.append(bot["name"])
                            count+=1
                        else:
                            #print(bot['name'] + ": \t" + version)
                            if args.verbose:
                                sys.stderr.write(bot['name'] + ":\t" + '\x1b[1;32m' + versionNum.strip() + '\x1b[0m' + "\n")


    print("Num of bots to be updated: " + str(count))
    return list

def write_file(filename, list_path):
    file = filename
    if filename[0] == "~":
        home = expanduser("~")
        file = home + filename[1:]

    with open(file, "w") as f:
        for bot in list:
            f.write(bot + "\n")


parser = argparse.ArgumentParser(description='A script to ganerate a list of bots to update')
parser.add_argument('-c', '--creds', default='~/.fleetapi/credentials_PRODUCTION', help='fleet credential file')
parser.add_argument('-o', '--output', default='~/bots', help='file to write list of bots')
parser.add_argument('-v', '--verbose', help='verbose output', action='store_true')
parser.add_argument('release', help='release you are going to (ex. 1.19.6)')
parser.add_argument('max_number', type=int, help='max number of bots to return')
args = parser.parse_args()

list = generate_list(args)
write_file(args.output, list)
