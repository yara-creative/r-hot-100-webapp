import pandas as pd
import datetime
import googleapiclient.discovery
import googleapiclient.errors
import re
from IPython.display import HTML
import warnings
from pandas.core.common import SettingWithCopyWarning
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
# Set up warnings
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

# Import data
youtube_song_data = pd.read_csv("data/youtube_song_data_%s.csv" % (str(datetime.date.today())))
logging.critical("\n---DataFrame created from import 'youtube_song_data_%s.csv'---\n" % (str(datetime.date.today())))

###---Create YouTube chart---###

youtube_chart = youtube_song_data.reindex(columns=['thumbnail_standard', 'yt_link',
                                                   'video_title', 'channel_title', 'r_genres',
                                                   'r_score_readable', 'view_count_readable', 
                                                   'like_count_readable',
                                                   'comment_count_readable',
                                                   'vid_duration_readable',
                                                   'publish_date_readable'])
logging.info("\n---DataFrame created: chart for YouTube songs (not cleaned up)---\n")

# Combine thumbnail and YouTube links in one column
for i, row in youtube_chart.iterrows():
    youtube_chart['thumbnail_standard'][i] = str(youtube_chart['thumbnail_standard'][i]) + ", " + str(youtube_chart['yt_link'][i]) 

youtube_chart.drop('yt_link', axis=1, inplace=True)

youtube_chart.rename(columns={'thumbnail_standard': 'Thumbnail',
                              'video_title': 'Video Title', 'channel_title': 'Channel',
                              'r_genres': 'Genre(s) on Reddit',
                              'r_score_readable': 'Reddit upvotes', 'view_count_readable': 'Views', 
                              'like_count_readable': 'Likes',
                              'comment_count_readable': 'Comments',
                              'vid_duration_readable': 'Duration',
                              'publish_date_readable': 'Date published'}, inplace=True)

# Start index numbering at 1
youtube_chart.index += 1 

# Define and export YouTube chart
youtube_chart_100 = youtube_chart[:100]
logging.info("\n---Cleaned up DataFrame created: chart for top 100 YouTube songs---\n")

youtube_chart_100.to_csv("data/chart_youtube_%s.csv" % (str(datetime.date.today())), index=None)
logging.info("\n---CSV created: 'data/chart_youtube_%s'---\n" % (str(datetime.date.today())))