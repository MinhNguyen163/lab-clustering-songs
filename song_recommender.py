#import libraries
import requests
import pandas as pd
import numpy as np 
import pickle

import sys
sys.path.append('/Users/minhnguyen/IronHack2023-2024/Bootcamp/')
from config_2 import *

import spotipy
import json
from spotipy.oauth2 import SpotifyClientCredentials
from time import sleep
import streamlit as st
#Initialize SpotiPy with user credentias #
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=Client_ID, client_secret=Client_Secret))
# import libraries
#from recommend_function_2 import *

# load song_db
song_db = pd.read_csv('song_db_cluster.csv')

# split list of song ids:
def chunks (song_ids, n:int =50)-> list:
    """
    Divides a sequence of song IDs into chunks of a specified size.

    Parameters:
    - song_ids (list or pandas.DataFrame): The sequence of song IDs to be divided into chunks.
      It can be either a list or a pandas DataFrame.
    - n (int, optional): The desired size of each chunk. Default is 50.

    Returns:
    - list: A list containing chunks of song IDs, where each chunk has a maximum size of 'n'.

    Note:
    - If 'song_ids' is a list, the chunks are created using list slicing.
    - If 'song_ids' is a pandas DataFrame, the chunks are created using DataFrame row slicing.
    - If 'song_ids' is smaller than 'n', a single chunk containing all elements is returned.
    """
    if len(song_ids) > n:
        if type(song_ids) == list:
            chunks = [song_ids[x:x+n] for x in range(0, len(song_ids), n)]
            return chunks
        elif type(song_ids) == pd.DataFrame:
            chunks = [song_ids.iloc[x:x+n,] for x in range(0, len(song_ids), n)]
            return chunks
        else:
            pass
        
    else:
        chunks = [song_ids]
        return chunks


def song_info_spotify(title:str, artist:str ='', limit:int = 1):

    track_id_list = []
    track_name_list = []
    artist_name_list = []
    href_list = []
    popularity_list = []

    if artist == '':
        try:
            result = sp.search(q=f"track:{title}", limit=limit)
            for i in range(0,limit):
                track_id = result['tracks']['items'][i]['id']
                track_id_list.append(track_id)
                track_name = result['tracks']['items'][i]['name']
                track_name_list.append(track_name)
                href = result['tracks']['items'][i]['href']
                href_list.append(href)
                artist_name = result['tracks']['items'][i]['artists'][0]['name']
                artist_name_list.append(artist_name)
                popularity = result['tracks']['items'][i]['popularity']
                popularity_list.append(popularity)

        except:
            print('Song not found')
            track_id_list.append('None')
            track_name_list.append('None')
            href_list.append('None')
            artist_name_list.append("None")
            popularity_list.append('None')

    else:
        try:
            result = sp.search(q=f"track:{title} artist:{artist}", limit=limit)
            for i in range(0,limit):
                track_id = result['tracks']['items'][i]['id']
                track_id_list.append(track_id)
                track_name = result['tracks']['items'][i]['name']
                track_name_list.append(track_name)
                href = result['tracks']['items'][i]['href']
                href_list.append(href)
                artist_name = result['tracks']['items'][i]['artists'][0]['name']
                artist_name_list.append(artist_name)
                popularity = result['tracks']['items'][i]['popularity']
                popularity_list.append(popularity)

        except:
            print('Song not found')
            track_id_list.append('None')
            track_name_list.append('None')
            href_list.append('None')
            artist_name_list.append("None")
            popularity_list.append('None')

    track_info = pd.DataFrame({'song_id':track_id_list, 'track_name': track_name_list, 'artist_name': artist_name_list, 'track_href': href_list, 'popularity': popularity_list})

    return track_info

# function for getting audio features
def get_audio_features (list:list):
    
    sublists = chunks(list,100)
    audio_features_dict ={'danceability':[], 'energy':[], 'key':[], 'loudness':[], 'mode':[], 'speechiness':[], 'acousticness':[],'instrumentalness':[], 'liveness':[], 'valence':[], 'tempo':[], 'type':[], 'id':[], 'uri':[], 'track_href':[], 'analysis_url':[], 'duration_ms':[], 'time_signature':[]}
    for index,list in enumerate(sublists):
        #print(f"Retrieving audio_features from chunk {index}")
        # get audio_features
        try:
            audio_features = sp.audio_features(list)
            for feature in audio_features:
                for key in audio_features_dict:
                    audio_features_dict[key].append(feature[key])
            #audio_features['song_id'] = song_id # add dict item with key 'song_id' and value song_id            
            #audio_features_list.append(audio_features)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', 1))
                print(f"Rate limited. Retrying after {retry_after} seconds.")
                sleep(retry_after + 1)
                continue
            else:
                raise
        except Exception as e:
            print(f"Failed to get audio features for some track IDs: {e}")

        #print("sleep a bit before getting the next chunk")
        print('Processing...')  
        sleep(10)

    audio_features_df = pd.DataFrame(audio_features_dict)
    return audio_features_df

# function to add audio features to the track info dataframe
def add_audio_features (df1, df2, left_col, right_col, how = 'inner' ):
   
    extended_df = pd.merge(df1, df2, left_on=left_col, right_on=right_col, how = how)
    return extended_df

# function to get recommendation from the song_db
def recommendation(song_db, user_song_cluster, hot_value:str = None, num_recommendations=5):
    if hot_value != None:
        recommendation = song_db[(song_db['cluster'] == int(user_song_cluster)) & (song_db['hotness'] == hot_value)].sample(num_recommendations)
    else: 
        recommendation = song_db[(song_db['cluster'] == int(user_song_cluster))].sample(num_recommendations)

    recommendation = recommendation[['track_name', 'artist_name', 'track_href']]
    sleep(20)
    print("\n Here are recommended songs and the link to spotify for you to try out: \n")
    print()
    print(recommendation)
    
# get Scaler and model
with open( "song_cluster_scaled.pkl","rb") as file:
    scaler= pickle.load(file)
    
with open( "KMeans_cluster.pkl","rb") as file:
    model= pickle.load(file)

choice = 'yes'
while choice == 'yes':

# ask for user inputs:
    track_name = str(input("Please enter your favourite's song: "))
    artist_name = str(input("Please enter the artist name (press enter to skip): "))

#from get_feature_update import *
    song_info = song_info_spotify(track_name, artist_name, 5)
# output the spotify search result of 5 songs with track_name with or without an artist_name
    print('Processing ... \n')
    print()
    print('we retrieved the below songs from Spotify: \n')
    print()
    print(song_info[['track_name', 'artist_name', 'popularity']])
    sleep(5)
    print()
    print('\n Please choose which song you would like to search: ')

# get choice from user
    choice = int(input("Please enter the number of the song you would like to search:"))
    print()
    print('\n Processing ... \n')
# set selected track from user input
    selected_track_id = [song_info.iloc[choice, 0]]

# get audio features for the selected track
    song_audio = get_audio_features(selected_track_id)

# calling function to add audio features to the selected track info dataframe
    user_song_final = add_audio_features(song_info, song_audio, 'song_id', 'id')
# get the df with selected audio features for cluster prediction
    user_song_cluster_df = user_song_final[['danceability', 'energy', 'acousticness', 'key', 'valence']]


# perform scale data and cluster prediction for selected track
    user_song_cluster_scaled = scaler.transform(user_song_cluster_df)
    user_song_cluster_scaled_df = pd.DataFrame(user_song_cluster_scaled, columns = user_song_cluster_df.columns)
    user_song_cluster = model.predict(user_song_cluster_scaled_df)

# check in which group of 'hotness' the selected track is, and get recommendation from song_db with the same cluster and the same hotness
# output recommendation to user, and promtp for new input
    if song_info.iloc[choice, 0] in song_db[song_db['hotness'] == 'yes']['song_id'].tolist():
        recommendation = recommendation(song_db, user_song_cluster, 'yes')
        print('\n What do you think?')
        print()
        sleep(10)
        print('\n You enjoyed and would like to have another recommendation from us?\n ')
        sleep(10)
        print()
        choice = str(input("If yes, please enter 'yes' to provide a song name! \n If not, please enter 'no' to escape"))
        if choice == 'yes':
            continue
        else:
            break
    elif song_info.iloc[choice, 0] in song_db[song_db['hotness'] == 'no']['song_id'].tolist():
        recommendation = recommendation(song_db, user_song_cluster, 'no')
        print('\n What do you think?')
        print()
        sleep(10)
        print('\n You enjoyed and would like to have another recommendation from us?\n ')
        sleep(10)
        print()
        choice = str(input("If yes, please enter 'yes' to provide a song name! \n If not, please enter 'no' to escape"))
        if choice == 'yes':
            continue
        else:
            break
    else:
        print('\n We could not process the "hotness" of this song at this moment yet.\n' )
        print('\n But we think you might enjoy these songs still! \n' )
        recommendation = recommendation(song_db, user_song_cluster)
        print('\n What do you think?')
        print()
        sleep(10)
        print('\n You enjoyed and would like to have another recommendation from us?\n ')
        sleep(10)
        print()
        choice = str(input("If yes, please enter 'yes' to provide a song name! \n If not, please enter 'no' to escape"))
        if choice == 'yes':
            continue
        else:
            break


        
    
