TRACK_WORDS = ['Facebook', 'Google']
TABLE_NAME = "fbgoogle"

TABLE_ATTRIBUTES = "id_str VARCHAR(255), created_at DATETIME, text STRING, \
            polarity INT, subjectivity INT, user_created_at VARCHAR(255), user_location VARCHAR(255), \
            user_description VARCHAR(255), user_followers_count INT, longitude DOUBLE, latitude DOUBLE, \
            retweet_count INT, favorite_count INT"