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
from io import BytesIO
from wand.image import Image
from wand.drawing import Drawing
from wand.drawing import Color
from wand.display import display

from TwitterAPI import TwitterAPI
import requests
import time
import os
import ConfigParser

degree_sign= u'\N{DEGREE SIGN}'
logo = Image(filename='images/logo.png')
thermo = Image(filename='images/thermo.png')

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

status_msg = 'Print done: ' + str(printpercentmsg)
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

sendtweet = True
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
    img = Image(blob=picdata)
    s = img.clone()
    l = logo.clone()
    t = thermo.clone()
    l.transparentize(0.30)
    with Drawing() as draw:
	#Draw Octoprint logo in the upper left corner
	draw.composite(operator='dissolve', left=525, top=395,
               width=l.width, height=l.height, image=l)
	#Draw transparent black rectangle on the bottom of picture
	draw.fill_color = Color('rgba(0, 0, 0, 0.5)')
	draw.rectangle(left=0, top=400, right=500, bottom=480, radius=5)
	#Insert thermometer pic over transparent rectangle
	draw.composite(operator='dissolve', left=7, top=409,
               width=t.width, height=t.height, image=t)
	draw.fill_color = Color('rgba(100, 100, 100, 0.8)')
	draw.rectangle(left=55, top=413, right=57, bottom=467)
	draw.rectangle(left=300, top=413, right=302, bottom=467)
	#Draw text
	#Text top row
	draw.fill_color = Color('rgba(255, 255, 255, 1.0)')
	draw.font = 'fonts/Roboto-Medium.ttf'
	draw.font_size = 20
	#Hot end text
	hotendtext = 'Hot end actual: ' + str(hotendactual) + degree_sign + 'C'
	draw.text(65, 430, hotendtext)
	hotendtext = 'Hot end target: ' + str(hotendtarget) + degree_sign + 'C'
	draw.text(65, 465, hotendtext)
	#Bed text
	hotendtext = 'Bed actual: ' + str(bedactual) + degree_sign + 'C'
	draw.text(310, 430, hotendtext)
	hotendtext = 'Bed target: ' + str(bedtarget) + degree_sign + 'C'
	draw.text(310, 465, hotendtext)
	draw(s) #Apply all the overlay changes
	#display(s) #For debug only. Displays image locally.
        #Convert the wand image back into a blob
        #that can be sent with requests to the twitter API
        picdata = s.make_blob('jpeg')
    r = api.request('statuses/update_with_media', {'status':status_msg}, {'media[]':picdata})
    print 'Twitter status code: ' + str(r.status_code)
    print 'Twitter response: ' + str(r.text)

