#!/usr/bin/python3

import sys
import requests
import json
from time import sleep
from os import getenv as os_getenv


DEBUG = os_getenv("DEBUG") == "True"
OFFLINE = os_getenv("OFFLINE") == "True"

max_entries = 200
timeout = 10.0  # Could lower to 0.125 eventually

print('Starting SonyDevWorld Telegram Bot python script...')
last_file = 'laststatus.txt'  # Last published update
last_status = None
# Example token: 1234567890:ABCDb1o0-ASDKHKJ3oiavKJDSFKJHkjwebb
token = os_getenv('SONYDEVWORLD_BOT_TOKEN')
# Example channel: -1000000000000 for t.me/MyExampleChannel
# You can get this from e.g. @getidsbot
channel = os_getenv('SONYDEVWORLD_BOT_CHANNEL')

if DEBUG:
    print("Token: {}, channel: {}".format(token, channel))

telegram_api = 'https://api.telegram.org/bot{}/sendMessage'.format(token)
base_url = 'https://developer.sony.com'
url = '{}/api/post-resources/fetch-posts/?resourceIs=file-download&limit={}'\
        .format(base_url, str(max_entries))

try:
    with open(last_file, 'r') as f:
        last_status = f.readline().strip()
except FileNotFoundError:
    print("{0} not found, starting from scratch".format(last_file))

if OFFLINE:
    # Work with local copy, avoid hammering the Dev World server
    with open('items.json', 'r') as f:
        items = json.load(f)
else:
    try:
        r = requests.get(url)
    except Exception as e:
        print('Failed to connect! Exception: {}'.format(e))
        sys.exit(1)
    items = json.loads(r.text)
    # Do this once
    #with open('items.json', 'w') as f:
    #    json.dump(items, f)

x = 0
check = True
while check:
    if x == len(items):
        # Can happen if too many entries were pushed (unrealistic) or saved
        # entry was taken down... Too bad!
        print("Saved state not found in response, posting all items")
        break
    guid = items[x]['guid']  # e.g. 'file-download-798601'
    check = guid != last_status
    if check:
        x += 1
    else:
        print("Found last item, continuing where we last left off: {}{}"
              .format(base_url, items[x]['permalink']))

t = 0
for n in reversed(range(0, x)):
    post = items[n]
    tags = post['tags']
    title = post['post_title']
    link = base_url + post['permalink']
    if len(post['vc_content']):  # Do not try to understand it
        vccont = post['vc_content'][0]
        while 'content' not in vccont:
            vccont = vccont['children'][0]
        description = vccont['content']
    else:
        description = post['post_content']
    size = post['download_file']['filesize']
    message = ' <b>{3}</b>\n\n{0}\n\n<a href=\'{2}\'>Download {3} ({1})</a>'\
        .format(description, size, link, title)
    message = message.replace('<p>', '')  # I do not remember why we need this
    message = message.replace('</p>', '')
    # Probably because Sony added <p> tags to description and
    # Telegram was messing up the HTML parsing (see below)
    if not tags:
        # Indicate that we found an unpublished entry
        if DEBUG:
            print('Skipping unpublished entry: {}'.format(link))
        continue

    t += 1
    # Take longer timeout before every 12th post to TG API
    # (Be even more cautious of being throttled)
    if t % 12 == 0:
        print("Cooling down a bit, sleeping for 100s")
        sleep(100.0)

    print("Posting item '{}' to TG".format(title))

    # Post to Telegram API
    r = requests.post(telegram_api,
                      data={
                          'chat_id': channel,
                          'text': message,
                          'parse_mode': 'HTML'
                          }
                      )
    # Response should look like:
    # b'{"ok":true,"result":...}
    if DEBUG:
        print("Got response from TG API: {}".format(r.content))

    r_dict = json.loads(r.content)
    if r_dict.get("ok") is not True:
        print("Failed to post to TG API, aborting!")
        if DEBUG:
            print(r.content)
        # Save progress before bailing
        with open(last_file, 'w') as f:
            f.write(guid)
        sys.exit(1)

    # Update guid only at this point so that only published entries are saved
    guid = post['guid']  # e.g. 'file-download-798601'

    sleep(timeout)  # We do not want to be cooled down by Bot API

# Write guid of last posted entry to laststatus.txt
with open(last_file, 'w') as f:
    f.write(guid)
