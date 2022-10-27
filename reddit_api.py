import pandas as pd
import praw
from youtube_title_parse import get_artist_title
import datetime
import re
import emoji
import warnings
from pandas.core.common import SettingWithCopyWarning
import logging
from user_credentials import R_CLIENT_ID, R_SECRET_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
# Set up warnings
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

# Reddit API authentication
rt = praw.Reddit(
    client_id=R_CLIENT_ID,
    client_secret=R_SECRET_KEY,
    user_agent='scrape-songs/0.0.1'
)
logging.critical("\n---Connected to Reddit API---\n")

###---Scrape raw data using Reddit API---###

def get_reddit_data(subreddit_name):
    """
    Inputs string for a subreddit relating to music recommendations
    and outputs a DataFrame with the data of 150 media posts. 
    Also saves raw data as a csv file.
    """
    df = pd.DataFrame()

    for post in rt.subreddit(subreddit_name).hot(limit=500):
        if post.media != None and post.over_18 == False and post.media['type'] in ('youtube.com', 'open.spotify.com'): # Include only posts with media from YouTube or Spotify and exclude NSFW posts
            if len(df) < 150:
                df = pd.concat([df, pd.DataFrame([{
                    'r_title': post.title,
                    'r_media_title': post.media['oembed']['title'],
                    'r_post_date': datetime.datetime.utcfromtimestamp(post.created_utc),
                    'r_upvote_ratio': post.upvote_ratio,
                    'r_score': post.score,
                    'r_media_data': post.media, # raw media data 
                    }])], ignore_index=True)
 
    # Format date to keep only YYYY:MM:DD
    df['r_post_date'] = df['r_post_date'].dt.date
    
    # Save data as a CSV file to avoid making extra API requests
    df.to_csv("data/reddit_r-%s_raw_data_%s.csv" % (subreddit_name, str(datetime.date.today())))
    return df

# Get reddit data for two of the most popular music subreddits
logging.info("\n---Executing 'get_reddit_data'...---\n")
r_music = get_reddit_data('music')
r_listentothis = get_reddit_data('listentothis')
logging.info("\n---DataFrame created: Reddit raw data---\n")
logging.info("\n---CSV exported: 'data/reddit_r-music_raw_data_%s.csv'---\n" % (str(datetime.date.today())))
logging.info("\n---CSV exported: 'data/reddit_r-listentothis_raw_data_%s.csv'---\n" % (str(datetime.date.today())))

# Combine DataFrames of the two subreddits
reddit = pd.concat([r_music, r_listentothis])
reddit.reset_index(inplace=True, drop=True)

###---Extract artist name, song title and genre---###

def clean_title(title):
    """
    Inputs Reddit post title string and outputs the
    string up to the first bracket/parentheses. 
    """
    try:
        title_no_emojis = emoji.replace_emoji(title)
        title_until_bracket = re.findall('^.*?(?=\s\[|\(|\{)', title_no_emojis)
        title_cleaned = re.sub("'", '', title_until_bracket[0]).lstrip()
    except:
        title_cleaned = title
        
    return title_cleaned

def get_reddit_genres(string):
    genres = re.findall('\[(.*?)\]', string) # get words between brackets
    genres_words = ', '.join(genres)
    lowercase = genres_words.lower()
    rnb = re.sub('r \& b', 'r&b', lowercase)
    hip_hop = re.sub('hip\-hop', 'hip hop', rnb)
    comma_separator = re.sub('\/|\||\ & ', ', ', hip_hop)
    no_comma_spaces = re.sub(' ,', ',', comma_separator)
    no_extra_spaces = re.sub('  |   ', ' ', no_comma_spaces)
    try:
        no_symbols = re.sub('?', '', no_extra_spaces)
        return no_symbols
    except:
        return no_extra_spaces

def get_reddit_artist_song_genres(df):
    """
    Inputs DataFrame of raw data from Reddit and outputs a new expanded
    DataFrame with columns for the Reddit post title's artist name and song title,
    post media title's artist name and song title and genres.
    """
    df = df.reindex(columns = df.columns.tolist() + ['r_post_artist','r_post_song', 'r_media_artist',
                                                    'r_media_song', 'r_genres'])
    
    for i, row in df.iterrows():
        title = clean_title(df['r_title'][i])
        media_title = clean_title(df['r_media_title'][i])
        
        # Try extracting artist and song from post title
        if type(title) is str and get_artist_title(title):
            try:
                artist, song = get_artist_title(title) # get artist and song
                df['r_post_artist'][i] = artist
                df['r_post_song'][i] = song
            except:    
                continue
        
        # Try extracting artist and song from post media title
        if type(media_title) is str and get_artist_title(media_title):
            try:
                artist, song = get_artist_title(media_title) # get artist and song
                df['r_media_artist'][i] = artist
                df['r_media_song'][i] = song
            except:    
                continue
            
        # Add genres to DataFrame 
        if type(df['r_title'][i]) is str:
            try:
                df['r_genres'][i] = get_reddit_genres(df['r_title'][i])
            except:
                continue
        else:
            continue
        
    return df

# Get song data from Reddit
logging.info("\n---Executing 'get_reddit_artist_song_genres'...---\n")
reddit_songs = get_reddit_artist_song_genres(reddit)
logging.info("\n---Expanded DataFrame created: added Reddit song/artist/genre from post and media titles---\n")

###---Extract media links from raw data---###

def url_to_ascii(url):
    """
    Inputs URL string with URL encoding and returns string
    where with URL converted to ASCII.
    """
    colon = re.sub('%3A', ':', url)
    slash = re.sub('%2F', '/', colon)
    equals_sign = re.sub('%3D', '=', slash) 
    
    return equals_sign

def get_youtube_link(post_media_dict):
    """
    Inputs dictionary of 'post.media' scraped from Reddit and outputs the YouTube link.
    """
    media = post_media_dict
    
    if 'url' in media['oembed']: # applies for embedded YouTube video link in post
        direct_link = media['oembed']['url']
    else: # applies for direct YouTube video link in post
        html = media['oembed']['html'] # navigate to string containing embed link
        src = re.findall('src="(\S+)"', html) # extract embed link
        src = src[0] # convert list to string
        no_suffix = re.sub('\?feature+\S+', '', src) # remove embed suffix (type 1)    
        no_suffix1 = re.sub('\?start+\S+', '', no_suffix) # remove embed suffix (type 2)
        no_suffix2 = re.sub('\?list+\S+', '', no_suffix1) # remove embed suffix (type 3)
        direct_link = re.sub('/embed/', '/watch?v=', no_suffix2) # replace embed with watch to get link
        
    # Get video ID
    video_id = re.sub('\S+v=', '', direct_link) 
    
    return direct_link, video_id

def get_spotify_link(post_media_dict):
    """
    Inputs dictionary of 'post.media' scraped from Reddit and outputs the Spotify link.
    """
    media = post_media_dict
    html = media['oembed']['html'] # navigate to string containing link
    src = re.findall('src="(\S+)"', html)
    try:
        src2 = re.findall('src=(\S+)', src[0]) # in case there is an src link another layer down
    except: 
        src2 = src
    converted_url = url_to_ascii(src2[0]) # convert URL symbols to ASCII
    no_embed = re.sub('embed/', '', converted_url) # remove 'embed' part of link
    direct_link = re.findall('^.*?(?=\%3F)', no_embed) # parse url string to get link 
    
    return direct_link[0]

def get_soundcloud_links(post_media_dict):
    """
    Inputs dictionary of 'post.media' scraped from Reddit and outputs
    the SoundCloud direct link and embed link.
    """
    media = post_media_dict
    html = media['oembed']['html'] # navigate to string containing link
    src = re.findall('src="(\S+)"', html) 
    try:
        src2 = re.findall('src=(\S+)', src[0]) # in case there is an src link another layer down
    except: 
        src2 = src
    embed_link = url_to_ascii(src2[0]) # convert URL symbols to ASCII
    # Format to get direct link
    split_char = re.sub('&', '%3F', embed_link) # replace '&' with characters to split on
    split_str = re.findall('\S+url=(\S+)', split_char) # extract url string
    direct_link = split_str[0].split('%3F')[0] # split url string to get link
    
    return direct_link, embed_link

def get_bandcamp_link(post_media_dict):
    """
    Inputs dictionary of 'post.media' scraped from
    Reddit and outputs the Bandcamp embed link.
    """
    media = post_media_dict
    html = media['oembed']['html'] # navigate to string containing link
    src = re.findall('src="(\S+)"', html)
    embed_link = url_to_ascii(src[0]) # convert URL symbols to ASCII
    
    return embed_link

def get_reddit_media_links(reddit_df):
    """
    Inputs a DataFrame of raw Reddit data and returns a new expanded DataFrame
    with the media link for each post. 
    Supported links are from YouTube, Spotify, SoundCloud and Bandcamp.
    """
    # Add columns to DataFrame for media links
    df = pd.concat([reddit_df, pd.DataFrame([{'link_source': None,
                            'sp_link': None, # Spotify
                            'yt_link': None, # YouTube
                            'yt_video_id': None,
                            'sc_link': None, # SoundCloud
                            'sc_embed_link': None,
                            'bc_embed_link': None, # Bandcamp
                            }])], ignore_index=True)
    
    for i, row in df.iterrows():
        media = df['r_media_data'][i]
        
        try:
            # Posts with Spotify media
            if media['oembed']['provider_url'] == 'https://spotify.com':
                direct_link = get_spotify_link(media) # extract Spotify link
                df['sp_link'][i] = direct_link # append direct link to DataFrame
                df['link_source'][i] = 'spotify'
                
            # Posts with YouTube media
            elif media['oembed']['provider_url'] == 'https://www.youtube.com/': 
                direct_link, video_id = get_youtube_link(media) # extract YouTube link
                df['yt_link'][i] = direct_link # append direct link to DataFrame
                df['yt_video_id'][i] = video_id # append video ID to DataFrame
                df['link_source'][i] = 'youtube'

            # Posts with SoundCloud media
            elif media['oembed']['provider_url'] == 'https://soundcloud.com':
                direct_link, embed_link = get_soundcloud_links(media) # extract SoundCloud links
                df['sc_link'][i] = direct_link # append direct link to DataFrame
                df['sc_embed_link'][i] = embed_link # append embed link to DataFrame
                df['link_source'][i] = 'soundcloud'
                
            # Posts with Bandcamp media
            elif media['oembed']['provider_url'] == 'http://bandcamp.com':
                embed_link = get_bandcamp_link(media) # extract Bandcamp link
                df['bc_embed_link'][i] = embed_link # append embed link to DataFrame
                df['link_source'][i] = 'bandcamp'
            else:
                df['link_source'][i] = 'other'
                continue
                
        except Exception as e:
            print(e, media) # one NaN value is expected due to empty row
            continue
            
    # Remove rows where link source is 'other'
    df.drop(df[df['link_source'] == 'other'].index, inplace=True)
    # Remove empty last row of DataFrame
    df.drop(df.tail(1).index, inplace=True)
    # Reset index
    df.reset_index(inplace=True, drop=True)
    
    return df

# Get media links
logging.info("\n---Executing 'get_reddit_media_links'...---\n")
reddit_songs_links = get_reddit_media_links(reddit_songs)
logging.info("\n---Expanded DataFrame created: added Reddit media links---\n")

###---Get top 150 songs (incl. buffer)---###

def top_150_songs(df):
    """
    Inputs a DataFrame with Reddit data and outputs a DataFrame of 
    150 Reddit posts sorted according to the post score.
    """
    # Sort songs according to the Reddit post score (number of upvotes)
    df = df.sort_values('r_score', ascending=False)
    top_songs = df[0:150] # keep only 150 posts
    top_songs.reset_index(inplace=True, drop=True) # reset index
    
    return top_songs

# Get top 150 songs
logging.info("\n---Executing 'top_150_songs'...---\n")
top_songs = top_150_songs(reddit_songs_links)
logging.info("\n---Cleaned up DataFrame created: top 150 Reddit songs sorted by upvotes---\n")

# Export top 150 songs (50-song buffer for Spotify search)
top_songs.to_csv("data/reddit_top_150_songs_%s.csv" % (str(datetime.date.today())), index=False)
logging.info("\n---CSV exported: 'reddit_top_150_songs_%s'---\n" % (str(datetime.date.today())))