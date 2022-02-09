# TODO: format output
# TODO: add log files

#!/usr/bin/env python3

from argparse import ArgumentParser, FileType
from multiprocessing import Process, Queue, freeze_support
from os.path import expanduser
from pe_tools.pkgs.remote_client_connection import RemoteClientConnection
from paramiko.ssh_exception import SSHException
from time import sleep
from pprint import pprint
import datetime
import socket
from socket import AF_INET, SOCK_DGRAM
import os

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

def add_files(con, args):
    output = []
    for file in args.add:
        output.append("-- Transferring {} to /home/bar/pe/ --".format(get_file_name_from_path(file)))
        con.transfer_file_upload(file,"/home/bar/pe/")
        output.append("-- Moving {} to {} --".format(get_file_name_from_path(file), map_folder(args.Folder)))
        con.exec_command("sudo cp /home/bar/pe/{} {}".format(get_file_name_from_path(file), map_folder(args.Folder)))
    return output

def disable_files(con, args):
    output = []
    for file in args.disable:
        output.append("-- Checking for {} in /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/ --".format(get_file_name_from_path(file)))
        if check_folder(con, file, "/var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/"):
            output.append("-- Disabling {} --".format(get_file_name_from_path(file)))
            con.exec_command("sudo mv /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/{} /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/{}.DISABLED".format(get_file_name_from_path(file), get_file_name_from_path(file)))
        else:
            output.append("-- {} NOT FOUND in /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/ --".format(get_file_name_from_path(file)))
            output.append("-- Checking for {} in /var/snap/bar-base/current/config/salt-master/srv/pillar/overrides/ --".format(get_file_name_from_path(file)))
            if check_folder(con, file, "/var/snap/bar-base/current/config/salt-master/srv/pillar/overrides/"):
                output.append("-- Disabling {} --".format(get_file_name_from_path(file)))
                con.exec_command("sudo mv /var/snap/bar-base/current/config/salt-master/srv/pillar/overrides/{} /var/snap/bar-base/current/config/salt-master/srv/pillar/overrides/{}.DISABLED".format(get_file_name_from_path(file), get_file_name_from_path(file)))
            else:
                output.append("-- {} NOT FOUND in /var/snap/bar-base/current/config/salt-master/srv/pillar/overrides/ --".format(get_file_name_from_path(file)))

        output.append("-- Locating {} --".format(get_file_name_from_path(file)))
        if check_folder(con, file, "/var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/"):
            output.append("-- {} found in /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/ --".format(get_file_name_from_path(file)))
            output.append("-- Disabling {} --".format(get_file_name_from_path(file)))
            con.exec_command("sudo mv /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/{} /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/{}.DISABLED".format(get_file_name_from_path(file), get_file_name_from_path(file)))
            output.append("-- File has been Disabled --".format(get_file_name_from_path(file)))
        elif check_folder(con, file, "/var/snap/bar-base/current/config/salt-master/srv/pillar/overrides/"):
            output.append("-- {} found in /var/snap/bar-base/current/config/salt-master/srv/pillar/overrides/ --".format(get_file_name_from_path(file)))
            output.append("-- Disabling {} --".format(get_file_name_from_path(file)))
            con.exec_command("sudo mv /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/{} /var/snap/bar-base/current/config/salt-master/srv/pillar/overrides/{}.DISABLED".format(get_file_name_from_path(file), get_file_name_from_path(file)))
            output.append("-- File has been Disabled --".format(get_file_name_from_path(file)))
        elif check_folder(con, file, "/var/snap/bar-base/current/config/salt-master/srv/pillar/pe-overrides/"):
            output.append("-- {} found in /var/snap/bar-base/current/config/salt-master/srv/pillar/pe-overrides/ --".format(get_file_name_from_path(file)))
            output.append("-- Disabling {} --".format(get_file_name_from_path(file)))
            con.exec_command("sudo mv /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/{} /var/snap/bar-base/current/config/salt-master/srv/pillar/pe-overrides/{}.DISABLED".format(get_file_name_from_path(file), get_file_name_from_path(file)))
            output.append("-- File has been Disabled --".format(get_file_name_from_path(file)))
        else:
            output.append("-- {} not found in any of the override directories --".format(get_file_name_from_path(file)))
    return output


def remove_files(con, args):
    output = []
    for file in args.remove:
        output.append("-- Locating {} --".format(get_file_name_from_path(file)))
        if check_folder(con, file, "/var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/"):
            output.append("-- {} found in /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/ --".format(get_file_name_from_path(file)))
            output.append("-- Removing {} --".format(get_file_name_from_path(file)))
            con.exec_command("sudo rm /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/{}".format(get_file_name_from_path(file)))
            output.append("-- File Removed --".format(get_file_name_from_path(file)))
        elif check_folder(con, file, "/var/snap/bar-base/current/config/salt-master/srv/pillar/overrides/"):
            output.append("-- {} found in /var/snap/bar-base/current/config/salt-master/srv/pillar/overrides/ --".format(get_file_name_from_path(file)))
            output.append("-- Removing {} --".format(get_file_name_from_path(file)))
            con.exec_command("sudo rm /var/snap/bar-base/current/config/salt-master/srv/pillar/overrides/{}".format(get_file_name_from_path(file)))
            output.append("-- File Removed --".format(get_file_name_from_path(file)))
        elif check_folder(con, file, "/var/snap/bar-base/current/config/salt-master/srv/pillar/pe-overrides/"):
            output.append("-- {} found in /var/snap/bar-base/current/config/salt-master/srv/pillar/pe-overrides/ --".format(get_file_name_from_path(file)))
            output.append("-- Removing {} --".format(get_file_name_from_path(file)))
            con.exec_command("sudo rm /var/snap/bar-base/current/config/salt-master/srv/pillar/pe-overrides/{}".format(get_file_name_from_path(file)))
            output.append("-- File Removed --".format(get_file_name_from_path(file)))
        else:
            output.append("-- {} not found in any of the override directories --".format(get_file_name_from_path(file)))

    return output

def map_folder(folder):
    if folder == "fleet":
        return "/var/snap/bar-base/current/config/salt-master/srv/pillar/fleet/"
    elif folder == "overrides":
        return "/var/snap/bar-base/current/config/salt-master/srv/pillar/overrides/"
    elif folder == "pe-overrides":
        return "/var/snap/bar-base/current/config/salt-master/srv/pillar/pe-overrides/"
    else:
        return ""

#checks a directory for the presence of a file
def check_folder(con, file, folder):
    fleet_check = con.exec_command("ls {}{}".format(folder, file))
    if len(fleet_check) == 1:
        return True
    else:
        return False

def commands(con, args):
    output = []
    if args.show:
        output.append("-- fleet directory contents: --")
        output.append(decode_output(con.exec_command("ls -l /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet")))
        output.append("-- overrides directory contents: --")
        output.append(decode_output(con.exec_command("ls -l /var/snap/bar-base/current/config/salt-master/srv/pillar/overrides")))
        output.append("-- pe-overrides directory contents: --")
        output.append(decode_output(con.exec_command("ls -l /var/snap/bar-base/current/config/salt-master/srv/pillar/pe-overrides")))

    if args.params != None:
        output.append("-- Params BEFORE salt changes applied --")
        for param in args.params:
            output.append("{}: {}".format(param, decode_output(con.exec_command("bar-base.bash -c \"rosparam get -p {}\"".format(param)))))

    if args.remove != None:
        remove_output = remove_files(con,args)
        for line in remove_output:
            output.append(line)

    if args.disable != None:
        disable_output = disable_files(con,args)
        for line in disable_output:
            output.append(line)

    if args.add != None:
        add_output = add_files(con,args)
        for line in add_output:
            output.append(line)

    if args.add != None or args.remove != None or args.disable != None:
        output.append("-- fleet directory contents after changes: --")
        output.append(decode_output(con.exec_command("ls -l /var/snap/bar-base/current/config/salt-master/srv/pillar/fleet")))
        output.append("-- overrides directory contents after salt update: --")
        output.append(decode_output(con.exec_command("ls -l /var/snap/bar-base/current/config/salt-master/srv/pillar/overrides")))
        output.append("-- pe-overrides directory contents: --")
        output.append(decode_output(con.exec_command("ls -l /var/snap/bar-base/current/config/salt-master/srv/pillar/pe-overrides")))
        output.append("-- Applying salt --")
        output.append(decode_output(con.exec_command("sudo bar-base.salt '*' state.apply")))
        if args.params != None:
            output.append("-- Params AFTER salt changes applied --")
            for param in args.params:
                output.append("{}: {}".format(param, decode_output(con.exec_command("bar-base.bash -c \"rosparam get -p {}\"".format(param)))))
    output.append("-- Done --")
    return output

def run_script(hostname, args):
    try:
        output = []
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
        #make connection
        con.connect()
        output = commands(con, args)
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
                print("Closing VPN")
                con.close()
            else:
                print("Leaving VPN open")



if __name__ == '__main__':
    parser = ArgumentParser(description='Script to add an override file to a list of bots, apply salt changes, and optionally check rosparams before and after')
    list_options = parser.add_mutually_exclusive_group()
    list_options.add_argument('-l', '--list',
                        nargs="*",
                        help="list of robots to update. Format: BARXXX BARYYY BARZZZ")
    list_options.add_argument('-f', '--fileList',
                        type=FileType('r'),
                        help="File containing the list of robots to update")
    parser.add_argument('-s', '--show', help='show contents of fleet, overrides, and pe_overrides directories', action='store_true')
    parser.add_argument("-a", "--add", nargs='+', help="salt override(s) to add")
    parser.add_argument("-d", "--disable", nargs='+', help="salt override(s) to disable")
    parser.add_argument("-r", "--remove", nargs='+', help="salt override(s) to remove")
    parser.add_argument("-p", "--params", nargs='+', help="rosparam(s) to check before and after applying salt changes")
    parser.add_argument("-F", "--Folder", choices={'fleet', 'overrides', 'pe-overrides'}, default="fleet", help='directory where you want the override to live')
    parser.add_argument("--dont_apply_changes", help="if you want to add an override but not apply salt changes", action="store_false")
    parser.add_argument('--ssh_key', default=expanduser("~/.ssh/barkey"), help='SSH key file EX: /home/jsbach/.ssh/barkey')
    parser.add_argument('--env', default="PRODUCTION", help='Current Env of bot')
    args = parser.parse_args()
    bot_list = []

    if args.list:
        for bot in args.list:
            bot_list.append(bot)
    else:
        for line in args.fileList:
            bot_list.append(line.strip())

    for bot in bot_list:
        print(bot)
        for line in run_script(bot, args):
            pprint(line)
        print("")
