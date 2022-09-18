#from secrets import randbelow
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
#from sklearn.preprocessing import MinMaxScaler
import streamlit as st
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
import pandas as pd
import datetime
from datetime import datetime as dt, timedelta
import os
import re
from IPython.display import HTML
import warnings
from pandas.core.common import SettingWithCopyWarning
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
# Set up warnings
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

###---Import data---###

# Get the latest files based on date in the filename 
files_list = os.listdir(str(os.getcwd()) + '/data')

def get_max_date(list):
        """
        Inputs a list of filenames in the 'data' directory and returns the latest date found in the filenames.
        """
        max_date = datetime.date.today() - timedelta(days=365)

        for filename in files_list:
                match = re.findall('\d{4}-\d{2}-\d{2}', filename)
                try:
                        date = dt.strptime(match[0], '%Y-%m-%d').date()
                        if date > max_date:
                                max_date = date
                        else:
                                continue
                except:
                        continue
                
        return str(max_date)

latest_date = get_max_date(files_list)

# Embed links for playlists
from spotify_links import spotify_embed_src, spotify_playlist_link
logging.critical("\n---Imported Spotify embed SRC string---\n")
from youtube_links import youtube_embed_src1, youtube_embed_src2, playlist_link_1, playlist_link_2
logging.critical("\n---Imported YouTube embed SRC and link strings---\n")

# REDDIT
top_songs = pd.read_csv('data/reddit_top_150_songs_%s.csv' % (latest_date))
logging.critical("\n---DataFrame created from import 'reddit_top_150_songs_%s.csv'---\n" % (latest_date))
# SPOTIFY
song_data = pd.read_csv('data/spotify_song_data_%s.csv' % (latest_date))
logging.critical("\n---DataFrame created from import 'spotify_song_data_%s.csv'---\n" % (latest_date))
sp = pd.read_csv('data/spotify_top_100_songs_%s.csv' % (latest_date))
logging.critical("\n---DataFrame created from import 'spotify_top_100_song_%s.csv'---\n" % (latest_date))
min_max = pd.read_csv('data/spotify_extremes_%s.csv' % (latest_date))
logging.critical("\n---DataFrame created from import 'spotify_extremes_%s.csv'---\n" % (latest_date))

# Charts
chart_top_100 = pd.read_csv('data/chart_reddit_%s.csv' % (latest_date))
logging.critical("\n---DataFrame created from import 'chart_reddit_%s.csv'---\n" % (latest_date))
chart_spotify_top_100 = pd.read_csv('data/chart_spotify_%s.csv' % (latest_date))
logging.critical("\n---DataFrame created from import 'chart_spotify_%s.csv'---\n" % (latest_date))
chart_youtube_top_100 = pd.read_csv('data/chart_youtube_%s.csv' % (latest_date))
logging.critical("\n---DataFrame created from import 'chart_youtube_%s.csv'---\n" % (latest_date))

####---Configure Streamlit---###

# Configuration (browser tab info, layout)
logging.info("\n---Configuring Streamlit...---\n")

st.set_page_config(
    page_title="r/ Daily Hot 100",
    page_icon="🔥",
    layout="wide",
)
 
# with st.sidebar:
#     choose = option_menu("r/ Daily Hot 100", ["Playlists", "Charts",
#                         "Today's Extremes", "Dashboard", "Your Feedback"],
#                          icons=['boombox', 'bar-chart', 'exclamation-circle', 'speedometer', 'chat-text'],
#                          menu_icon="music-note-beamed",
#                          default_index=0,
#                          styles={
#         "container": {"padding": "5!important", "background-color": "#efefef"},
#         "icon": {"color": "#222222", "font-size": "16px"}, 
#         "nav-link": {"color": "#222222", "font-size": "16px", "text-align": "left",
#         "margin":"0px", "--hover-color": "#DA0037"},
#         "nav-link-selected": {"color": "#ffffff", "background-color": "#DA0037"},
#     })

logging.info("\n---Streamlit configured---\n")

###---Pages---###

st.title("🔥 r/ Daily Hot 100")
st.subheader("Discover today's hottest songs recommended on Reddit.")
st.markdown("New playlists and charts generated every day from song posts on [r/Music](%s) and [r/ListenToThis](%s)." % ("https://www.reddit.com/r/Music/", "https://www.reddit.com/r/ListenToThis/"))

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Playlists", "Charts", "Today's Extremes", "Dashboard", "Feedback"])

###---Playlist pages---###
with tab1:

    playlist1, playlist2 = st.tabs(["Spotify Playlist", "YouTube Playlist"])

    with playlist1:
        logging.info("\n---Setting up Spotify Playlist page...---\n")
        st.subheader("Spotify Playlist")
        st.markdown("Today's most upvoted songs on [r/Music](%s) and [r/ListenToThis](%s) that were found on Spotify." % ("https://www.reddit.com/r/Music/", "https://www.reddit.com/r/ListenToThis/"))
        st.markdown("[**Save the playlist – new songs every day**](%s)" % (spotify_playlist_link))
        components.iframe(src=spotify_embed_src, width=380, height=640, scrolling=False)
        logging.info("\n---Spotify Playlist page ready---\n")

    with playlist2:
        logging.info("\n---Setting up YouTube Playlist page...---\n")
        st.subheader("YouTube Playlists")
        st.markdown("Today's most upvoted songs on [r/Music](%s) and [r/ListenToThis](%s) that were found on YouTube." % ("https://www.reddit.com/r/Music/", "https://www.reddit.com/r/ListenToThis/"))        
        st.markdown("##### **Pt.1 (Tracks 1 – 50)**")
        components.iframe(src=youtube_embed_src1,
                        width=560, height=315, scrolling=False)
        st.write('No video? Watch on [YouTube](%s).' % (playlist_link_1))
        
        st.markdown("##### **Pt.2 (Tracks 51 – 100)**")
        components.iframe(src=youtube_embed_src2,
                        width=560, height=315, scrolling=False)
        st.write('No video? Watch on [YouTube](%s).' % (playlist_link_2))
        logging.info("\n---YouTube Playlist page ready---\n")

###---Chart pages---###
with tab2: 
    
    # Format HTML images for charts
    def image_url_to_html(string):
        """
        Inputs url string for an image and returns image html string.
        """
        url, hyperlink = string.split(', ')

        return '<a href="' + hyperlink + '"><img src="'+ url + '" style=max-height:124px;"></a>'


    chart1, chart2 = st.tabs(["Spotify Chart", "YouTube Chart"])

    with chart1:
        logging.info("\n---Setting up Spotify Chart page...---\n")
        st.subheader("r/ Daily Hot 100 – Spotify Chart")
        st.markdown("Today's most upvoted songs in 'Hot' on [r/Music](%s) and [r/ListenToThis](%s) that were found on Spotify." % ("https://www.reddit.com/r/Music/", "https://www.reddit.com/r/ListenToThis/"))
        # HTML view of pandas DataFrame chart
        chart_spotify_top_100.index += 1 # Start chart index at 1
        # Convert DataFrame to html to display images
        st.write(HTML(chart_spotify_top_100.to_html(escape=False, 
                        formatters=dict(Artwork=image_url_to_html))))
        logging.info("\n---Spotify Chart page ready---\n")

    with chart2:
        logging.info("\n---Setting up YouTube Chart page...---\n")
        st.subheader("r/ Daily Hot 100 – YouTube Chart")
        st.markdown("Today's most upvoted songs in 'Hot' on [r/Music](%s) and [r/ListenToThis](%s) that were found on YouTube." % ("https://www.reddit.com/r/Music/", "https://www.reddit.com/r/ListenToThis/"))
        # HTML view of pandas DataFrame chart
        chart_youtube_top_100.index += 1 # Start chart index at 1
        # Convert DataFrame to html to display images
        st.write(HTML(chart_youtube_top_100.to_html(escape=False, 
                        formatters=dict(Thumbnail=image_url_to_html))))
        logging.info("\n---YouTube Chart page ready---\n")

###---Extremes page---###
with tab3:
    logging.info("\n---Setting up Today's Extremes page...---\n")
    
    st.subheader("Today's Extremes")
    st.markdown("Every track on Spotify is measured for audio features like danceability and mood. Check out the most extreme tracks on today's Spotify Hot 100.") 

    max1, min1 = st.columns([0.5, 0.5])
    with max1:
        # Valence / Happiness
        # Max
        st.markdown("##### Happiest track: %s" % (min_max['max_track'][7]))
        st.markdown("###### Valence: %s / 100" % (min_max['max_value'][7]))
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['max_link'][7]), str(min_max['max_artwork'][7])), 
                        unsafe_allow_html=True)
    with min1:
        # Min 
        st.markdown(f"##### Least happy track: {min_max['min_track'][7]}")
        st.markdown(f"###### Valence: {min_max['min_value'][7]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['min_link'][7]), str(min_max['min_artwork'][7])), 
                        unsafe_allow_html=True)

    max2, min2 = st.columns([0.5, 0.5])
    with max2:
        # Danceability
        # Max
        st.markdown(f"##### Most danceable: {min_max['max_track'][0]}")
        st.markdown(f"###### Danceability: {min_max['max_value'][0]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['max_link'][0]), str(min_max['max_artwork'][0])), 
                        unsafe_allow_html=True)
    with min2:
        # Min 
        st.markdown(f"##### Least danceable: {min_max['min_track'][0]}")
        st.markdown(f"###### Danceability: {min_max['min_value'][0]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['min_link'][0]), str(min_max['min_artwork'][0])), 
                        unsafe_allow_html=True)
    
    max3, min3 = st.columns([0.5, 0.5])
    with max3:
        # Tempo
        # Max
        st.markdown(f"##### Fastest tempo: {min_max['max_track'][8]}")
        st.markdown(f"###### Tempo: {min_max['max_value'][8]} bpm")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['max_link'][8]), str(min_max['max_artwork'][8])), 
                        unsafe_allow_html=True)
    with min3:
        # Min 
        st.markdown(f"##### Slowest tempo: {min_max['min_track'][8]}")
        st.markdown(f"###### Tempo: {min_max['min_value'][8]} bpm")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['min_link'][8]), str(min_max['min_artwork'][8])), 
                        unsafe_allow_html=True)
        
    max4, min4 = st.columns([0.5, 0.5])
    with max4:
        # Energy
        # Max
        st.markdown(f"##### Most energetic: {min_max['max_track'][1]}")
        st.markdown(f"###### Energy: {min_max['max_value'][1]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['max_link'][1]), str(min_max['max_artwork'][1])), 
                        unsafe_allow_html=True)
    with min4:
        # Min 
        st.markdown(f"##### Least energetic: {min_max['min_track'][1]}")
        st.markdown(f"###### Energy: {min_max['min_value'][1]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['min_link'][1]), str(min_max['min_artwork'][1])), 
                        unsafe_allow_html=True)
        
    max5, min5 = st.columns([0.5, 0.5])
    with max5:
        # Loudness
        # Max
        st.markdown(f"##### Loudest: {min_max['max_track'][2]}")
        st.markdown(f"###### Loudness: {min_max['max_value'][2]} dB")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['max_link'][2]), str(min_max['max_artwork'][2])), 
                        unsafe_allow_html=True)
    with min5:
        # Min 
        st.markdown(f"##### Softest: {min_max['min_track'][2]}")
        st.markdown(f"###### Loudness: {min_max['min_value'][2]} dB")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['min_link'][2]), str(min_max['min_artwork'][2])), 
                        unsafe_allow_html=True)

    max6, min6 = st.columns([0.5, 0.5])
    with max6:
        # Speechiness
        # Max
        st.markdown(f"##### Most talky: {min_max['max_track'][3]}")
        st.markdown(f"###### Speechiness: {min_max['max_value'][3]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['max_link'][3]), str(min_max['max_artwork'][3])), 
                        unsafe_allow_html=True)
    with min6:
        # Min 
        st.markdown(f"##### Least talky: {min_max['min_track'][3]}")
        st.markdown(f"###### Speechiness: {min_max['min_value'][3]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['min_link'][3]), str(min_max['min_artwork'][3])), 
                        unsafe_allow_html=True)

    max7, min7 = st.columns([0.5, 0.5])
    with max7:
        # Acousticness
        # Max
        st.markdown(f"##### Most acoustic: {min_max['max_track'][4]}")
        st.markdown(f"###### Acousticness: {min_max['max_value'][4]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['max_link'][4]), str(min_max['max_artwork'][4])), 
                        unsafe_allow_html=True)
    with min7:
        # Min 
        st.markdown(f"##### Least acoustic: {min_max['min_track'][4]}")
        st.markdown(f"###### Acousticness: {min_max['min_value'][4]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['min_link'][4]), str(min_max['min_artwork'][4])), 
                        unsafe_allow_html=True)
        
    max8, min8 = st.columns([0.5, 0.5])
    with max8:
        # Instrumentalness
        # Max
        st.markdown(f"##### Most instrumental: {min_max['max_track'][5]}")
        st.markdown(f"###### Instrumentalness: {min_max['max_value'][5]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['max_link'][5]), str(min_max['max_artwork'][5])), 
                        unsafe_allow_html=True)
    with min8:
        # Min 
        st.markdown(f"##### Least instrumental: {min_max['min_track'][5]}")
        st.markdown(f"###### Instrumentalness: {min_max['min_value'][5]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['min_link'][5]), str(min_max['min_artwork'][5])), 
                        unsafe_allow_html=True)

    max9, min9 = st.columns([0.5, 0.5])
    with max9:
        # Liveness
        # Max
        st.markdown(f"##### Most likely recorded live: {min_max['max_track'][6]}")
        st.markdown(f"###### Liveness: {min_max['max_value'][6]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['max_link'][6]), str(min_max['max_artwork'][6])), 
                        unsafe_allow_html=True)
    with min9:
        # Min 
        st.markdown(f"##### Least likely recorded live: {min_max['min_track'][6]}")
        st.markdown(f"###### Liveness: {min_max['min_value'][6]} / 100")
        st.markdown('''<a href=%s><img src=%s width="380" /></a>''' 
                        % (str(min_max['min_link'][6]), str(min_max['min_artwork'][6])), 
                        unsafe_allow_html=True)
    logging.info("\n---Today's Extremes page ready---\n")


###---Dashboard page---###
with tab4:

    logging.info("\n---Setting up Dashboard page...---\n")
    st.title("Dashboard")
    st.markdown("##### Dive into the stats behind today's Hot 100 songs and artists.")

    col1, col2 = st.columns([0.3, 0.7])
    with col1:
        logging.info("\n---Displaying Average values---\n")
        st.markdown("#### Today's averages: ")

        st.markdown(f"### {int(sp['r_score'].median())} upvotes")
        st.markdown("Reddit popularity (median)")

        st.markdown(f"### {sp['sp_popularity'].mean()} / 100")
        st.markdown("Spotify popularity")
        
        st.markdown(f"### {int(sp['valence'].mean())} / 100")
        st.markdown("Valence (song happiness)")
        
        st.markdown(f"### {int(sp['tempo'].mean())} bpm")
        st.markdown("Tempo")
        
        st.markdown(f"### {int(sp['energy'].mean())} / 100")
        st.markdown("Energy")

        st.markdown(f"### {int(sp['danceability'].mean())} / 100")
        st.markdown("Danceability")
        
        st.markdown(f"### {int(sp['loudness'].mean())} dB")
        st.markdown("Loudness")

        st.markdown(f"### {int(sp['speechiness'].mean())} / 100")
        st.markdown("Speechiness (talking vs. melodic)")

        st.markdown(f"### {int(sp['acousticness'].mean())} / 100")
        st.markdown("Acousticness")

        st.markdown(f"### {int(sp['instrumentalness'].mean())} / 100")
        st.markdown("Instrumentalness (instruments vs. vocals)")

        st.markdown(f"### {int(sp['liveness'].mean())} / 100")
        st.markdown("Liveness (live  audience detection)")

    with col2:
        # Scatterplot Reddit upvotes by mood
        logging.info("\n---Displaying Scatterplot Reddit upvotes by mood...---\n")
        fig1 = px.scatter(sp, x='tempo', y='valence', color='danceability',
                        hover_name="r_title", hover_data=["r_genres", "sp_popularity"],
                        size="r_score", size_max=55,
                        title='Popularity of song by mood, i.e. valence vs. tempo (size shows popularity)',
                        labels={
                            "sp_popularity": "Spotify popularity (0-100)",
                            "r_score": "Reddit upvotes",
                            "valence": "Valence / Happiness (0-100)",
                            "tempo": "Tempo (bpm)",
                            "r_genres": "Genres",
                            "danceability": "Song danceability (0-100)"
                        })
        st.write(fig1)
            
        # Histogram release years
        logging.info("\n---Displaying Histogram release years...---\n")
        decades = []
        for year in sp['sp_release_year']:
            decade = int(np.floor(year / 10) * 10)
            decades.append(decade)
                    
        bins_decades=len(set(decades))
        fig6 = px.histogram(sp,
                            x='sp_release_year',
                            nbins=bins_decades,
                            title="Number of songs by decade",
                            labels={
                            "count": "Count",
                            "sp_release_year": "Release year"
                            })
        st.write(fig6)
        
        # Pie chart explicit tracks
        logging.info("\n---Displaying Pie chart explicit tracks...---\n")
        values = sp['sp_explicit'].value_counts()
        names = ['not explicit', 'explicit']
        fig2 = px.pie(sp, 
                        values=values, 
                        names=names, 
                        title="Percentage of explicit songs"
                    )
        st.write(fig2)

        # Bar plot Key signature vs. Spotify popularity
        logging.info("\n---Displaying Bar plot Key signature vs. Spotify popularity...---\n")
        fig3 = px.bar(sp, x="key", y="sp_popularity", color='r_score', orientation='v',
                    hover_data=["r_title", "r_score"],
                    height=400,
                    title='Song popularity per key signature',
                    labels={
                            "sp_popularity": "Spotify popularity score (0-100)",
                            "r_score": "Reddit upvotes",
                            "key": "Key signature"
                        })
        st.write(fig3)

        # # Map of song tempo by country
        # logging.info("\n---Displaying Map of song tempo by country...---\n")
        # fig4 = px.choropleth(countries,
        #                     locations="country_ISO-3", 
        #                     locationmode="ISO-3", 
        #                     scope="world",
        #                     color="tempo",
        #                     color_continuous_scale="Viridis_r",
        #                     title="Average song tempo by country",
        #                     labels={
        #                         "artist_country_ISO-3": "Country",
        #                         "tempo": "Song tempo (bpm)"
        #                     })
        # st.write(fig4)

        # Most underground vs. mainstream tracks
        logging.info("\n---Displaying Most underground vs. mainstream tracks...---\n")
        fig5 = px.scatter(sp, x='sp_artist_popularity', 
                    y='sp_popularity', 
                    color='sp_follower_count',
                    hover_name="r_title",
                    hover_data=['sp_genres'],
                    title='Most underground (lower left) vs. mainstream tracks (upper right)',
                    labels={
                        "r_title": "Track",
                        "sp_genres": "Genres",
                        "sp_popularity": "Spotify song popularity (0-100)",
                        "sp_follower_count": "Spotify followers",
                        "sp_artist_popularity": "Spotify artist popularity (0-100)"
                    })
        st.write(fig5)

        # # Reddit upvotes vs. Spotify popularity
        # logging.info("\n---Displaying Reddit upvotes vs. Spotify popularity...---\n")
        # scaler = MinMaxScaler()
        # r_score_normalized = pd.DataFrame(scaler.fit_transform(sp[['r_score']]))
        # sp_popularity_normalized = pd.DataFrame(scaler.fit_transform(sp[['sp_popularity']]))
        
        # x = list(range(1,101))
        # fig7 = go.Figure()
        # fig7.add_trace(go.Scatter(
        #     x=x,
        #     y=r_score_normalized[0],
        #     name = 'Reddit upvotes (normalized)', # Style name/legend entry with html tags
        #     connectgaps=True # override default to connect the gaps
        # ))
        # fig7.add_trace(go.Scatter(
        #     x=x,
        #     y=sp_popularity_normalized[0],
        #     name='Spotify popularity (normalized)',
        # ))
        # fig7.update_layout(title='Reddit upvotes vs. Spotify popularity score',
        #                 xaxis_title='Chart position',
        #                 yaxis_title='Popularity')
        # st.write(fig7)

    logging.info("\n---Dashboard page ready---\n")

###---Feedback page---###
with tab5:

    logging.info("\n---Setting up Feedback page...---\n")
    st.subheader("Your Feedback")
    st.markdown("Help improve this web app!\n If the form doesn't show up below, click [here](https://forms.gle/yDRBDT11fhb7dTQV8).")
    components.iframe(src="https://docs.google.com/forms/d/e/1FAIpQLSf3yu7dwmCD0kx4THNpJUEsRkdnTyMcE74EKk7-YRNrkaM95w/viewform?embedded=true", width=640, height=1090)
    logging.info("\n---Feedback page ready---\n")