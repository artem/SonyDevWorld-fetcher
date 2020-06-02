#!/usr/bin/python3
import sys
from time import sleep
import requests
import json
import socket
import socks


use_proxy = True
max_entries = 20

print('Started')
last_file = 'SonyOSS.status' # last published update
token = 'bot token goes here'
channel = '-1001334007105' # https://t.me/SMDW_downloads

if use_proxy:
    socks.set_default_proxy(socks.SOCKS5, "localhost", 9050, True) # TOR proxy to push to Telegram
    socket.socket = socks.socksocket

telegram = 'https://api.telegram.org/bot{0}/sendMessage'.format(token)
base_url = 'https://developer.sony.com'
url = base_url + '/api/post-resources/fetch-posts/?resourceIs=file-download&limit=' + max_entries
with open(last_file, 'r') as f:
    status = f.readline().strip()

try:
    r = requests.get(url)
except:
    print('Failed to connect server! :(')
    sys.exit()

items = json.loads(r.text)

x = 0
check = True
while check:
    if x == len(items):
        print('Unfortunately, we are fucked') # means saved state could not be found in JSON response
        sys.exit()       # can happen if too many entries were pushed (unrealistic) or saved entry was taken down... Too bad!
    link = base_url + items[x]['permalink']
    check = link != status
    if check:
        #print(link, status) yes, this is print() debug leftover
        x += 1

for n in reversed(range(0, x)):
    post = items[n]
    tags = post['tags']
    title = post['post_title']
    link = base_url + post['permalink']
    if len(post['vc_content']): # Do not try to understand it
        vccont = post['vc_content'][0]
        while not 'content' in vccont:
            vccont = vccont['children'][0]
        description = vccont['content']
    else:
        description = post['post_content']
    size = post['download_file']['filesize']
    message = ' <b>{3}</b>\n\n{0}\n\n<a href=\'{2}\'>Download {3} ({1})</a>'.format(description, size, link, title)
    message = message.replace('<p>', '') # I do not remember why we need this
    message = message.replace('</p>', '') # prob because sony added <p> tags to description and TG was messing up shit with HTML parsing (see below)
    if not tags:
        print('VERY secret!!!') # indicate that we have found an unpublished entry 
        #print(message)
        continue
    #print(message)
    r = requests.post(telegram, data={'chat_id': channel, 'text': message, 'parse_mode': 'HTML'}) # lvl 100 Telegram API
    with open(last_file, 'w') as f:
        f.write(link)
    sleep(0.125) # We do not want to be cooled down by Bot API
