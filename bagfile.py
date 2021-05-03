from datetime import datetime
from pytz import timezone
from os.path import expanduser
import argparse
from pe_tools.pkgs.remote_client_connection import RemoteClientConnection


def change_timezone_of_datetime_object(date_time_object, new_timezone_name):
    """Return the *date_time_object* with it's timezone changed to *new_timezone_name*

    :param date_time_object: The datetime object whose timezone is to be changed
    :type date_time_object: datetime
    :param new_timezone_name: The name of the timezone to which the *date_time_object* is to be changed to
    :type new_timezone_name: str
    :rtype: datetime
    """
    # Create a pytz.timezone object for the new_timezone
    new_timezone_object = timezone(new_timezone_name)
    # Update the timezone of the datetime object
    date_time_object = date_time_object.astimezone(new_timezone_object)
    # Return the converted datetime object
    return date_time_object

parser = argparse.ArgumentParser(description='A script to set aside bagfiles')
parser.add_argument('--env', default='PRODUCTION', help='fleet environment')
parser.add_argument('-k', '--barkey', default='~/.ssh/barkey', help='location of barkey')
parser.add_argument('--DEBUG', help='output debug statements', action='store_true')
parser.add_argument('--dont_close', help='leaves VPN open on bot', action='store_false')
parser.add_argument('bot' , help='robot files are to be pulled from (BARXXX format)')
parser.add_argument('start', help='stsrt time in this datetime format \"%%Y-%%m-%%dT%%H:%%M:%%S.%%f%%z\" (ex. \"2021-04-01T14:21:00.000-0400\")')
parser.add_argument('end', help='end time in this datetime format \"%%Y-%%m-%%dT%%H:%%M:%%S.%%f%%z\" (ex. \"2021-04-01T14:48:00.000-0400\")')
parser.add_argument('ticket' , help='FIT ticket number (used for the directory name that the files will be set aside in)')

args = parser.parse_args()

#set varibale from pre-argparse script
bot = args.bot
start = args.start
end = args.end
ticket = args.ticket
barkey = expanduser(args.barkey)
env = args.env
DEBUG = args.DEBUG
close_vpn = args.dont_close

#convert strings to datetime objects
startDT = datetime.strptime(start,'%Y-%m-%dT%H:%M:%S.%f%z')
endDT = datetime.strptime(end,'%Y-%m-%dT%H:%M:%S.%f%z')

#open connection to bot
if DEBUG: print("Connecting to {}".format(bot))
con = RemoteClientConnection(bot, barkey, env)
if DEBUG: print("Opening VPN...")
con.connect()
# run initial command to get contents of
if DEBUG: print("Grabbing list of bagfiles in /var/snap/bar-base/common/bagfiles/low_res_recorder/ready_for_upload/")
output = con.exec_command("ls /var/snap/bar-base/common/bagfiles/low_res_recorder/ready_for_upload/")

#get timezone info
botTimezoneReadable = con.exec_command("cat /etc/timezone")[0].decode("utf-8")
botTimezoneAbbr = con.exec_command("date +\"%z\"")[0].decode("utf-8")


oldStart = startDT
oldEnd = endDT
if DEBUG: print("Converting timezones")
startDT = change_timezone_of_datetime_object(startDT, botTimezoneReadable)
endDT = change_timezone_of_datetime_object(endDT, botTimezoneReadable)
if DEBUG: print("\t{}->{}".format(oldStart,startDT))
if DEBUG: print("\t{}->{}".format(oldEnd,endDT))

#list of the entire direcotry contents (will be in alphabetical order which is also increasing date order)
directoryOutput = []
for line in output:
    #convert bytes to strings
    directoryOutput.append(line.decode("utf-8"))


#list of only the movement bagfiles
movementBagfiles = []
for line in directoryOutput:
    if len(line.strip().split('_')) >= 4:
        type = line.strip().split('_')[len(line.strip().split('_'))-1]
        if type.split('.')[0] == "movement":
            movementBagfiles.append(line)

#list of files that need to be pulled
filesToPull = []
if DEBUG: print("Analyzing and generating list of files to set aside")
## TODO: make these 2 asserts and handle the errors
if startDT > endDT:
    print("start time can not be after end time")
elif change_timezone_of_datetime_object(datetime.strptime(movementBagfiles[0].strip().split('_')[1]+botTimezoneAbbr,'%Y-%m-%d-%H-%M-%S%z'), botTimezoneReadable) > startDT:
    print("Bagfile too old. Not on bot anymore. (check date accuracy)")
else:
    filesToPull.append(movementBagfiles[0])
    for line in movementBagfiles:
        date = line.strip().split('_')[1]
        dt = change_timezone_of_datetime_object(datetime.strptime(date+botTimezoneAbbr,'%Y-%m-%d-%H-%M-%S%z'), botTimezoneReadable)
        if dt < startDT:
            filesToPull.pop()
            filesToPull.append(line)
        elif dt > startDT and dt < endDT:
            filesToPull.append(line)

#create folders for bagfiles
if DEBUG: print("Creating /home/bar/pe if it does not exist")
con.exec_command("mkdir -p /home/bar/pe")
if DEBUG: print("Creating /home/bar/pe/{}  if it does not exist".format(ticket))
con.exec_command("mkdir -p /home/bar/pe/{}".format(ticket))

#generate copy command
copyCommand = "sudo cp "
print("List of files to be pulled:")
for line in filesToPull:
    print("\t{}".format(line))
    copyCommand += "/var/snap/bar-base/common/bagfiles/low_res_recorder/ready_for_upload/{} ".format(line.strip())
if DEBUG: print("Generating copy command")
copyCommand += "/home/bar/pe/{}".format(ticket)

#execute copy command
if DEBUG: print("Executing comand: {}".format(copyCommand))
con.exec_command(copyCommand)

#remember to close the vpn when done
if close_vpn:
    if DEBUG: print("Closing VPN")
    con.close()
else:
    if DEBUG: print("Leaving VPN open")
