#!/usr/bin/env python3

from argparse import ArgumentParser
from multiprocessing import Process, Queue, freeze_support
from os.path import expanduser
from pe_tools.pkgs.remote_client_connection import RemoteClientConnection
from paramiko.ssh_exception import SSHException
from time import sleep
from pprint import pprint
import datetime

#convert from bytes for more readable output
def decode_output(lst):
    nu = []
    for line in lst:
        nu.append(line.decode('utf-8'))
    return nu

#helps to format output
def get_file_name_from_path(file):
    if len(file.split("/")) > 1:
        return file.split("/")[-1]
    return file


def commands(con, args):
    output = []
    if args.params != None:
        output.append("-- Params BAFORE salt changes applied --")
        for param in args.params:
            output.append("{}: {}".format(param, decode_output(con.exec_command("bar-base.bash -c \"rosparam get -p {}\"".format(param)))))
    output.append("-- Transferring {} to /home/bar/pe/ --".format(get_file_name_from_path(args.file_to_upload)))
    con.transfer_file_upload(args.file_to_upload,"/home/bar/pe/")
    output.append("-- Moving {} to {} --".format(get_file_name_from_path(args.file_to_upload), args.destination))
    con.exec_command("sudo cp /home/bar/pe/{} {}".format(get_file_name_from_path(args.file_to_upload), args.destination))
    #handle any file removing here
    #con.exec_command("sudo rm /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/01-caution-wav.sls /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/aaa-caution-wav.sls")
    output.append("-- {} contents after file transfer: --".format(args.destination))
    output.append(decode_output(con.exec_command("ls -al {}".format(args.destination))))
    if args.dont_apply_changes:
        output.append("-- Applying salt changes --")
        output.append(decode_output(con.exec_command("sudo bar-base.salt '*' state.apply")))
        if args.params != None:
            output.append("-- Params AFTER salt changes applied --")
            for param in args.params:
                output.append("{}: {}".format(param, decode_output(con.exec_command("bar-base.bash -c \"rosparam get -p {}\"".format(param)))))
    output.append("-- Done --")
    return output

def run_script(hostname, args):
    try:
        con = RemoteClientConnection(hostname, args.ssh_key, args.env)
        sleep(.5)
        con.connect()
        output = commands(con, args)
        return output

    except SSHException as e:
        print("Failed: {}".format(e))
        return

    finally:
        print("")
        con.close()


if __name__ == '__main__':
    parser = ArgumentParser(description='Script to add an override file to a list of bots, apply salt changes, and optionally check rosparams before and after')
    parser.add_argument('bot_list', help='File containing list of bots (BARXXX\n format)')
    parser.add_argument('file_to_upload', help='Override file to upload to bot')
    parser.add_argument("-d", "--destination", default="/var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/", help='directory where you want the override to end up')
    parser.add_argument("-p", "--params", nargs='+', help="rosparameter to check before and after applying salt changes")
    parser.add_argument("--dont_apply_changes", help="if you want to add an override but not apply salt changes", action="store_false")
    parser.add_argument('--ssh_key', default=expanduser("~/.ssh/barkey"), help='SSH key file EX: /home/jsbach/.ssh/barkey')
    parser.add_argument('--env', default="PRODUCTION", help='Current Env of bot')
    args = parser.parse_args()
    bot_list = []


    with open(args.bot_list, 'r') as file:
        for line in file:
            bot_list.append(line.strip())

    print(datetime.datetime.now())
    results = []
    for bot in bot_list:
        print(bot)
        for line in run_script(bot, args):
            pprint(line)
        print("")
