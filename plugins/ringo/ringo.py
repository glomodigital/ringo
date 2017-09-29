import os
import re
import json
from datetime import datetime, timedelta
from slackclient import SlackClient
import spotipy
import pprint
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
from config import config

# Debugger
# import pdb

from rtmbot.core import Plugin

config.set_environ_variables()

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
        super(RingoPlugin, self).__init__(name, slack_client, plugin_config)

        self.is_dev = plugin_config['debug']
        self.previous_volume = None
        self.track_queue = ['spotify:track:6f49kbOuQSOsStBpyGvQfA', 'spotify:track:3bVwuZb0nYvAMn3roElQnY', 'spotify:track:0yac0FPhLRH9i9lOng3f81', 'spotify:track:6IVlHRrjTKep5SS9kbcpTa']
        self.queue_playing = False
        self.slack_channel = plugin_config['slack_channel']

        self.slack_client = SlackClient(os.environ.get('SLACK_CLIENT_BOT_KEY'))

        # Get list of users
        response = self.slack_client.api_call('users.list')
        self.users = response['members']

        self.commands = [
            ('help|hey', self.command_help),
            ('song', self.command_current_song),
            ('play', self.command_playback_play),
            ('pause', self.command_playback_pause),
            ('skip|next', self.command_playback_skip),
            ('previous', self.command_playback_previous),
            ('volume', self.command_playback_volume),
            ('mute', self.command_playback_mute),
            ('unmute', self.command_playback_unmute),
            ('shuffle', self.command_current_shuffle),
            ('unshuffle', self.command_current_unshuffle),
            ('queue', self.command_queue),
            # ('.+', self.command_unknown)
        ]

        #=================
        # Authenticate with spotify
        # See scopes here https://developer.spotify.com/web-api/using-scopes/
        #=================
        scope = 'user-read-playback-state user-follow-modify user-follow-read playlist-read-collaborative playlist-read-private playlist-modify-public playlist-modify-private user-library-read user-library-modify user-modify-playback-state user-read-currently-playing user-read-recently-played ugc-image-upload streaming' # scope of access rights for the slack bot on spotify app
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
        self.sp_user = self.sp.me()
        self.sp.repeat('context') # Repeat is always on for now






    def append_channel_output(self, output):
        self.outputs.append([
            self.slack_channel,
            output
        ])

    def show_error_message(self, message):
        message = """
{}

Alternatively type `help` to see the help menu.
 """.format(message)
        self.append_channel_output(message)

    def check_spotify_argument(self, arg):
        return re.match(r'((spotify:(track|album|user|artist):([\d\w])*)|(https:\/\/open\.spotify\.com\/(user|track)\/([\d\w\\/])*))', arg)

    def get_current_song(self):
        current_song = self.sp.current_user_playing_track()
        duration = current_song['item']['duration_ms']

        def format_timedelta(td):
            minutes, seconds = divmod(td.seconds + td.days * 86400, 60)
            return '{:02d}:{:02d}'.format(minutes, seconds)

        return {
            'track_artist': current_song['item']['artists'][0]['name'],
            'track_name': current_song['item']['name'],
            'track_duration': format_timedelta(timedelta(milliseconds=duration)),
            'track_uri': self.get_current_song_uri()
        }

    def get_current_song_uri(self):
        current_song = self.sp.current_user_playing_track()
        return current_song['item']['uri']

    def get_user_device(self):
        devices = self.sp.devices()

        for device in devices['devices']:
            if device['is_active'] == True:
                device = device

        return device

    def get_username(self, user_id):
        for user in self.users:
            if user['id'] == user_id:
                return '<@{}>'.format(user['name'])

        # Unmatched user
        return 'someone'

    def normalize_uri(self, uri):
        for char in ['<', '>']:
            if char in uri:
                uri = uri.replace(char, '')

        return uri



    #=================
    # Assistance controls
    #=================
    # HELP
    def command_help(self, data, user):
        self.append_channel_output("""
Hey It's me :microphone: *Ringo* :guitar:! I'm here to help you with the _rock & roll_ in the office :the_horns:.


I can let you know the current song being played right now :headphones:. Just send the command:
- *`song`*: I'll send you Spotify URI back so you can see all the information about the track :tada:.


I can also control playback with the following commands:
- *`play`*: I'll resume a track or playlist, if it is paused.
- *`pause`*: I'll pause a track or playlst, if it is playing.
- *`skip|next`*: I'll skip the current song and play the next track in the playlist or queue.
- *`previous`*: I'll go back to the previous track that was played.
- *`volume up|down|0...100`*:
    - `up`: I'll increase the volume by _10%_.
    - `down`: I'll decrease the volume by _10%_.
    - `0-100`: I'll set the volume as a % to the number specified.
- *`mute`*: I'll mute the playback.
- *`unmute`*: I'll unmute the playback.
- *`shuffle`*: I'll shuffle the playback.
- *`unshuffle`*: I'll unshuffle the playback.


*Please note:* When you give commands to control the playlist I'll advertise the changes on *#music channel*


*TODO*:
- There are still things to implement see _todo list_ https://github.com/globalmouth/ringo/blob/master/README.md#todo-list
- If you have any _issues_ or _new ideas_ log them here https://github.com/globalmouth/ringo/issues
        """)

    def command_unknown(self, data):
        self.append_channel_output("Yo dude! I didn't get what you meant, sorry :flushed:. If you need, just say `help` and I can tell you how I can be of use. :stuck_out_tongue_winking_eye:")


    #=================
    # Song controls
    #=================
    # SONG
    def command_current_song(self, data, user):
        current_song = self.get_current_song()

        self.append_channel_output("""
<@{user}> the current song being played on Spotify is:

>>>*Track information*

Name: *{track_name}*
Artist: _{track_artist}_
Duration: _{duration}_

Spotify URI: {uri}

""".format(user=user, track_name=current_song['track_name'], track_artist=current_song['track_artist'], duration=current_song['track_duration'], uri=current_song['track_uri']))

    # PLAY
    def command_playback_play(self, data, user):
        device = self.get_user_device()
        device_name = device['name']

        args = data['text'].split()


        if len(args) > 1:
            arg = self.normalize_uri(args[1])
            print(arg)
            is_spotify_uri = self.check_spotify_argument(arg)

            if is_spotify_uri:
                if 'track' in arg:
                    print([arg, *self.track_queue])
                    self.sp.start_playback(uris=[arg, *self.track_queue])
                else:
                    self.sp.start_playback(context_uri=arg)

                current_song = self.get_current_song_uri()
                self.append_channel_output('<@{}> started playing {} song'.format(user, current_song))
            else:
                self.show_error_message('Soz awks :flushed:. That was not a valid *Spotify URI or URL*, currently Ringo only supports a Spotify URI or URL. _See (https://spotipy.readthedocs.io/en/latest/#ids-uris-and-urls) for more details._')
        else:
            if len(self.track_queue) >= 1:
                self.sp.start_playback(uris=self.track_queue)
                current_song = self.get_current_song_uri()
                self.append_channel_output('<@{}> started playing {} song from the queue.'.format(user, current_song))
            else:
                self.sp.start_playback()
                current_song = self.get_current_song_uri()
                self.append_channel_output('<@{}> started playing {} song'.format(user, current_song))


    # PAUSE
    def command_playback_pause(self, data, user):
        current_song = self.get_current_song_uri()
        self.sp.pause_playback()
        self.append_channel_output('<@{}> paused {} song'.format(user, current_song))

    # SKIP/NEXT
    def command_playback_skip(self, data, user):
        # if len(self.track_queue) < 1 and self.queue_playing:
        #     self.append_channel_output('Sorry <@{}> there were no more songs left in the queue to play. Add some more tracks or start a playlist.'.format(user))
        #     self.queue_playing = False
        #     print(self.queue_playing)
        #     return

        self.sp.next_track()
        # self.track_queue.pop(-1) # remove first item from track queue once played
        # print(self.track_queue)
        current_song = self.get_current_song_uri()
        self.append_channel_output('<@{}> skipped playback to *next* song: {}'.format(user, current_song))

    # SKIP/PREVIOUS
    def command_playback_previous(self, data, user):
        self.sp.previous_track()
        current_song = self.get_current_song_uri()
        self.append_channel_output('<@{}> went to the *previous* song: {}'.format(user, current_song))

    # SHUFFLE
    def command_current_shuffle(self, data, user):
        self.sp.shuffle(True)
        self.append_channel_output('<@{}> turned *on* shuffle.'.format(user))

    # UNSHUFFLE
    def command_current_unshuffle(self, data, user):
        self.sp.shuffle(False)
        self.append_channel_output('<@{}> turned *off* shuffle.'.format(user))

    # VOL UP|DOWN|0-100
    def command_playback_volume(self, data, user):
        args = data['text'].split()
        arg = args[1]
        step = 10

        device = self.get_user_device()
        device_volume = device['volume_percent']

        if arg == 'up':
            if device_volume >= 90:
                self.sp.volume(100)
                self.append_channel_output('<@{}> Playback volume is at *100%*.... Entering the *rave zone*'.format(user))
            else:
                self.sp.volume(device_volume + step)
                self.append_channel_output(':point_up: Let\'s pump the volume! <@{}> turned up the volume. It is now at *{}%*'.format(user, device_volume + step))
        elif arg == 'down':
            if device_volume <= 10:
                self.command_playback_mute()
            else:
                self.sp.volume(device_volume - step)
                self.append_channel_output(':point_down: Let\'s quieten things down a little bit. <@{}> turned down the volume. It is now at *{}%*'.format(user, device_volume - step))
        else:
            self.sp.volume(int(arg))
            self.append_channel_output('<@{}> has set the playback volume to *{}%*'.format(user, arg))

    # MUTE
    def command_playback_mute(self, data, user):
        device = self.get_user_device()
        self.previous_volume = device['volume_percent']
        self.sp.volume(0)
        self.append_channel_output('<@{}> muted the playback'.format(user))

    # UNMUTE
    def command_playback_unmute(self, data, user):
        self.sp.volume(self.previous_volume)
        self.append_channel_output('<@{}> unmuted the playback. Volume is at {}%'.format(user, self.previous_volume))

    # REPEAT


    #=================
    # Queue controls
    #=================
    # queue <Spotify URI>
    def command_queue(self, data, user):
        # self.queue_playing = True
        args = data['text'].split()
        print(args[1:])
        for arg in args[1:]:
            uri = self.normalize_uri(args[1])
            is_spotify_uri = self.check_spotify_argument(uri)

            if is_spotify_uri:
                self.track_queue.append(uri)
                print(self.track_queue)
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
    def catch_all(self, data):
        if self.is_dev:
            print(data)

    def process_group_joined(self, data):
        self.command_help(data, None)

    def process_channel_joined(self, data):
        self.command_help(data, None)

    def process_channel_left(self, data):
        self.append_channel_output('*:open_mouth: I\'ve kicked me from the <#{}> group*. You cannot control Spotify playback from this channel now :sob:'.format(data['cahnnel']))

    def process_group_left(self, data):
        self.append_channel_output('*:open_mouth: I\'ve kicked me from the <#{}> group*. You cannot control Spotify playback from this channel now :sob:'.format(data['cahnnel']))

    def process_message(self, data):
        for (expression, class_method) in self.commands:
            if re.match(r'{}'.format(expression), data['text'].lower()):
                user = data['user']
                class_method(data, user)
