import pandas as pd
import datetime
from IPython.display import HTML
import warnings
from pandas.core.common import SettingWithCopyWarning
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
# Set up warnings
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

# Import data
sp = pd.read_csv("data/spotify_top_100_songs_%s.csv" % (str(datetime.date.today())))
logging.critical("\n---DataFrame created from import 'spotify_top_100_songs_%s.csv'---\n" % (str(datetime.date.today())))
song_data = pd.read_csv("data/spotify_song_data_%s.csv" % (str(datetime.date.today())))
logging.critical("\n---DataFrame created from import 'spotify_song_data_%s.csv'---\n" % (str(datetime.date.today())))

# Get extreme audio features
def get_min_max_features(df):
    """
    Inputs DataFrame with Spotify audio features and outputs
    the songs with the min and max of each audio feature.
    """
    min_max_list = []
    
    audio_features = ['danceability', 'energy', 'loudness',
                        'speechiness', 'acousticness', 
                        'instrumentalness', 'liveness',
                        'valence', 'tempo']
    
    for feature in audio_features:
        min_max_dict = {'feature': feature,
                        'max_track': None,
                        'max_value': None,
                        'min_track': None,
                        'min_value': None,
                        'max_link': None,
                        'min_link': None,
                        'max_artwork': None,
                        'min_artwork': None}
                        
        min_max_dict['max_track'] = df['sp_song'][df[feature].idxmax()] + ' - ' + df['sp_artist'][df[feature].idxmax()]
        min_max_dict['max_value'] = df[feature][df[feature].idxmax()]
        min_max_dict['max_artwork'] = df['sp_artwork_640px'][df[feature].idxmax()]
        min_max_dict['max_link'] = "https://open.spotify.com/track/" + str(df['id'][df[feature].idxmax()])
        min_max_dict['min_track'] = df['sp_song'][df[feature].idxmin()] + ' - ' + df['sp_artist'][df[feature].idxmin()]
        min_max_dict['min_value'] = df[feature][df[feature].idxmin()]
        min_max_dict['min_artwork'] = df['sp_artwork_640px'][df[feature].idxmin()]
        min_max_dict['min_link'] = "https://open.spotify.com/track/" + str(df['id'][df[feature].idxmin()])
        min_max_list.append(min_max_dict)
    
    min_max = pd.DataFrame(min_max_list)
    
    return min_max

# Get min/max features
logging.info("\n---Executing 'get_min_max_features'...---\n")
min_max = get_min_max_features(sp) # get features
logging.info("\n---DataFrame created: songs with minimum and maximum Spotify feature values...---\n")

min_max.set_index('feature', inplace=True) # set index to feature
# Make values more readable
min_max[['max_value', 'min_value']] = (min_max[['max_value', 'min_value']] * 100).astype(int) 
min_max['max_value']['tempo'] = min_max['max_value']['tempo'] / 100
min_max['min_value']['tempo'] = min_max['min_value']['tempo'] / 100
min_max['max_value']['loudness'] = min_max['max_value']['loudness'] / 100
min_max['min_value']['loudness'] = min_max['min_value']['loudness'] / 100

# Combine artwork and Spotify links in same column and remove link column
# for i, row in min_max.iterrows():
#     min_max['max_artwork'][i] = str(min_max['max_artwork'][i]) + ", https://open.spotify.com/track/" + str(min_max['max_link'][i]) 
#     min_max['min_artwork'][i] = str(min_max['min_artwork'][i]) + ", https://open.spotify.com/track/" + str(min_max['min_link'][i]) 
# min_max.drop(['max_link', 'min_link'], axis=1, inplace=True)

# Export min and max audio feature tracks DataFrame to CSV
min_max.to_csv("data/spotify_extremes_%s.csv" % (str(datetime.date.today())), index=None)
logging.info("\n---CSV created: 'spotify_extremes_%s'---\n" % (str(datetime.date.today())))

###---Build DataFrame for Top 100 chart---###

# Format numbers to be human readable - from Stack Overflow rtaft
def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

# Spotify chart
chart_df = song_data.reindex(columns=(['sp_artwork_640px', 'id', 'sp_artist', 'sp_song', 'r_genres', 'r_score', 
                                        'sp_popularity', 'sp_artist_popularity', 'sp_follower_count',
                                        'sp_release_date']))
logging.info("\n---DataFrame created: chart for Reddit/overall top songs (not cleaned up)---\n")

# Combine artwork and Spotify links in same column and remove link column
for i, row in chart_df.iterrows():
    chart_df['sp_artwork_640px'][i] = str(chart_df['sp_artwork_640px'][i]) + ", https://open.spotify.com/track/" + str(chart_df['id'][i]) 

chart_df.drop('id', axis=1, inplace=True)

# Fill NaNs to transform float columns to int with unique string that can be removed later
chart_df.fillna('10101010101010', inplace=True)
# Convert float columns to int
chart_df[['r_score', 'sp_popularity', 'sp_artist_popularity', 'sp_follower_count']] = chart_df[['r_score', 'sp_popularity', 'sp_artist_popularity', 'sp_follower_count']].astype(int)
# Replace unique NaN replacement string with dash indicating no data
chart_df.replace(to_replace=10101010101010, value='-', inplace=True)
chart_df.replace(to_replace='10101010101010', value='-', inplace=True)

# Convert Spotify follower count to human readable number, ex. 1256 to 1.2K
for i, row in chart_df.iterrows():
    try:
        num = int(chart_df['sp_follower_count'][i])
        formatted_num = human_format(num)
        chart_df['sp_follower_count'][i] = formatted_num
    except ValueError:
        continue
    try:
        num = int(chart_df['r_score'][i])
        formatted_num = human_format(num)
        chart_df['r_score'][i] = formatted_num
    except ValueError:
        continue
        
# Rename columns
chart_df.rename(columns={'sp_artwork_640px': 'Artwork', 'sp_artist': 'Artist', 'sp_song': 'Song', 'r_genres': 'Genre(s) on Reddit',
                            'r_score': 'Reddit upvotes', 'sp_popularity': 'Spotify song popularity (0-100)', 
                            'sp_follower_count': 'Spotify artist follower count',   
                            'sp_artist_popularity': 'Spotify artist popularity (0-100)', 
                            'sp_release_date': 'Released on Spotify'}, inplace=True)

chart_df.index += 1 
logging.info("\n---Cleaned up DataFrame: chart for Reddit/overall top songs---\n")

# Make charts
chart_top_100 = chart_df[:100]
logging.info("\n---DataFrame created: chart for Reddit/overall top 100 songs---\n")
chart_sp_top_100 = chart_df.loc[chart_df['Spotify song popularity (0-100)'] != '-'][:100]
logging.info("\n---DataFrame created: chart for Spotify top 100 songs---\n")

# Export chart data DataFrames to CSV file
chart_top_100.to_csv("data/chart_reddit_%s.csv" % (str(datetime.date.today())), index=None) # General Top 100
logging.info("\n---CSV created: 'chart_reddit_%s'---\n" % (str(datetime.date.today())))
chart_sp_top_100.to_csv("data/chart_spotify_%s.csv" % (str(datetime.date.today())), index=None) # Spotify Top 100
logging.info("\n---CSV created: 'chart_spotify_%s'---\n" % (str(datetime.date.today())))