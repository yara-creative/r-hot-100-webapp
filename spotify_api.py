import pandas as pd
import datetime
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import emoji
from fuzzywuzzy import process
import warnings
from pandas.core.common import SettingWithCopyWarning
import logging
from user_credentials import S_CLIENT_ID, S_SECRET_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
# Set up warnings
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

# Import data
reddit_songs = pd.read_csv("data/reddit_top_150_songs_%s.csv" % (str(datetime.date.today())))
logging.critical("\n---DataFrame created from import 'reddit_top_150_songs_%s.csv'---\n" % (str(datetime.date.today())))

# Spotify API authentication
auth_manager = SpotifyClientCredentials(S_CLIENT_ID, S_SECRET_KEY)
sp = spotipy.Spotify(auth_manager=auth_manager)
logging.critical("\n---Connected to Spotify API---\n")


# Get track ID from Spotify links already found in the Reddit data
def get_track_id(string):
    """
    Inputs Spotify track link string and outputs the track ID.
    """
    track_id = re.sub('https\:\/\/open\.spotify\.com\/track\/|spotify\:track\:', '', string)
    
    return track_id

# Get track IDs
logging.info("\n---Executing 'get_track_id'...---\n")
reddit_songs['track_id'] = None

for i, row in reddit_songs[~(reddit_songs['sp_link'].isna())].iterrows():
    reddit_songs['track_id'][i] = get_track_id(reddit_songs['sp_link'][i])
logging.info("\n---Expanded Reddit DataFrame created: added Spotify Track ID column---\n")

###---Get Spotify raw data via Spotify API---###

def get_spotify_features(df):
    """
    Inputs a DataFrame with artist and song titles and returns a DataFrame
    of each song's Spotify audio and album features. If the song is not
    found via the Spotify API, it will return a blank row.
    """
    feats_list = []
    not_found_list = []
    
    for i, row in df.iterrows():
        query_post = str(df['r_post_song'][i]) + ' ' + str(df['r_post_artist'][i])
        query_media = str(df['r_media_song'][i]) + ' ' + str(df['r_media_artist'][i])
        queries = [query_post, query_media]
        
        for query in queries:
            if query != 'nan nan':
                search_result = sp.search(q=query, type='track')
                
                try: 
                    if df['track_id'][i] != None:
                        # Get track ID from Spotify links posted on Reddit
                        track_id = df['track_id'][i]
                    else:
                        # Get the track ID of the song
                        track_id = search_result['tracks']['items'][0]['id']

                    # Get audio features via Spotify API
                    features = sp.audio_features(tracks=track_id)
                    # Add audio features to features dictionary
                    feats_dict = features[0]

                    # Get album features via Spotify API
                    track_result = sp.track(track_id, market=None)
                    # Add results to features dictionary
                    feats_dict['sp_artwork_640px'] = track_result['album']['images'][0]['url'] 
                    date = pd.to_datetime(track_result['album']['release_date']) 
                    feats_dict['sp_release_date'] = date
                    feats_dict['sp_release_year'] = int(date.year)
                    feats_dict['sp_explicit'] = track_result['explicit'] 
                    feats_dict['sp_popularity'] = track_result['popularity'] 
                    feats_dict['sp_audio_preview'] = track_result['preview_url'] 

                    # Add song and artist to dictionary (allows merge with input df)
                    feats_dict['r_post_song'] = df['r_post_song'][i]
                    feats_dict['r_post_artist'] = df['r_post_artist'][i]
                    feats_dict['r_media_song'] = df['r_media_song'][i]
                    feats_dict['r_media_artist'] = df['r_media_artist'][i]
                    feats_dict['r_title'] = df['r_title'][i]
                    feats_dict['r_media_title'] = df['r_media_title'][i]
                    feats_dict['r_score'] = df['r_score'][i]
                    feats_dict['sp_link'] = df['sp_link'][i]

                    # Get Spotify song and artist name
                    feats_dict['sp_song'] = track_result['name'] # song name
                    feats_dict['sp_artist'] = track_result['artists'][0]['name'] # artist name

                    # Save song's dictionary in list
                    feats_list.append(feats_dict)

                except: #IndexError
                    # If the song was not found via the Spotify API search, save the song and artist to a list
                    not_found_dict = {}
                    not_found_dict['r_post_song'] = df['r_post_song'][i]
                    not_found_dict['r_post_artist'] = df['r_post_artist'][i]
                    not_found_list.append(not_found_dict)
                    continue
            
            else:                
                continue
            
    # Convert features list into DataFrames        
    features = pd.DataFrame(feats_list)    
    
    # Reindex columns so song, artist and track ID are first
    features = features.reindex(columns=(['sp_song', 'sp_artist', 'r_title', 'r_media_title', 'r_post_song', 
                                          'r_post_artist', 'r_media_song', 'r_media_artist', 'id', 'sp_link',
                                          'r_score', 'danceability', 
                                          'energy', 'key', 'loudness', 'mode', 'speechiness', 'acousticness', 
                                          'instrumentalness', 'liveness', 'valence', 'tempo', 'type', 'uri', 
                                          'track_href', 'analysis_url', 'duration_ms', 'time_signature', 
                                          'sp_artwork_640px', 'sp_release_date', 'sp_release_year', 
                                          'sp_explicit', 'sp_popularity', 'sp_audio_preview']))
    
    # Save to CSV to avoid extra API requests
    features.to_csv("data/spotify_raw_data_%s.csv" % (str(datetime.date.today())), index=None)
    
    # Convert not found list into DataFrames        
    not_found = pd.DataFrame(not_found_list)
    
    return features, not_found

# Get Spotify features
logging.info("\n---Executing 'get_spotify_features'...---\n")
spotify_feats, not_found_feats = get_spotify_features(reddit_songs)
logging.info("\n---CSV exported: 'spotify_raw_data_%s'---\n" % (str(datetime.date.today())))
logging.info("\n---DataFrame created: Spotify raw data for songs found---\n")
logging.info("\n---DataFrame created: list of songs not found on Spotify---\n")

# Drop duplicates from not found songs
not_found_feats = not_found_feats.drop_duplicates().reset_index(drop=True)

# Drop duplicate rows
spotify_feats.drop_duplicates(inplace=True) # drop general duplicates
spotify_feats.drop_duplicates(['sp_song', 'sp_artist'], inplace=True) # drop duplicate spotify search results

# Get DataFrame of songs where there were 2 different results
multiple_sp_results = spotify_feats[spotify_feats.duplicated('r_title', keep=False)]

# Remove duplicates DataFrame from main DataFrame
spotify_feats.drop(multiple_sp_results.index, inplace=True)

def get_the_right_song(df):
    """
    Inputs a DataFrame with multiple songs found on Spotify and chooses the one closest
    to the original Reddit post title or post media title.
    """
    df = pd.concat([df, pd.DataFrame([{'match_score': None}])], ignore_index=True)
    
    for i, row in df.iterrows():
        spotify_string = str(df['sp_artist'][i]) + '' + str(df['sp_song'][i]) # spotify result
        r_post_string = str(df['r_post_artist'][i]) + '' + str(df['r_post_song'][i]) # artist and song parsed from Reddit post title
        r_media_string = str(df['r_media_artist'][i]) + '' + str(df['r_media_song'][i]) # artist and song parsed from Reddit post media title
        
        # Compare Reddit post and post media title with Spotify result
        choices = [r_post_string, r_media_string]
        match_score = process.extractOne(spotify_string, choices)
        df['match_score'][i] = match_score[1]
    
    # Remove empty last row of DataFrame
    df.drop(df.tail(1).index, inplace=True)
    
    return df

# Get the best song match out of the duplicates
logging.info("\n---Executing 'get_the_right_song'...---\n")
match_scores = get_the_right_song(multiple_sp_results)
logging.info("\n---Cleaned up DataFrame created: only best match kept from duplicates---\n")

# Sort duplicates DataFrame by best song match and drop the other one
best_spotify_match = match_scores.sort_values('match_score', ascending=False).drop_duplicates('r_title').sort_index()
best_spotify_match.drop(columns=['match_score'], inplace=True)

# Reapply the best matched songs to the main DataFrame
spotify_feats_matched = pd.concat([spotify_feats, best_spotify_match])

# Resort song order by Reddit upvotes
spotify_feats_matched = spotify_feats_matched.sort_values('r_score', ascending=False)

# Reset index
spotify_feats_matched.reset_index(inplace=True, drop=True)

###---Merge with top songs DataFrame---###

# Merge Spotify DataFrame with top songs DataFrame
reddit_with_feats = reddit_songs.merge(spotify_feats_matched, on=['r_post_song', 'r_post_artist', 
                                                                  'r_score', 'r_title', 'r_media_title', 
                                                                  'r_media_song', 'r_media_artist'], 
                                                                   how='outer')
logging.info("\n---Merged Spotify and Reddit DataFrames---\n")


###---Troubleshoot Spotify query---###

def clean_spotify_query(string):
    """
    Inputs a string with 'artist name' + ' ' + 'song title' and returns
    a cleaned string (remove special characters etc.)
    """
    remove_emojis = ''.join(char for char in string if char not in emoji.UNICODE_EMOJI['en']) # remove emojis
    #to_ascii = unidecode(no_emojis) # replace non-ASCII characters with ASCII equivalent
    remove_non_ascii = remove_emojis.encode("ascii", "ignore") # remove non-ASCII characters (encoding)
    remove_non_ascii_2 = remove_non_ascii.decode() # remove non-ASCII characters (decoding)
    dash_to_space = re.sub('-', ' ', remove_non_ascii_2) # replace dashes with space, ex. inside artist name
    space_before_capitals = re.sub(r"(?<=\w)([A-Z])", r" \1", dash_to_space) # put space before capital letters, ex. HaHa = Ha Ha
    until_feat = re.findall('^.*?(?=feat\.|feat|ft\.|ft|f\/|f\.|Feat\.|Ft\.)', space_before_capitals) # keep text up to 'feat', i.e. featured artists
    
    if until_feat == []:
        return space_before_capitals # for titles without a featuring artist
    else:
        return until_feat[0] # for titles with a featuring artist

def remove_first_word(string):
    """
    Returns a string with the first word removed.
    """
    words = string.split()
    no_first_word = ' '.join(words[1:])
    
    return no_first_word

def separate_multiple_artists(string):
    """
    Inputs a string of a song artist. If there are multiple artist names,
    it will return a list of artist names. 
    """
    # Check for multiple artists by finding 'feat.', '&', ' X ', etc. in artist name
    artists = re.findall('&|\sx\s|\sX\s|\+|,|\sand\s|feat\.|feat|ft\.|ft|f\/|f\.|Feat\.|Ft\.', string)
    
    if artists != []: 
        return re.split('&|\sx\s|\sX\s|\+|,|\sand\s|feat\.|feat|ft\.|ft|f\/|f\.|Feat\.|Ft\.', string)
    
def get_spotify_artist_data(df):
    """
    Inputs a DataFrame with artist and song titles and returns a DataFrame
    of each artist's genres as listed on Spotify. If the song is not found
    via the Spotify API, it will return a blank row. 
    """
    artist_list = []
    not_found = []
    
    for i, row in df.iterrows():
        if df['sp_artist'][i] == None:
            query = str(df['r_artist_post'][i])
        else:
            query = df['sp_artist'][i]
        
        search_result = sp.search(q=query, type='artist')

        try:
            artist_dict = {}
            # Extract genre from search result
            genres = search_result['artists']['items'][0]['genres']
            # Format result into comma-separated string
            genres_no_brackets = re.sub('\[', '', str(genres))
            genres_no_brackets2 = re.sub('\]', '', genres_no_brackets)
            # Add artist genres to dictionary
            artist_dict['sp_genres'] = genres_no_brackets2
            # Add artist (not track) popularity to dictionary
            artist_dict['sp_artist_popularity'] = search_result['artists']['items'][0]['popularity']
            # Add Spotify follower count (does not incl. monthly listeners) to dictionary
            artist_dict['sp_follower_count'] = search_result['artists']['items'][0]['followers']['total']
            
            # Add Reddit post song and artist to dictionary (allows for merge with input df)
            artist_dict['r_post_song'] = df['r_post_song'][i]
            artist_dict['r_post_artist'] = df['r_post_artist'][i]
            artist_dict['r_media_song'] = df['r_media_song'][i]
            artist_dict['r_media_artist'] = df['r_media_artist'][i]
            artist_dict['r_title'] = df['r_title'][i]
            artist_dict['r_media_title'] = df['r_media_title'][i]
            artist_dict['r_score'] = df['r_score'][i]
            # Save artist dictionaries in list
            artist_list.append(artist_dict)
        
        except IndexError:
            # If the artist was not found via the Spotify API search, save the artist to a list
            not_found.append(query)
            continue
    
    # Convert genres to DataFrame
    artist_data = pd.DataFrame(artist_list)    
    # Reindex columns so song and artist are first
    artist_data = artist_data.reindex(columns=(['r_title', 'r_media_title', 'r_post_song', 'r_post_artist', 'r_media_song',
                                                'r_media_artist', 'r_score', 'sp_genres', 'sp_artist_popularity',
                                                'sp_follower_count']))
    
    return artist_data, not_found

# Get Spotify artist data
logging.info("\n---Executing 'get_spotify_artist_data'---\n")
spotify_artist_data, not_found_artists = get_spotify_artist_data(reddit_with_feats)
logging.info("\n---Expanded DataFrame created: added Spotify artist data")
logging.info("\n---DataFrame created: artists not found on Spotify---\n")


# Merge combined Spotify DataFrame with top songs DataFrame
song_data = reddit_with_feats.merge(spotify_artist_data, on=['r_post_song', 'r_post_artist', 
                                                                  'r_score', 'r_title', 'r_media_title', 
                                                                  'r_media_song', 'r_media_artist'], how='outer')
logging.info("\n---Merged expanded Spotify DataFrame and Reddit Top 150 DataFrames---\n")                                                                   


# Drop post_media_data as the dictionaries in the column are non-hashable to allow for dropping duplicates
song_data.drop(columns=['r_media_data'], inplace=True)
# Drop duplicate rows
song_data.drop_duplicates(inplace=True)

# Reset index
song_data.reset_index(inplace=True)
# Remove old index column
song_data = song_data.drop(columns=['index'])

# Export song data to CSV
song_data.to_csv("data/spotify_song_data_%s.csv" % (str(datetime.date.today())), index=None)
logging.info("\n---CSV created: 'spotify_song_data_%s'---\n" % (str(datetime.date.today())))                                                                   

###---Make Spotify-specific DataFrame---###

sp = song_data.loc[~(song_data['danceability'].isna())] # Get only tracks found on Spotify
sp = sp[0:100] # Get only the top 100 tracks
logging.info("\n---DataFrame created: top 100 songs found on Spotify---\n")                                                                   

# Convert value of keys from numbers to key names
keys_list = ['C', 'D', 'Db/C#', 'Eb', 'E', 'F', 'Gb/F#', 'G', 'Ab', 'A', 'Bb', 'B/Cb']    
sp['key'] = sp['key'].apply(lambda x: keys_list[int(x)])

# Make decimal values more readable
sp[['energy', 'danceability', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'r_upvote_ratio']] = (sp[['loudness', 'energy', 'danceability', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence']] * 100).round(2)

def format_ms(milliseconds):
    """
    Inputs a timestamp in milliseconds and returns a string in format MM:SS.
    """
    milliseconds = int(milliseconds)
    
    seconds = int((milliseconds/1000)%60)
    seconds = str(seconds)
    if len(seconds) != 2: 
        seconds = '0' + seconds
        
    minutes = int((milliseconds/(1000*60))%60)
    minutes = str(minutes)
    if len(minutes) != 2: 
        minutes = '0' + minutes

    return (minutes + ':' + seconds)

# Convert milliseconds to MM:SS
for i, row in sp.iterrows():
    sp['duration_ms'][i] = format_ms(sp['duration_ms'][i])

sp['sp_artist_popularity'].fillna(0, inplace=True) # fill NaNs
sp['sp_artist_popularity'] = sp['sp_artist_popularity'].astype(int) # convert to int

sp['tempo'] = sp['tempo'].astype(int) # convert to int

# Clean up 'explicit' values
sp['sp_explicit'] = sp['sp_explicit'].astype(str)

for i, row in sp.iterrows():
    if sp['sp_explicit'][i] == '1.0':
        sp['sp_explicit'][i] = 'True'
    elif sp['sp_explicit'][i] == '0.0':
        sp['sp_explicit'][i] = 'False'

# Format numbers to be human readable - from Stack Overflow rtaft
def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

# Convert Spotify follower count and upvotes to human readable number, ex. 1256 to 1.2K
sp['r_score_readable'] = None
sp['sp_follower_count_readable'] = None

for i, row in sp.iterrows():
    try:
        num = int(sp['sp_follower_count'][i])
        formatted_num = human_format(num)
        sp['sp_follower_count_readable'][i] = formatted_num
    except ValueError:
        continue
    try:
        num = int(sp['r_score'][i])
        formatted_num = human_format(num)
        sp['r_score_readable'][i] = formatted_num
    except ValueError:
        continue

sp = sp.reindex(columns=['r_title', 'r_post_song', 'r_post_artist', 'r_media_song',
                         'r_media_artist', 'sp_song', 'sp_artist', 'r_genres', 'sp_genres',
                         'r_media_title', 'r_post_date', 'r_upvote_ratio', 'r_score',
                            'bc_embed_link', 'link_source', 'sc_embed_link',
                           'sc_link', 'sp_link', 'yt_link', 'yt_video_id', 
                           'id', 'danceability', 'energy', 'key', 'loudness', 'mode',
                           'speechiness', 'acousticness', 'instrumentalness', 'liveness',
                           'valence', 'tempo', 'type', 'uri', 'track_href', 'analysis_url',
                           'duration_ms', 'time_signature', 'sp_artwork_640px', 'sp_release_date',
                           'sp_release_year', 'sp_explicit', 'sp_popularity', 'sp_audio_preview',
                            'sp_artist_popularity', 'sp_follower_count'])

# Export Spotify DataFrame to CSV
sp.to_csv("data/spotify_top_100_songs_%s.csv" % (str(datetime.date.today())), index=None)
logging.info("\n---CSV created: 'spotify_top_100_songs_%s'---\n" % (str(datetime.date.today())))                                                                   