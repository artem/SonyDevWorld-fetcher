#!/usr/bin/python3

import sys
import requests
import json
from time import sleep
from os import getenv as os_getenv


DEBUG = os_getenv("DEBUG") == "True"
OFFLINE = os_getenv("OFFLINE") == "True"

max_entries = 50
timeout = 0.125
long_timeout = 40.0

print('Starting SonyDevWorld Telegram Bot python script...')
last_file = 'laststatus.txt'  # Last published update
last_status = [None]
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
        last_status = f.read().splitlines()
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
    # Do this once for working offline:
    #with open('items.json', 'w') as f:
    #    json.dump(items, f)
    #with open('items-pretty.json', 'w') as f:
    #    prettified = json.dumps(items, indent=4)
    #    f.write(prettified)

x = 0
check = True
while check:
    if x == len(items) and None in last_status:
        # Can happen if too many entries were pushed (unrealistic) or 3
        # consecutive items at once were taken down (even more unrealistic)
        # We can deal with this in two ways:
        # Option A - Post all items:
        print("Saved state not found in response, posting all items")
        break
        # Option B - Bail out
        #print("Saved state not found in response, maybe item was taken down?")
        #print("Exiting")
        #sys.exit(1)
    guid = items[x]['guid']  # e.g. 'file-download-798601'
    check = guid not in last_status
    if check:
        x += 1
    else:
        print("Found last posted item, continuing after we last left off: {}{}"
              .format(base_url, items[x]['permalink']))
        items = items[:x]

# Filter out entries that are not OSS archives or blobs,
# and also unpublished entries which have no tags
items = filter(lambda x: x.get("tags"), items)
items = list(reversed(list(filter(
    lambda x: x["tags"][0].get("slug") in [
        "xperia-open-source-archives",
        "software-binaries"],
    items))))

if len(items) == 0:
    print("No new items!")
    sys.exit(0)

last_guids = []
t = 0
for n in range(0, len(items)):
    post = items[n]
    tags = post.get('tags')
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

    # Take longer timeout before every 12th post to TG API
    # (Be even more cautious of being throttled)
    t += 1
    if t % 12 == 0:
        print("Cooling down a bit, sleeping for {}s".format(long_timeout))
        sleep(long_timeout)

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
        if last_guids:
            with open(last_file, 'w') as f:
                f.writelines(last_guids)
        sys.exit(1)

    # Update guid at this point so that only published entries are saved
    last_guids = [
        "{}\n".format(items[n].get("guid")),
        "{}\n".format(items[max(n - 1, 0)].get("guid")),
        "{}\n".format(items[max(n - 2, 0)].get("guid"))
    ]

    sleep(timeout)  # We do not want to be cooled down by Bot API

# Write guid of last posted entry to laststatus.txt
with open(last_file, 'w') as f:
    f.writelines(last_guids)
