#get bot list
#need to figure out which metrics to sort on
#organization, code level, solution
import random
import requests
import json
import argparse
import sys
from pprint import pprint
from os.path import expanduser


FLEETURL = 'https://fleet.badger-technologies.com/api/web/v1/'
FLEET_USER = ""
FLEET_PASS = ""

def get_creds(file):
    if file[0] == '~':
        home = expanduser("~")
        file = home + file[1:]

    with open(file, 'r') as f:
        line = f.readline()
        return line.split()[0], line.split()[1]

#following 4 functions just pull fleet data and format nicely
def pull_organizations():
    orgRequest = requests.get(FLEETURL+'organizations', auth=(FLEET_USER, FLEET_PASS))
    orgsJson = orgRequest.json()
    orgDict = {}
    for item in orgsJson:
        orgDict[item['id']] = item
    return orgDict

def pull_robots():
    botRequest = requests.get(FLEETURL+'robots', auth=(FLEET_USER, FLEET_PASS))
    botsJson = botRequest.json()
    return botsJson

def pull_stores():
    storeRequest = requests.get(FLEETURL+'stores', auth=(FLEET_USER, FLEET_PASS))
    storesJson = storeRequest.json()
    storesDict = {}
    for item in storesJson:
        storesDict[item['id']] = item
    return storesDict

def pull_models():
    modelRequest = requests.get(FLEETURL+'robot_models', auth=(FLEET_USER, FLEET_PASS))
    modelsJson = modelRequest.json()
    modelsDict = {}
    for item in modelsJson:
        modelsDict[item['id']] = item
    return modelsDict

#makes fleet call and parses for bar-base version
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

#handles filtering of bots based on input parameters
def generate_list(args):
    if args.verbose:
        print("Pulling list of stores...")
    stores = pull_stores()
    if args.verbose:
        print("Pulling list of robots...")
    bots = pull_robots()
    if args.shuffle:
        random.shuffle(bots)
    if args.verbose:
        print("Pulling list of organizations...")
    orgs = pull_organizations()
    if args.verbose:
        print("Pulling list of robot models...")
    models = pull_models()

    if args.verbose:
        print("Beginning robot filtering...")

    list = []
    count = 0
    for bot in bots:
        if count < int(args.number):
            org_check = args.organization.lower() in orgs[stores[bot['store_id']]['organization_id']]['name'].lower()
            lifecycle_check = bot['lifecycle_state'] in ['fully_operational', 'hold_for_service', 'store_hold', 'level_3_support']
            model_check = ( args.model == -1 or args.model == bot['robot_model_id'] )
            if org_check and lifecycle_check and model_check:
                version = get_version(bot, FLEET_USER, FLEET_PASS)
                version_check = args.release in version
                if version_check != args.exclude:
                    name = bot['name']
                    print(f"{name}:   \t{version}")
                    list.append(bot['name'])
                    count += 1
    print(f"Total: {len(list)}")
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
parser.add_argument('-w', '--write', default='~/bots', help='file to write list of bots to (~/bots by default)')
parser.add_argument('-v', '--verbose', help='verbose output', action='store_true')
parser.add_argument('-s', '--shuffle', help='shuffle list of bots from fleet to promote random rollout', action='store_true')
parser.add_argument('-e', '--exclude', help='if present bot will only select all bots NOT on the provided release', action='store_true')
parser.add_argument('-n', '--number', help='max number of bots', default = "100")
parser.add_argument('-r', '--release', default='1.24', help='release you are looking for(unless exclude-version flag is present) (ex. 1.19.6 or just 1.19)')
parser.add_argument("-o", "--organization", choices={'Woodmans', 'Woolworths', 'Ahold'}, default="Ahold", help='organization')
parser.add_argument("-m", "--model", type=int,  default="-1", help='robot model number (3 for Inspect PVT) (-1 for all models)')
#may implement list flag so we can see all possible options for models and orgs, not necessary yet though
#parser.add_argument('-l', '--list', nargs=0 , help='list all model and org options', action=ListAction)
args = parser.parse_args()


FLEET_USER, FLEET_PASS = get_creds(args.creds)
list = generate_list(args)
write_file(args.write, list)
