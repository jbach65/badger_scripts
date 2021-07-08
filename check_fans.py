#!/usr/bin/env python3

import requests
from argparse import ArgumentParser
from multiprocessing import Process, Queue, freeze_support
from os.path import expanduser
from pe_tools.pkgs.remote_client_connection import RemoteClientConnection
from badger_pylibs.badger_jira.badger_jira import PeTicket
from paramiko.ssh_exception import SSHException
from time import sleep
from pprint import pprint
import datetime

FLEETURL = 'https://fleet.badger-technologies.com/api/web/v1/'
FLEETUSR = 'josh_steinbach@jabil.com'
FLEETPASS = '#JSBach4171997'

if 1==1:
    botRequest = requests.get(FLEETURL+'robots', auth=(FLEETUSR, FLEETPASS))
    botsJson = botRequest.json()
    BOTS = {}
    for bot in botsJson:
        BOTS[bot['name']] = bot

    storeRequest = requests.get(FLEETURL+'stores', auth=(FLEETUSR, FLEETPASS))
    storesJson = storeRequest.json()
    STORES = {}
    for store in storesJson:
            STORES[store['id']] = store

#convert from bytes for more readable output
def decode_output_list(lst):
    nu = []
    for line in lst:
        nu.append(line.decode('utf-8'))
    return nu

def decode_output(line):
    return line.decode('utf-8')

#helps to format output
def get_file_name_from_path(file):
    if len(file.split("/")) > 1:
        return file.split("/")[-1]
    return file

def get_version(bot):
    try:
        hb = requests.get('{}robots/{}/heartbeats?created_before=%222099-11-19T15:49:57.416Z%22&limit=1'.format(FLEETURL, bot['id']), auth=(FLEETUSR, FLEETPASS)).json()
        snaps = hb[0]['data']['snaps']
        for snap in snaps:
            if snap['name'] == 'bar-base':
                return snap['version']
        return ""
    except:
        return ""


def log_pe_issue(bot, summary, description):
    pe_ticket = PeTicket()

    store_data = STORES[BOTS[bot]['store_id']]
    description = "The following error(s) occurred while updating FW:\n{}".format(description)
    print(bot)
    print(get_version(BOTS[bot]))
    print(bot)
    #logging.debug("JIRA SUMMARY: {} - Failed FW update - {}".format(robot_api.robot_name, summary))
    #logging.debug("JIRA DESC: {}".format(description))
    ticket = pe_ticket.create_field_issue_ticket(
        summary="TEST",
        description="description",
        bar="{}".format(bot),
        track_code="FW Update",
        store="{}".format(store_data['name']),
        versions=[{"name": get_version(BOTS[bot])}]
    )
    try:
        ticket = pe_ticket.create_field_issue_ticket(
            summary="TEST",
            description="description",
            bar="{}".format(bot),
            track_code="FW Update",
            store="{}".format(store_data['name']),
            versions=[{"name": get_version(bot)}]
        )
        return ticket.key
    except:
        return "UNABLE TO LOG PE TICKET"

def run_script(bot, args):
    try:
        output = []
        output.append(bot)
        con = RemoteClientConnection(bot, args.ssh_key, args.env, port = 2222)
        sleep(.5)
        con.connect()
        status = con.exec_command("bar-base.bash -c 'rostopic echo /Control/status/status -n 1'")
        output.append("Status:")
        if status != None:
            output.append(decode_output(status[0]))
        fans = con.exec_command("sudo modprobe it87; bar-base.bash -c 'sensors | grep -i fan'")
        output.append("Truck:")
        output.append(decode_output(fans[0]))
        con = RemoteClientConnection(bot, args.ssh_key, args.env, port = 3222)
        sleep(.5)
        con.connect()
        fans = con.exec_command("sudo modprobe it87; insight-payload.bash -c 'sensors | grep -i fan'")
        output.append("Payload:")
        output.append(decode_output(fans[1])) #we only care about the second fan here. The first was removed to make room for the hd
        return output

    except SSHException as e:
        print("Failed: {}".format(e))
        return

    finally:
        #con.close()
        print("")


if __name__ == '__main__':
    parser = ArgumentParser(description='Script to check fans on a list of bots')
    parser.add_argument('bot_list', help='File containing list of bots (BARXXX\n format)')
    parser.add_argument('--ssh_key', default=expanduser("~/.ssh/barkey"), help='SSH key file EX: /home/jsbach/.ssh/barkey')
    parser.add_argument('--env', default="PRODUCTION", help='Current Env of bot')
    args = parser.parse_args()
    bot_list = []


    with open(args.bot_list, 'r') as file:
        for line in file:
            bot_list.append(line.strip())


    #print(log_pe_issue("BAR813", "SUMMARY GOES HERE", "This is a description"))
    pprint(STORES[BOTS['BAR144']['store_id']])
    results = []
    print(datetime.datetime.now())
    for bot in bot_list:
        result = run_script(bot, args)
        for line in result:
            pprint(line)
        print("")
