import requests
import datetime
import json
from pprint import pprint
import xlwt
from xlwt import Workbook

# Workbook is created
wb = Workbook()

# add_sheet is used to create sheet.
sheet1 = wb.add_sheet('Sheet 1')

FLEETURL = 'https://fleet.badger-technologies.com/api/web/v1/'
FLEETUSR = 'josh_steinbach@jabil.com'
FLEETPASS = '#JSBach4171997'

dtNow = datetime.datetime.now()
startDelta = datetime.timedelta(days=1)
incrementDelta = datetime.timedelta(minutes=30)

row = 1

print(dtNow)
dt = dtNow - startDelta
while dt <= dtNow:
    ## TODO: check for duplicates (will happen if bot does not have heartbeats for a period of time)
    hb = requests.get('{}robots/{}/heartbeats?created_before=%{}%&limit=1'.format(FLEETURL, 789, dt), auth=(FLEETUSR,FLEETPASS)).json()
    print("{}:\t{}\t{}".format(hb[0]["created_at"], hb[0]["data"]["truck"]["load"], hb[0]["data"]["truck"]["temperature"]["Package id 0"]))
    sheet1.write(row, 0, dt) ## TODO: change this to the actual time of the heartbeat not the searched time
    sheet1.write(row, 1, hb[0]["data"]["truck"]["load"])
    sheet1.write(row, 2, hb[0]["data"]["truck"]["temperature"]["Package id 0"])
    dt += incrementDelta
    row += 1

wb.save('test.xls')

#print("\t")
#print(hb[1])
