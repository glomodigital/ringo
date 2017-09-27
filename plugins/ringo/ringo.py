import os
import re
import spotipy
import pprint
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
from config import config

# Debugger
# import pdb

from rtmbot.core import Plugin

config.set_environ_variables()
song_uri = "spotify:track:0t8zIi7cwdADvWmkIWE1sp"


# ===============
# OAuth not working
# ===============
# client_id = 'e069be2e913e49e0bfacfe7363c954c4'
# client_secret = '41ae34499956431bbf35fa91c28f8e00'
#
# credentials = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
# token = credentials.get_access_token()

class RingoPlugin(Plugin):
    def __init__(self, name=None, slack_client=None, plugin_config=None):
        super(JukePyPlugin, self).__init__(name, slack_client, plugin_config)

        self.previous_volume = None
        self.slack_channel = plugin_config['slack_channel']

        self.commands = [
            ('help', self.command_help),
            ('song', self.command_current_song),
            ('play', self.command_playback_play),
            ('pause', self.command_playback_pause),
            ('skip', self.command_playback_skip),
            ('previous', self.command_playback_previous),
            ('volume', self.command_playback_volume),
            ('mute', self.command_playback_mute),
            ('unmute', self.command_playback_unmute),
            ('shuffle', self.command_current_shuffle),
            # ('.+', self.command_unknown)
        ]

        #=================
        # Authenticate with spotify
        #=================
        scope = 'user-read-playback-state playlist-modify-private user-library-read user-library-modify user-modify-playback-state user-read-currently-playing user-read-recently-played' # scope of access rights for the slack bot on spotify app
        username = '1265281092' # user id from spotify
        token = util.prompt_for_user_token(
            username,
            scope,
            client_id=os.environ.get('SPOTIPY_CLIENT_ID'),
            client_secret=os.environ.get('SPOTIPY_CLIENT_SECRET'),
            redirect_uri=os.environ.get('SPOTIPY_REDIRECT_URI')
        )

        # Instantiate spotipy
        self.sp = spotipy.Spotify(auth=token)

        # Log user
        user = self.sp.me()
        pprint.pprint(user)




    def append_channel_output(self, output):
        self.outputs.append([
            self.slack_channel,
            output
        ])


    def set_playback_volume(vol):
        print(vol)
        self.sp.volume(vol)


    def get_current_song(self):
        current_song = self.sp.current_user_playing_track()
        track_uri = current_song['item']['uri']
        return track_uri

    def get_user_device(self):
        devices = self.sp.devices()

        for device in devices['devices']:
            if device['is_active'] == True:
                device = device

        return device

    #=================
    # Assistance controls
    #=================
    # HELP
    def command_help(self, data):
        self.append_channel_output("""
Hey It's me :microphone: *Ringo* :guitar:! I'm here to help you with the _rock & roll_ in the office :the_horns:.


I can let you know the current song being played right now :headphones:. Just send the command:
- *`song`*: I'll send you Spotify URI back so you can see all the information about the track :tada:.


I can also control playback with the following commands:
- *`play`*: I'll resume a track or playlist, if it is paused.
- *`pause`*: I'll pause a track or playlst, if it is playing.
- *`skip`*: I'll skip the current song and play the next track in the playlist or queue.
- *`previous`*: I'll go back to the previous track that was played.
- *`volume up|down|0...100`*:
    - `up`: I'll increase the volume by _10%_.
    - `down`: I'll decrease the volume by _10%_.
    - `0-100`: I'll set the volume as a % to the number specified.
- *`mute`*: I'll mute the playback.
- *`unmute`*: I'll unmute the playback.


*Please note:* When you give commands to control the playlist I'll advertise the changes on *#music channel*


*TODO*:
- There are still things to implement see todo list
- If you have any issues or new ideas log them here
        """)

    def command_unknown(self, data):
        self.append_channel_output("Yo dude! I kinda didn't get what you mean, sorry :flushed:. If you need, just say `help` and I can tell you how I can be of use. :stuck_out_tongue_winking_eye:")
    #=================
    # Song controls
    #=================
    # SONG
    def command_current_song(self, data):
        current_song = self.get_current_song()
        self.append_channel_output('Current song being played on Spotify: {}'.format(current_song))

    # PLAY
    def command_playback_play(self, data):
        device = self.get_user_device()
        device_name = device['name']

        current_song = self.get_current_song()

        self.sp.start_playback()
        self.append_channel_output('Playing {} song from {}'.format(current_song, device_name))

    # PAUSE
    def command_playback_pause(self, data):
        device = self.get_user_device()
        device_name = device['name']

        current_song = self.get_current_song()

        self.sp.pause_playback()
        self.append_channel_output('Paused {} song on {}'.format(current_song, device_name))

    # SKIP/NEXT
    def command_playback_skip(self, data):
        self.sp.next_track()

        current_song = self.get_current_song()
        self.append_channel_output('Skipped playback to *next* song: {}'.format(current_song))

    # SKIP/PREVIOUS
    def command_playback_previous(self, data):
        self.sp.previous_track()

        current_song = self.get_current_song()
        self.append_channel_output('Skipped playback to *previous* song: {}'.format(current_song))

    # SHUFFLE
    def command_current_shuffle(self, data):
        return

    # VOL UP|DOWN|0-100
    def command_playback_volume(self, data):
        args = data['text'].split()
        arg = args[1]
        step = 10

        device = self.get_user_device()
        device_volume = device['volume_percent']

        if arg == 'up':
            if device_volume >= 90:
                self.sp.volume(100)
                self.append_channel_output('Playback volume is at *100%*.... Entering the *rave zone*')
            else:
                self.sp.volume(device_volume + step)
                self.append_channel_output('Let\'s pump the volume! Playback volume is at *{}%*'.format(device_volume + step))
        elif arg == 'down':
            if device_volume <= 10:
                self.command_playback_mute()
            else:
                self.sp.volume(device_volume - step)
                self.append_channel_output('Let\'s quieten things down a little bit. Playback volume is at *{}%*'.format(device_volume - step))
        else:
            self.sp.volume(int(arg))
            self.append_channel_output('You took charge! Playback volume is at *{}%*'.format(arg))

    # MUTE
    def command_playback_mute(self, data):
        device = self.get_user_device()
        self.previous_volume = device['volume_percent']
        self.sp.volume(0)
        self.append_channel_output('Playback volume is at *0%*.... Someone has muted me')

    # UNMUTE
    def command_playback_unmute(self, data):
        self.sp.volume(self.previous_volume)
        self.append_channel_output('Playback volume is at *{}%*.... I\'m unmuted again what a relief!'.format(self.previous_volume))

    # STATUS


    #=================
    # Queue controls
    #=================
    # queue <Spotify URI>
    # queue list



    #=================
    # Playlist controls
    #=================
    # LIST ADD <name> <Spotify URI>
    # LIST REMOVE <name>
    # lSIT RENAME <old_name> <new_name>
    # LIST START <name>

    #=================
    # Use RTM bot and slackclient
    #=================
    def process_message(self, data):
        for (expression, class_method) in self.commands:
            if re.match(expression, data['text'].lower()):
                class_method(data)
