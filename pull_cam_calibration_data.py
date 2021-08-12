#!/usr/bin/env python3

import requests
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
import tqdm
import os
from pathlib import Path


CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
FLEETURL = 'https://fleet.badger-technologies.com/api/web/v1/'
FLEETUSR = 'josh_steinbach@jabil.com'
FLEETPASS = '#JSBach4171997'

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

def create_folder(args, bot):
    Path("{}{}/".format(args.output,bot)).mkdir(parents=True, exist_ok=True)

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


def pull_files(args, bot):
    try:
        con = RemoteClientConnection(bot, args.ssh_key, args.env, port = 2222)
        sleep(.5)
        con.connect()
        con.download_file("/var/snap/bar-base/current/config/depthcams/depthcam_proximity_back_pos.yaml", "{}{}/depthcam_proximity_back_pos.yaml".format(args.output,bot))
        spoiler_calibration_check = con.exec_command("ls /var/snap/bar-base/common/calibration/depthcams/body-image_*.pgm")
        if len(spoiler_calibration_check) > 0:
            for weird_format_file in spoiler_calibration_check:
                file = decode_output(weird_format_file)
                file_name = file.split('/')[-1]
                con.download_file(file, "{}{}/{}".format(args.output,bot,file_name))
        else:
            print("file not found")
        return

    except SSHException as e:
        print("Failed: {}".format(e))
        return

    except socket.timeout as e:
        print("Timeout error: {}".format(e))
        return

    except IndexError as e:
        print("Heartbeat Error: {}".format(e))
        return

    finally:
        con.close()
        #print("")


if __name__ == '__main__':
    parser = ArgumentParser(description='Script to pull these files: /var/snap/bar-base/current/config/depthcams/depthcam_proximity_back_pos.yaml and /var/snap/bar-base/common/calibration/depthcams/body_image_*.pgm')
    parser.add_argument('bot_list', help='File containing list of bots (BARXXX\n format)')
    parser.add_argument('-o', '--output', default="{}/output/".format(CURRENT_DIRECTORY), help='Output directory to store files')
    parser.add_argument('--ssh_key', default=expanduser("~/.ssh/barkey"), help='SSH key file EX: /home/jsbach/.ssh/barkey')
    parser.add_argument('--env', default="PRODUCTION", help='Current env of bot')
    args = parser.parse_args()
    if args.output[-1] != '/':
        args.output = args.output + '/'
    print(args.output)

    #generate list of bots
    bot_list = []
    with open(args.bot_list, 'r') as file:
        for line in file:
            bot_list.append(line.strip())


    print(datetime.datetime.now())
    for bot in bot_list:
        print(bot)
        create_folder(args, bot)
        pull_files(args, bot)
        sleep(10)
