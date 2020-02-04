import credentials # Import api/access_token keys from credentials.py
import preferences # Import related setting constants from preferences.py 

import re
from textblob import TextBlob
import tweepy

import sqlite3
from sqlite3 import Error




def init_database(db_file, table_name, attributes):
    qry_check_table = f"""SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}'"""
    qry_create_table = f"""CREATE TABLE {table_name} ({attributes});"""
    qry_list_table = f"""SELECT name FROM sqlite_master WHERE type ='table' AND name NOT LIKE 'sqlite_%';"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.execute(qry_check_table)
        # create table if previously doesn't exists
        if cursor.fetchone()[0]==0 : 
            conn.execute(qry_create_table)
        conn.commit()
    except Error as e:
        raise(e)
    finally:
        if conn:
            return conn

def clean_tweet(tweet): 
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) \
                            |(\w+:\/\/\S+)", " ", tweet).split()) 
def to_ascii(text):
    if text:
        return text.encode('ascii', 'ignore').decode('ascii')
    else:
        return None
        
# Override tweepy.StreamListener  on_status
class MyStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        # Get information of each tweet
        # Don't take retweet
        if status.retweeted:
            return True

        id_str = status.id_str
        created_at = status.created_at # utc+0
        text = to_ascii(status.text)
        text = clean_tweet(text)
        sentiment = TextBlob(text).sentiment
        polarity = sentiment.polarity
        subjectivity = sentiment.subjectivity

        user_created_at = status.user.created_at # utc+0
        user_location = to_ascii(status.user.location)
        user_description = to_ascii(status.user.description)
        user_followers_count =status.user.followers_count
        longitude = None
        latitude = None
        if status.coordinates:
            longitude = status.coordinates['coordinates'][0]
            latitude = status.coordinates['coordinates'][1]

        retweet_count = status.retweet_count
        favorite_count = status.favorite_count

        print(f"""ID: {id_str}\tCreated: {created_at}\tPolarity: {polarity} subjectivity: {subjectivity}""")

        query = sql = f"INSERT INTO {preferences.TABLE_NAME} \
        (id_str, created_at, text, polarity, subjectivity, user_created_at, user_location, \
        user_description, user_followers_count, longitude, latitude, retweet_count, favorite_count) \
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        
        val = (id_str, created_at, text, polarity, subjectivity, user_created_at, user_location, \
                user_description, user_followers_count, longitude, latitude, retweet_count, favorite_count)
        
        try:
            db.execute(query, val)
        except Error as e: 
            raise(e)
        finally:
            db.commit()
    
    def on_error(self, status_code):
        if status_code == 420:
            # return False to disconnect the stream
            return False

if __name__ == '__main__':
    auth  = tweepy.OAuthHandler(credentials.API_KEY, credentials.API_SECRET_KEY)
    auth.set_access_token(credentials.ACCESS_TOKEN, credentials.ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    db = init_database('fbgoogle.db', preferences.TABLE_NAME, preferences.TABLE_ATTRIBUTES)
    myStreamListener = MyStreamListener()
    myStream = tweepy.Stream(auth = api.auth, listener = myStreamListener)
    myStream.filter(languages=["en"], track = preferences.TRACK_WORDS)