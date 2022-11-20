import pandas as pd
import datetime
import googleapiclient.discovery
import googleapiclient.errors
import re
from IPython.display import HTML
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

###---Use YouTube API---###

def get_youtube_data(df):
    """
    Inputs a DataFrame with a column of YouTube video IDs and returns a
    DataFrame of YouTube data (e.g. view count) for each video. 
    Limited to 100 videos due to API's daily requests quota.
    """
    video_ids = df['yt_video_id'].dropna()

    video_list = []
    
    for video in video_ids:
        # Define API request
        request = yt.videos().list(
            part="contentDetails,id,snippet,statistics,recordingDetails,topicDetails",
            id=video)
        # Get data from API
        res = request.execute()
        
        # Extract relevant data 
        video_dict = {}
        try:
            video_dict['yt_video_id'] = res['items'][0]['id']
            video_dict['video_title'] = res['items'][0]['snippet']['title']
            video_dict['channel_title'] = res['items'][0]['snippet']['channelTitle']
            video_dict['publish_date'] = res['items'][0]['snippet']['publishedAt']
            video_dict['vid_duration'] = res['items'][0]['contentDetails']['duration']
            video_dict['view_count'] = res['items'][0]['statistics']['viewCount']        
            video_dict['thumbnail_standard'] = res['items'][0]['snippet']['thumbnails']['high']['url']
        except IndexError:
            continue
        try:
            video_dict['like_count'] = res['items'][0]['statistics']['likeCount']
        except:
            video_dict['like_count'] = None
        try:
            video_dict['comment_count'] = res['items'][0]['statistics']['commentCount']
        except:
            video_dict['comment_count'] = None
        try:
            video_dict['video_tags'] = res['items'][0]['snippet']['tags']
        except:
            video_dict['video_tags'] = None
        video_list.append(video_dict)
    
    # Create DataFrame
    video_data = pd.DataFrame(video_list)
    
    return video_data

# Get YouTube data
logging.info("\n---Executing 'get_youtube_data'...---\n")
youtube_data = get_youtube_data(song_data) 
logging.info("\n---DataFrame created: YouTube video data---\n")

# Make numbers human readable
def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

# Convert YouTube counts to human readable numbers, ex. 1256 to 1.2K
youtube_data['view_count_readable'] = None
youtube_data['like_count_readable'] = None
youtube_data['comment_count_readable'] = None

for i, row in youtube_data.iterrows():
    try:
        num = int(youtube_data['view_count'][i])
        formatted_num = human_format(num)
        youtube_data['view_count_readable'][i] = formatted_num
    except:
        continue
    try:
        num = int(youtube_data['like_count'][i])
        formatted_num = human_format(num)
        youtube_data['like_count_readable'][i] = formatted_num
    except:
        continue
    try:
        num = int(youtube_data['comment_count'][i])
        formatted_num = human_format(num)
        youtube_data['comment_count_readable'][i] = formatted_num
    except:
        continue

# Make video duration readable
def format_yt_duration(time_string):
    """
    Inputs a time string in format 'PT__H__M__S' from the YouTube API and outputs a time string in foramt HH:MM:SS.
    """
    no_letters = re.sub('P|T|S', '', time_string)
    dividers = re.sub('H|M', ':', no_letters)
    time_list = dividers.split(':')
    if len(time_list[0]) == 1:
        time_list[0] = '0' + time_list[0]
    try:
        if len(time_list[1]) == 1:
            time_list[1] = '0' + time_list[1]
    except:
        pass
    try:
        if len(time_list[2]) == 1: # If there is a value for hours
            time_list[2] = '0' + time_list[2]
    except IndexError:
        pass
        
    formatted_string = ':'.join(time_list[0:])
    
    return formatted_string

# Format YouTube duration values in DataFrame
youtube_data['vid_duration_readable'] = None

for i, row in youtube_data.iterrows():
    youtube_data['vid_duration_readable'][i] = format_yt_duration(youtube_data['vid_duration'][i])

# Make video publish date readable
def format_yt_date(datetime_string):
    """
    Inputs a datetime string for publish date from the YouTube API with format YYYY-MM-DDTHH:MM:SS and outputs 
    a date string in format YYYY-MM-DD.
    """
    date_time = datetime_string.split('T')
    date = date_time[0]
    return date

# Format video publish date
youtube_data['publish_date_readable'] = None

for i, row in youtube_data.iterrows():
    youtube_data['publish_date_readable'][i] = format_yt_date(youtube_data['publish_date'][i])

# Merge formatted YouTube DataFrame with main song DataFrame
youtube_song_data = song_data.merge(youtube_data, on="yt_video_id")
logging.info("\n---Merged Youtube data and Reddit top 150 songs DataFrames---\n")

# Make Reddit scores human readable
youtube_song_data['r_score_readable'] = None

for i, row in youtube_data.iterrows():
    try:
        num = int(youtube_song_data['r_score'][i])
        formatted_num = human_format(num)
        youtube_song_data['r_score_readable'][i] = formatted_num
    except:
        continue

# Export YouTube data CSV
youtube_song_data.to_csv("data/youtube_song_data_%s.csv" % (str(datetime.date.today())), index=None)
logging.info("\n---CSV created: 'data/youtube_song_data_%s'---\n" % (str(datetime.date.today())))