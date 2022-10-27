import pandas as pd
import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import warnings
from pandas.core.common import SettingWithCopyWarning
import logging
from user_credentials import S_CLIENT_ID, S_SECRET_KEY, S_USERNAME, S_REDIRECT_URI

# Set up logging
logging.basicConfig(level=logging.INFO)
# Set up warnings
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

# Import data
song_data = pd.read_csv("data/spotify_top_100_songs_%s.csv" % (str(datetime.date.today())))
logging.critical("\n---DataFrame created from import 'spotify_song_data_%s.csv'---\n" % (str(datetime.date.today())))

# Get user access to edit Spotify playlist
username = S_USERNAME
scope = 'playlist-modify-public'

token = spotipy.util.prompt_for_user_token(username, scope, client_id=S_CLIENT_ID,
                                           client_secret=S_SECRET_KEY, redirect_uri=S_REDIRECT_URI)

sp = spotipy.Spotify(auth=token)

logging.critical("\n---Connected to Spotify API: access to edit user playlist---\n")

# Get track ids for songs with Spotify links and save in a list
track_ids = list(song_data[['id']].loc[~(song_data['id'].isna())]['id']) # exclude missing values / NaNs

# Get top 100 track IDs
track_ids_100 = track_ids[0:100]

# Get user playlists and get playlist ID of first entry
playlists = sp.user_playlists(S_USERNAME, limit=50, offset=0)
playlist_id = playlists['items'][0]['id']

###---Make new playlist and add 100 tracks---###

# Create new public playlist for user
#new_playlist = sp.user_playlist_create(S_USERNAME, 'r/ Daily Hot 100', public=True, collaborative=False, description='The top 100 recommended songs on r/music and r/listentothis found on Spotify every day.')

# Get playlist ID
#new_playlist_id = new_playlist['id']

# Add top 100 tracks
#sp.playlist_add_items(new_playlist_id, track_ids_100, None)

###---Replace existing tracks with new 100 tracks---###

# Replace tracks in existing playlist
sp.user_playlist_replace_tracks(S_USERNAME, playlist_id, track_ids_100)
logging.info("\n---Replaced Spotify playlist tracks---\n")

# Get Spotify player embed code for the playlist to add to Streamlit 
spotify_embed_src = 'https://open.spotify.com/embed/playlist/%s' % (playlist_id)
spotify_playlist_link = 'https://open.spotify.com/playlist/%s' % (playlist_id)

# Save embed src link to import into streamlit dashboard in Python script
##with open('spotify_links.py', 'w') as f:
#    f.write('spotify_embed_src="%s"\nspotify_playlist_link="%s"' % (spotify_embed_src, spotify_playlist_link))
#logging.info("\n---Python file written: 'spotify_links'---\n")

# Preserve embed src link and playlist link in text file
#with open('data/spotify_links_%s.txt' % (str(datetime.date.today())), 'w') as f:
#    f.write('spotify_embed_src="%s"\nspotify_playlist_link="%s"' % (spotify_embed_src, spotify_playlist_link))
#logging.info("\n---Text file written: 'spotify_links'---\n")