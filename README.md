# SonyDevWorld Telegram Bot

The bot that powers [t.me/SMDW_downloads](https://t.me/SMDW_downloads)

*Neither affiliated nor endorsed by Sony Mobile*

### Requirements:

You need to have `python3` installed with the `requests` module.

Further, you need to supply token and channel id via environment variables:

- `SONYDEVWORLD_BOT_TOKEN`: Bot token,
  get one from [t.me/botfather](https://t.me/botfather),
  e.g. `1234567890:ABCDb1o0-ASDKHKJ3oiavKJDSFKJHkjwebb`
- `SONYDEVWORLD_BOT_CHANNEL`: Channel id to post to,
  e.g. `-1000000000000` for [t.me/MyExampleChannel](https://t.me/MyExampleChannel).
  You can quickly obtain channel info from [@getidsbot](https://t.me/getidsbot)

### Running

```
export SONYDEVWORLD_BOT_TOKEN=<my-token>
export SONYDEVWORLD_BOT_CHANNEL=<my-channel-id>
python3 SonyDevWorld.py
```

It makes sense to run this bot maybe once an hour to avoid hammering the Sony
Dev World API.

Set `export DEBUG=true` to run in debug mode, set `export OFFLINE=True` to run
in offline mode after you've saved `items.json`.


### Deploying
For deploying, a simple `systemd` unit file with a timer is included.

After you've supplied your token inside the `.service` file and copied the unit
and timer files into `~/.config/systemd/user/`, you can run this unit without
special permissions as a user unit via
`systemctl --user daemon-reload` and then
`systemctl --user enable --now sonydevworldbot.timer`

### Details
`SonyDevWorld.py` does all the heavy lifting for you. It posts to the Telegram
bot API at `https://api.telegram.org/bot<token>/sendMessage`

The last posted item's `guid` info is saved to `laststatus.txt`. It would look
something like `file-download-786918`.
