#!/usr/bin/env python3

import requests
import json
import socket
from socket import AF_INET, SOCK_DGRAM
from argparse import ArgumentParser
from multiprocessing import Process, Queue, freeze_support
from os.path import expanduser
from pe_tools.pkgs.remote_client_connection import RemoteClientConnection
from badger_pylibs.badger_jira.badger_jira import PeTicket
from paramiko.ssh_exception import SSHException
from time import sleep
from pprint import pprint
import datetime

SR_TEST_URL = 'https://hooks.slack.com/services/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'
WOODMANS_URL = 'https://hooks.slack.com/services/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'
WOOLWORTHS_URL = 'https://hooks.slack.com/services/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'
FLEETURL = 'https://fleet.badger-technologies.com/api/web/v1/'
FLEETUSR = 'josh_steinbach@jabil.com'
FLEETPASS = '#JSBach4171997'
HERE = '<!here>'
JOSH = '<@UUG6FMJQ7>'
MATT = '<@UHXNTLBQW>'
JAMIE = '<@UDKLJFK3L>'

# TODO: only check payload if robot is certain solution
# TODO: add data to sharepoint
# TODO: read fleet creds from file in .fleetapi
# TODO: remove webhooks and put them somewhere else

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

def slack_post(org, bot, fan):
    data = {
        'text': '{} {}: {}\'s {} fan is not spinning. A technician needs to be dispatched to replace that fan if that has not already been done.'.format(JOSH, MATT, bot, fan),
        'username': 'fan_checker',
        'icon_emoji': ':robot_face:'
    }
    if org == 'Woodmans':
        #slack_response = requests.post(WOODMANS_URL, data=json.dumps(data), headers={'Content-Type': 'application/json'})
        slack_response = requests.post(SR_TEST_URL, data=json.dumps(data), headers={'Content-Type': 'application/json'})
    elif org == 'Woolworths':
        #slack_response = requests.post(WOOLWORTHS_URL, data=json.dumps(data), headers={'Content-Type': 'application/json'})
        slack_response = requests.post(SR_TEST_URL, data=json.dumps(data), headers={'Content-Type': 'application/json'})
    return slack_response.status_code

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
        # this variable is to check is a connection was opened so we know if we need to close it in the finally block
        connectionEstablished = False
        con = RemoteClientConnection(bot, args.ssh_key, args.env, port = 2222)
        sleep(.5)
        #this shouldnt have to be here but until the error in pe_tools gets fixed it is a necessary evil
        latest_heartbeat = con.fleet.get_latest_heartbeat().json()
        if len(latest_heartbeat) == 0:
            raise Exception("No recent heartbeats found. Aborting to avoid IndexError in remote_client_connection.py")
        #proceed with the rest of the script
        connectionEstablished = True
        #check vpn state so we know if we need to close it at the end or leave it open
        vpn_state = latest_heartbeat[0]['data']['vpn']['state']

        #connect to the bot (or die trying)
        con.connect()

        #greab bot status for logging
        status = con.exec_command("bar-base.bash -c 'rostopic echo /Control/status/status -n 1'")
        output.append("Status:")
        if status != None:
            bot_status = decode_output(status[0])
            output.append(bot_status)

        #get truck fan speed
        fans = con.exec_command("sudo modprobe it87; bar-base.bash -c 'sensors | grep -i fan'")
        output.append("Truck:")
        truck = int(decode_output(fans[0]).split()[1])
        output.append(truck)
        if truck <= 0 and args.report:
            slack_status = slack_post(args.organization, bot,"Truck")

        #get payload fan speed
        output.append("Payload:")
        con = RemoteClientConnection(bot, args.ssh_key, args.env, port = 3222)
        sleep(.5)
        con.connect()
        fans = con.exec_command("sudo modprobe it87; insight-payload.bash -c 'sensors | grep -i fan'")
        payload = int(decode_output(fans[1]).split()[1])
        output.append(payload) #we only care about the second fan here. The first was removed to make room for the hd
        if payload <= 0 and args.report:
            slack_status = slack_post(args.organization, bot,"Payload")
        return output

    except SSHException as e:
        print("Failed: {}".format(e))
        output.append("SSH Exception")
        return output

    except socket.timeout as e:
        print("Timeout error: {}".format(e))
        output.append("Socket Timeout")
        return output

    except IndexError as e:
        print("Heartbeat Error: {}".format(e))
        output.append("Heartbeat Error")
        return output

    except Exception as e:
        print("Other exception: {}".format(e))
        return output

    finally:
        if connectionEstablished:
            if vpn_state == "down":
                con.close()


if __name__ == '__main__':
    parser = ArgumentParser(description='Script to check fans on a list of bots')
    parser.add_argument('organization', help='The organization we are checking the fans of',choices={'Woolworths', 'Woodmans'})
    parser.add_argument('bot_list', help='File containing list of bots (BARXXX\n format)')
    parser.add_argument('--ssh_key', default=expanduser("~/.ssh/barkey"), help='SSH key file EX: /home/jsbach/.ssh/barkey')
    parser.add_argument('--env', default="PRODUCTION", help='Current Env of bot')
    parser.add_argument('-r', '--report', help='automatically report to apprepriate slack channel if truck fan speed is 0', action='store_true')
    args = parser.parse_args()

#    botRequest = requests.get(FLEETURL+'robots', auth=(FLEETUSR, FLEETPASS))
#    botsJson = botRequest.json()
#    BOTS = {}
#    for bot in botsJson:
#        BOTS[bot['name']] = bot
#
#    storeRequest = requests.get(FLEETURL+'stores', auth=(FLEETUSR, FLEETPASS))
#    storesJson = storeRequest.json()
#    STORES = {}
#    for store in storesJson:

    bot_list = []
    with open(args.bot_list, 'r') as file:
        for line in file:
            bot_list.append(line.strip())


    #print(log_pe_issue("BAR813", "SUMMARY GOES HERE", "This is a description"))
    results = []
    print(datetime.datetime.now())
    for bot in bot_list:
        result = run_script(bot, args)
        pprint(result)
