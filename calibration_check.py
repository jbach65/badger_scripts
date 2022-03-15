#!/usr/bin/env python3
import cv2 as cv
import numpy as np
from argparse import ArgumentParser, FileType
from os.path import expanduser
from pe_tools.pkgs.remote_client_connection import RemoteClientConnection
from paramiko.ssh_exception import SSHException
from time import sleep
from pprint import pprint
from socket import timeout
import subprocess

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

#handle trailing slash
def remove_slash(path):
    if len(path) > 0:
        if path[-1] == '/':
            return path[:-1]
        else:
            return path
    else:
        return ""

#gets stereoS cams and IR depthcams
def get_pgm_list(con, args):
    return con.exec_command("ls /var/snap/bar-base/current/config/depthcams/*.pgm")

def commands(hostname, con, args):
    pgms = decode_output(get_pgm_list(con, args))
    for pgm in pgms:
        new_name = hostname + "_" + pgm.split("/")[-1]
        print("Downloading: {}".format(new_name))
        destination_path = args.directory + "/" + new_name
        con.download_file(pgm, destination_path)

        #normalize image so it is easier to identify
        img = cv.imread(destination_path)
        norm_img = np.zeros((800,800))
        final_img = cv.normalize(img,  norm_img, 0, 255, cv.NORM_MINMAX)

        #write file to destnation specified in args
        norm_file = args.normalized + "/" + new_name + ".jpg"
        cv.imwrite(norm_file, final_img)

def run_script(bot, args):
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
        commands(bot, con, args)
        return output

    except SSHException as e:
        print("Failed: {}".format(e))
        output.append("SSH Exception")
        return output

    except timeout as e:
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
    parser.add_argument("-d", "--directory", default=expanduser("~/calibration_files/"), help='directory you want the pgms to be pulled to')
    parser.add_argument("-n", "--normalized", default=expanduser("~/calibration_files/normalized/"), help='directory where you want the nomalized jpgs to be placed')
    parser.add_argument('--ssh_key', default=expanduser("~/.ssh/barkey"), help='SSH key file EX: ~/.ssh/barkey')
    parser.add_argument('--env', default="PRODUCTION", help='Current Env of bot')
    args = parser.parse_args()

    #generate list of bots based on input method
    bot_list = []
    if args.list:
        for bot in args.list:
            bot_list.append(bot)
    else:
        for line in args.fileList:
            bot_list.append(line.strip())

    #handle '~/' notation and trailing slashes
    args.directory = expanduser(remove_slash(args.directory))
    args.normalized = expanduser(remove_slash(args.normalized))

    #make necessary directories (if they don't already exist)
    subprocess.Popen(['mkdir', '-p', args.directory], stdout=subprocess.PIPE,  stderr=subprocess.STDOUT)
    subprocess.Popen(['mkdir', '-p', args.normalized], stdout=subprocess.PIPE,  stderr=subprocess.STDOUT)

    print(args.directory)
    print(args.normalized)

    #grab all of the calibration files already present to make sure we dont get duplicates (aids in stopping and re-starting long lists right where you left off)
    result = subprocess.Popen(['ls', args.directory], stdout=subprocess.PIPE,  stderr=subprocess.STDOUT)
    stdout,stderr = result.communicate()
    contents = stdout.decode('utf-8')

    for bot in bot_list:
        print(bot)
        #check presence of calibration files in specified directory
        if (bot + "_") not in contents:
            run_script(bot, args)
        else:
            print("Calibration files already present in {}".format(args.directory))
        print("")
