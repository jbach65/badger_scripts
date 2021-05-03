import os
import sys
import subprocess
import time
import argparse
from pprint import pprint


class OpenRVIZAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        botIP = getStoreNetwork(namespace.hosts,values[0])
        if botIP == "":
            print("ERROR: Could not get bot IP. Make sure bot has VPN open")
            return
        IPList = getAddresses()
        hostname = findIPToExport(IPList, botIP)
        if hostname == "":
            print("ERROR: Could not generate hostname to export. Make sure you are connected to the correct VPN")
            return
        hostnameLine = "export ROS_HOSTNAME=" + hostname
        print(hostnameLine)
        ROSMasterURILine = "export ROS_MASTER_URI=http://" + botIP + ":11311"
        print(ROSMasterURILine)
        RVIZRunLine = "rviz -d " + namespace.folder + namespace.config[0]
        print(RVIZRunLine)
        os.system(hostnameLine + "; " + ROSMasterURILine + ";" + RVIZRunLine)

class ListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        print("RVIZ folder path: " + namespace.folder + " contains these config files:")
        for file in os.listdir(namespace.folder):
            if len(file.split(".")) >= 2:
                if file.split(".")[1] == "rviz":
                    print(file)

def getStoreNetwork(hosts, bot):
    with open(hosts, "r") as f:
        lines = f.readlines()
        for line in lines:
            splitLine = line.split()
            if len(splitLine) > 2:
                if splitLine[1] == "bar"+str(bot):
                    return splitLine[0]
    return ""

def getAddresses():
    sub = subprocess.Popen("ifconfig", shell=True, stdout=subprocess.PIPE)
    subprocess_return = sub.stdout.read()
    output_list = str(subprocess_return).split()
    indices = [i+1 for i, x in enumerate(output_list) if x == "inet"]
    addresses = [output_list[i] for i in indices]
    return addresses

def findIPToExport(addressList, botAddress):
    for address in addressList:
        if(botAddress.split(".")[:-1] == address.split(".")[:-1]):
            return address
    return ""

parser = argparse.ArgumentParser(description='A script for all your PE RVIZ needs')
parser.add_argument('--hosts', default='/etc/hosts', help='hosts file path')
parser.add_argument('--folder', default='/home/jsbach/Documents/RVIZ_configs/', help='RVIZ config file folder path')
parser.add_argument('-c', '--config', nargs=1, help='RVIZ config file you want to use', default = 'default.rviz')
parser.add_argument('-o', '--open', nargs=1, type=int, help='bot # you want to open RVIZ on', action=OpenRVIZAction)
parser.add_argument('-l', '--list', nargs=0 , help='list all .rviz files in config folder', action=ListAction)
args = parser.parse_args()
