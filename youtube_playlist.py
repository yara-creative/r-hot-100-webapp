import pandas as pd
import numpy as np
import datetime
import googleapiclient.discovery
import googleapiclient.errors
import re
#import webbrowser as wb
import requests
from bs4 import BeautifulSoup
import warnings
from pandas.core.common import SettingWithCopyWarning
import logging
from user_credentials import Y_API_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
# Set up warnings
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

# Import data
song_data = pd.read_csv("data/reddit_top_150_songs_%s.csv" % (str(datetime.date.today())))
logging.critical("\n---DataFrame created from import 'reddit_top_150_songs_%s.csv'---\n" % (str(datetime.date.today())))

# YouTube - direct API Key authentication
api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = Y_API_KEY

yt = googleapiclient.discovery.build(api_service_name, api_version, developerKey=DEVELOPER_KEY)

logging.critical("\n---Connected to YouTube API---\n")

# Get YouTube video IDs
video_ids = song_data['yt_video_id'].dropna()
video_ids_1 = video_ids[0:50].reset_index(drop=True)
logging.info("\n---List created: YouTube video IDs (songs 1-50)---\n")
video_ids_2 = video_ids[51:101].reset_index(drop=True)
logging.info("\n---List created: YouTube video IDs (songs 51-100)---\n")

def get_playlist_string(video_ids_list):
    """
    Inputs list of video IDs and outputs string that can be used to create a YouTube playlist.
    """
    playlist_string = 'http://www.youtube.com/watch_videos?video_ids=' 

    for video in video_ids_list:
        playlist_string = playlist_string + video + ','
        
    return playlist_string

# Get playlist strings (split into two playlist due to max 50 videos per playlist through this method)
logging.info("\n---Executing 'get_playlist_string'...---\n")
playlist_string_1 = get_playlist_string(video_ids_1)
logging.info("\n---Playlist string 1 created---\n")
logging.info("\n---Executing 'get_playlist_string'...---\n")
playlist_string_2 = get_playlist_string(video_ids_2)
logging.info("\n---Playlist string 2 created---\n")

def get_playlist_link(string):
    """
    Inputs long playlist string and returns redirected URL.
    """
    #wb.open(string) # activates playlist

    r = requests.get(string)
    
    soup = BeautifulSoup(r.text, 'html.parser')
    redirected_url = soup.find('link', rel='canonical')['href']

    return redirected_url

# Get playlist links
logging.info("\n---Executing 'get_playlist_link'...---\n")
playlist_link_1 = get_playlist_link(playlist_string_1)
logging.info("\n---Playlist link 1 created---\n")
logging.info("\n---Executing 'get_playlist_link'...---\n")
playlist_link_2 = get_playlist_link(playlist_string_2)
logging.info("\n---Playlist link 2 created---\n")

def get_suffix(string):
    """
    Inputs string of playlist link and outputs the suffix to construct the link to embed the playlist.
    """
    suffix_list = re.findall('list\=(.+)', string)
    suffix_string = suffix_list[0]
    
    return suffix_string

# Get link suffixes
logging.info("\n---Executing 'get_suffix'...---\n")
suffix_1 = get_suffix(playlist_link_1)
logging.info("\n---SRC suffix string 1 created---\n")
logging.info("\n---Executing 'get_suffix'...---\n")
suffix_2 = get_suffix(playlist_link_2)
logging.info("\n---SRC suffix string 2 created---\n")

# Create YouTube playlist embed src for Streamlit and export .py file
youtube_embed_src1 = "https://www.youtube.com/embed/videoseries?list=" + suffix_1
youtube_embed_src2 = "https://www.youtube.com/embed/videoseries?list=" + suffix_2

# Save src embed links in Python script
with open('youtube_links.py', 'w') as f:
    f.write('youtube_embed_src1="%s"\nyoutube_embed_src2="%s"\nplaylist_link_1="%s"\nplaylist_link_2="%s"' %  (youtube_embed_src1, youtube_embed_src2, playlist_link_1, playlist_link_2))
logging.info("\n---Python file written: YouTube src links and playlist links---\n")

# Preserve src embed links in text file
with open('data/youtube_links_%s.txt' % (str(datetime.date.today())), 'w') as f:
    f.write('youtube_embed_src1="%s"\nyoutube_embed_src2="%s"\nplaylist_link_1="%s"\nplaylist_link_2="%s"' %  (youtube_embed_src1, youtube_embed_src2, playlist_link_1, playlist_link_2))
logging.info("\n---Text file written: YouTube src links and playlist links---\n")