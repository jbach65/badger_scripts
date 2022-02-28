# TODO: figure out why I need sys.path.append

import sys
import time
import argparse
from pprint import pprint

sys.path.append('/home/jsbach/Documents')
from badger_pylibs.api_controllers.api_controllers.fleet_api_controller import FleetApiController


class OpenAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        open_things(namespace, values)

class CloseAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        close_things(namespace, values)

class RemoveAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        remove_things(namespace, values)

class VerifyAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        for bot in get_hosts_bot_list(namespace.hosts):
            fleetObj = FleetApiController(bot, namespace.env)
            if vpn_check(fleetObj):
                message = "OPEN"
                sys.stderr.write(bot.strip() + ": " + '\x1b[1;32m' + message.strip() + '\x1b[0m' + "\n")
            else:
                message = "CLOSED"
                sys.stderr.write(bot.strip() + ": " + '\x1b[1;31m' + message.strip() + '\x1b[0m' + "\n")

class ListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        for bot in get_hosts_bot_list(namespace.hosts):
            print(bot)

class TidyAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        for bot in get_hosts_bot_list(namespace.hosts):
            fleetObj = FleetApiController(bot, namespace.env)
            if not vpn_check(fleetObj):
                if remove_from_hosts(namespace.hosts,bot):
                    print("BAR" + str(bot[3:]) + " removed from " + namespace.hosts)
                else:
                    print("ERROR: BAR" + str(bot[3:]) + " not found in " + namespace.hosts)


def open_things(args, vpn_list):
    for vpn in vpn_list:
        fleetObj = FleetApiController("bar"+str(vpn), args.env)
        print("Opening vpn on BAR{}".format(vpn))
        if vpn_check(fleetObj):
            print('VPN open')
            print("Getting IP from Fleet command history")
            command_line = get_vpn_opened_line(fleetObj)
            IP = ""
            if command_line != "":
                IP = parse_vpn_line(str(command_line['result']))
            if IP != "":
                print("IP: " + IP)
                print("Generating hosts file string...")
                hostsLine = generate_hostfile_string(IP,'bar'+str(vpn),fleetObj.robot_serial)
                print("Writing this line hosts file: " + hostsLine)
                write_to_hosts(args.hosts,hostsLine)
            else:
                print("Open VPN command not found in bar"+ vpn + "\'s command history\nSending OpenVPN command")
                fleetObj.open_vpn()
                print("Waiting on IP...")
                fleet_result = wait_for_IP(fleetObj)
                IP = parse_vpn_line(str(fleet_result))
                if IP == "":
                    print("ERROR: Unable to reserve VPN connection")
                else:
                    print("IP: " + IP)
                    print("Generating hosts file string...")
                    hostsLine = generate_hostfile_string(IP,'bar'+str(vpn),fleetObj.robot_serial)
                    print("Writing this line hosts file: " + hostsLine)
                    write_to_hosts(args.hosts,hostsLine)

        else:
            print('VPN closed')
            print("Sending Open VPN command to fleet")
            fleetObj.open_vpn()
            print("Waiting on IP...")
            fleet_result = wait_for_IP(fleetObj)
            IP = parse_vpn_line(str(fleet_result))
            if IP == "":
                print("ERROR: Unable to reserve VPN connection")
            else:
                print("IP: " + IP)
                print("Generating hosts file string...")
                hostsLine = generate_hostfile_string(IP,'bar'+str(vpn),fleetObj.robot_serial)
                print("Writing this line hosts file: " + hostsLine)
                write_to_hosts(args.hosts,hostsLine)

def close_things(args, vpn_list):
    for vpn in vpn_list:
        fleetObj = FleetApiController("bar"+str(vpn), args.env)
        print("Closing vpn on bar%r" % (vpn))
        print("Sending Close VPN command to fleet")
        fleetObj.close_vpn()
        print("Removing line from hosts file")
        if remove_from_hosts(args.hosts,'bar'+str(vpn)):
            print("BAR" + str(vpn) + " removed from " + args.hosts)
        else:
            print("ERROR: BAR" + str(vpn) + " not found in " + args.hosts)

def remove_things(args, vpn_list):
    for vpn in vpn_list:
        print("Removing line from hosts file")
        if remove_from_hosts(args.hosts,'bar'+str(vpn)):
            print("BAR" + str(vpn) + " removed from " + args.hosts)
        else:
            print("ERROR: BAR" + str(vpn) + " not found in " + args.hosts)

def vpn_check(fleet):
    latest_heartbeat = fleet.get_latest_heartbeat().json()
    if len(latest_heartbeat) != 1:
        #print("Hearbeat data not foud (Assuming vpn is not open)")
        return False
    if str(fleet.get_latest_heartbeat().json()[0]['data']['vpn']['state']) == 'activated':
        #print('VPN currently open')
        return True
    else:
        #print('VPN not currently open')
        return False

def get_vpn_opened_line(fleet):
    cmd_list = fleet.get_command_history(1).json()
    cmd_list_sorted = sorted(cmd_list, key=lambda k: k['created_at'], reverse=True)
    for cmd in cmd_list_sorted:
        if cmd['command_type'] == "open_vpn":
            return cmd
    return ""

def parse_vpn_line(vpn_line):
    split = vpn_line.split(" ")
    if split[-1].split(".")[0] == "172":
        return split[-1]
    else:
        return ""

def generate_hostfile_string(ip, robot, serial):
    return str(ip) + '\t' + str(robot) + '\tbar' + str(serial)

def write_to_hosts(hostsFilePath, newLine):
    bot = newLine.split()[1]
    with open(hostsFilePath, "r") as f:
        lines = f.readlines()
        for line in lines:
            splitLine = line.split()
            if len(splitLine) > 2:
                if splitLine[1] == bot:
                    lines.remove(line)
        lines.append(newLine + "\n")
    with open("/etc/hosts", "w") as f:
        f.writelines(lines)

def remove_from_hosts(hostsFilePath, bot):
    found = False
    with open(hostsFilePath, "r") as f:
        lines = f.readlines()
        for line in lines:
            splitLine = line.split()
            if len(splitLine) > 2:
                if splitLine[1] == bot:
                    lines.remove(line)
                    found = True
    with open("/etc/hosts", "w") as f:
        f.writelines(lines)
    return found

def wait_for_IP(fleet):
    cmd_list = fleet.get_command_history(1).json()
    cmd_list_sorted = sorted(cmd_list, key=lambda k: k['created_at'], reverse=True)
    checks = 0
    while checks <= 180:
        cmd_index = 0
        while cmd_list_sorted[cmd_index]['command_type'] != "open_vpn":
            cmd_index+=1
        if cmd_list_sorted[cmd_index]['result'] is not None:
            return cmd_list_sorted[cmd_index]['result']
        checks+=1
        time.sleep(2)
        cmd_list = fleet.get_command_history(1).json()
        cmd_list_sorted = sorted(cmd_list, key=lambda k: k['created_at'], reverse=True)

def get_hosts_bot_list(hostsFilePath):
    bot_list = []
    with open(hostsFilePath, "r") as f:
        lines = f.readlines()
        for line in lines:
            splitLine = line.split()
            if len(splitLine) == 3:
                if len(splitLine[1]) > 3:
                    if splitLine[1][:3] == "bar":
                        bot_list.append(splitLine[1])
    return bot_list


parser = argparse.ArgumentParser(description='A script for all your PE VPN needs')
parser.add_argument('--env', default='PRODUCTION', help='fleet environment')
parser.add_argument('--hosts', default='/etc/hosts')
parser.add_argument('-o', '--open', nargs='+', type=int, help='bot # you want to open VPN on (if multiple, separate with spaces)', action=OpenAction)
parser.add_argument('-c', '--close', nargs='+', type=int, help='bot # you want to close VPN on (if multiple, separate with spaces)', action=CloseAction)
parser.add_argument('-r', '--remove', nargs='+', type=int, help='bot # you want to remove from hosts file (if multiple, separate with spaces)', action=RemoveAction)
parser.add_argument('-l', '--list', nargs=0 , help='list all VPN connections in hosts file', action=ListAction)
parser.add_argument('-v', '--verify', nargs=0 , help='verify all VPN connections in hosts file', action=VerifyAction)
parser.add_argument('-t', '--tidy', nargs=0 , help='tidy up all VPN connections in hosts file by clearing out all closed connections', action=TidyAction)
args = parser.parse_args()
