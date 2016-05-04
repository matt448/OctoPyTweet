#!/usr/bin/python

# Written by Matthew McMillan
# matthew.mcmillan@gmail.com
# @matthewmcmillan
# @MattsPrintrbot
# https://matthewcmcmillan.blogspot.com

###############
# Description
#
# This is a simple script to tweet stats and pictures for print jobs 
# running on an OctoPrint print server. It is called from cron once a minute.
# This would be better if it was an OctoPrint plug-in but what can you do.
# It works and I don't have time to learn how to make a plug-in right now.
#


from TwitterAPI import TwitterAPI
import requests
import time
import os
import ConfigParser


# Read settings from the config file
settings = ConfigParser.ConfigParser()
settings.read('config.cfg')
host = settings.get('OctoPrintAPI', 'host')
apikey = settings.get('OctoPrintAPI', 'apikey')
debug = int(settings.get('Debug', 'debug_enabled'))
CONSUMER_KEY = settings.get('TwitterAPI', 'CONSUMER_KEY')
CONSUMER_SECRET = settings.get('TwitterAPI', 'CONSUMER_SECRET')
ACCESS_TOKEN_KEY = settings.get('TwitterAPI', 'ACCESS_TOKEN_KEY')
ACCESS_TOKEN_SECRET = settings.get('TwitterAPI', 'ACCESS_TOKEN_SECRET')

#Header for Octoprint API requests
headers = {'X-Api-Key': apikey}

# This stores the completion percentage from the last run
tmpfile = '/tmp/tweetpercent.txt'

# Default to not send tweet
sendtweet = False

###################################
#
# FUNCTIONS
#
###################################

def readlastpercent():
    if os.path.exists(tmpfile) and os.path.getsize(tmpfile) > 0:
        file = open(tmpfile, 'r')
        last_percent = file.read()
        file.close()
        print 'Percent from last run: ' + str(last_percent) + '%'
        return(int(last_percent))
    else:
        print 'Temp file ' + tmpfile + ' doesn\'t exist or is empty'
        print 'Creating new tmp file with 0%'
        file = open(tmpfile, 'w')
        file.write('0')
        file.close()
        return(0)

def writetmpfile( printpercent ):
    print 'Writing ' + str(printpercent) + '% to ' + tmpfile
    file = open(tmpfile, 'w')
    file.write(str(printpercent))
    file.close()
    return




###################################
#
# MAIN
#
###################################

# Get the temperatures of the hotend and bed
r = requests.get('http://' + host + '/api/printer', headers=headers)
#print 'STATUS CODE: ' + str(r.status_code)
# Non 200 status code means the printer isn't responding
if r.status_code == 200:
    printeronline = True
    printerstate = r.json()['state']
    print 'STATE: ' + str(printerstate)
    hotendactual = r.json()['temperature']['tool0']['actual']
    hotendtarget = r.json()['temperature']['tool0']['target']
    hotmsg = ('Hotend: [') + str(hotendactual) + 'C / ' + str(hotendtarget) + 'C]'
    bedactual = r.json()['temperature']['bed']['actual']
    bedtarget = r.json()['temperature']['bed']['target']
    bedmsg = ('Bed: [') + str(bedactual) + 'C / ' + str(bedtarget) + 'C]'
    isprinting = r.json()['state']['flags']['printing']
else:
    printeronline = False
    hotmsg = ''
    bedmsg = ' 3D Printer offline'
    if debug:
        print 'STATUS CODE: ' + str(r.status_code)
        print bedmsg
    exit()

# Only check job status if the printer is online
if printeronline:
    r = requests.get('http://' + host + '/api/job', headers=headers)
    printtime = r.json()['progress']['printTimeLeft']
    if printtime is None:
        printtimemsg = '00:00:00'
    else:
        printhours = int(printtime/60/60)
        if printhours > 0:
            printminutes = int(printtime/60)-(60*printhours)
        else:
            printminutes = int(printtime/60)
        printseconds = int(printtime % 60)
        printtimemsg = str(printhours).zfill(2) + ':' + str(printminutes).zfill(2) + ':' + str(printseconds).zfill(2)

    printpercent = r.json()['progress']['completion']
    if printpercent is None:
        printpercentmsg = '---%'
    else:
        printpercent = int(printpercent)
    printpercentmsg = str(printpercent) + '%'

status_msg = bedmsg + '\r\n' + hotmsg + '\r\n' + 'Print done: ' + str(printpercentmsg)
status_msg += '\r\n #3DPrinting #Printrbot'


last_percent = readlastpercent()

if last_percent == printpercent:
    print 'Not tweeting status or writing to tmp file because percent hasn\'t changed'
    print 'Current: ' + str(printpercent) + '%'
    print '   Last: ' + str(last_percent) + '%'
    print
    sendtweet = False
elif printpercent == 0 and isprinting:
    status_msg = 'Starting new job!' + '\r\n' + status_msg
    sendtweet = True
elif printpercent >= (last_percent/10*10) + 10 and isprinting and printpercent < 100:
    print 'Current: ' + str(printpercent) + '%'
    print '   Last: ' + str(last_percent) + '%'
    print
    sendtweet = True
elif printpercent == 100:
    status_msg = 'Job complete!' + '\r\n' + status_msg
    sendtweet = True
else:
    print 'Not tweeting status or writing to tmp file because percent hasn\'t reached threshold'
    print 'Current: ' + str(printpercent) + '%'
    print '   Last: ' + str(last_percent) + '%'

if sendtweet:
    print 'Updating ' + tmpfile
    writetmpfile(printpercent)
    print 'Message length: ' + str(len(status_msg))
    print 'Sending tweet!'
    print '---------------------'
    print status_msg
    print '---------------------'
    api = TwitterAPI(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET)
    #Grab picture from web cam
    r = requests.get('http://' + host + ':8080/?action=snapshot')
    picdata = r.content
    r = api.request('statuses/update_with_media', {'status':status_msg}, {'media[]':picdata})
    print 'Twitter status code: ' + str(r.status_code)
    #status = api.PostUpdate(status_msg)
    #print status.text
