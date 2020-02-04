import credentials, preferences

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

import pandas as pd
import pytz
import sqlite3
import datetime

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Live Twitter Visualization'

server = app.server

app.layout = html.Div(children=[

    html.H2('Live Tweet Sentiment Dashboard', style={'textAlign': 'center'}),
    
    html.Div(id='live-update-graph'),

    dcc.Interval(
        id='interval-component-slow',
        interval=5*1000, # in milliseconds
        n_intervals=0
    )
    ], style={'padding': '20px'})



# Update graph everytime interval is fired
@app.callback(Output('live-update-graph', 'children'),
              [Input('interval-component-slow', 'n_intervals')])
def update_graph_live(n):

    # 1. Create Database Connection
    db = sqlite3.connect('fbgoogle.db')

    # 2. Query the data 
    tz_gmt = pytz.timezone('GMT+0')
    time_diff = datetime.timedelta(minutes=15)
    now = pd.datetime.now(tz=tz_gmt)
    last_5min = now-time_diff
    last_10min = now-time_diff*2

    query = f"""SELECT id_str, created_at, polarity, user_location, text FROM {preferences.TABLE_NAME} WHERE created_at >= '{last_10min}' AND created_at <= '{now}';"""

    df10 = pd.read_sql(query, con=db, parse_dates='created_at')
    df10['created_at'] = df10['created_at'].dt.tz_localize('GMT+0')
    df = df10[df10['created_at'] > last_5min ]

    # 3. Apply Preprocessing for Area Plot
    result = df.copy()
    result['sentiment'] = df['polarity'].apply(to_sentiment)
    result = result.join(pd.get_dummies(result['sentiment']))
    result['total_tweets'] = result[['positive', 'negative', 'neutral']].sum(axis=1)
    result = result.set_index('created_at').resample('5S').agg({
        'positive':sum,
        'neutral':sum,
        'negative':sum,
        'total_tweets':sum,
    })


    # Create the graph html object
    children = [
                html.Div([
                    # Line Plot
                    html.Div([
                        dcc.Graph(
                            id='line-plot',
                            figure={
                                'data': [
                                    go.Scatter(
                                        x=result.index,
                                        y=result['neutral'] ,
                                        name='Neutrals',
                                        opacity=0.8,
                                        mode='lines',
                                        line=dict(shape='spline', smoothing=0.5, width=0.5, color='#323232'),
                                        stackgroup='one'
                                    ),
                                    go.Scatter(
                                        x=result.index,
                                        y=result['negative']*-1,
                                        name='Negatives',
                                        opacity=0.8,
                                        mode='lines',
                                        line=dict(shape='spline', smoothing=0.5, width=0.5, color='#891921'),
                                        stackgroup='two'
                                    ),
                                    go.Scatter(
                                        x=result.index,
                                        y=result['positive'] ,
                                        name='Positives',
                                        opacity=0.8,
                                        mode='lines',
                                        line=dict(shape='spline', smoothing=0.5, width=0.5, color='#119dff'),
                                        stackgroup='three'
                                    )
                                ],
                                'layout':{
                                    'showlegend':False,
                                    'title':'Number of Tweets in 15min',
                                }
                            }
                        )
                    ], style={'width': '73%', 'display': 'inline-block', 'padding': '0 0 0 20'}),
                    
                    # Pie Plot
                    html.Div([
                        dcc.Graph(
                            id='pie-chart',
                            figure={
                                'data': [
                                    go.Pie(
                                        labels=['Positives', 'Negatives', 'Neutrals'], 
                                        values=[result['positive'].sum(), result['negative'].sum(), result['neutral'].sum()],
                                        marker_colors=['#119dff','#891921','#323232'],
                                        opacity=0.8,
                                        textinfo='value',
                                        hole=.65)
                                ],
                                'layout':{
                                    'showlegend':True,
                                    'title':'Tweets Percentage',
                                    'annotations':[
                                        dict(
                                            text='{0:.1f}K'.format(result[['positive', 'negative', 'neutral']].sum().sum()/1000),
                                            font=dict(
                                                size=40
                                            ),
                                            showarrow=False
                                        )
                                    ]
                                }

                            }
                        )
                    ], style={'width': '27%', 'display': 'inline-block'})
                    
                ]),
                
            ]
    return children


'''
@app.callback(Output('live-update-graph-bottom', 'children'),
              [Input('interval-component-slow', 'n_intervals')])
def update_graph_bottom_live(n):

    # Loading data from Heroku PostgreSQL
    DATABASE_URL = os.environ['DATABASE_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    query = "SELECT id_str, text, created_at, polarity, user_location FROM {}".format(settings.TABLE_NAME)
    df = pd.read_sql(query, con=conn)
    conn.close()

    # Convert UTC into PDT
    df['created_at'] = pd.to_datetime(df['created_at']).apply(lambda x: x - datetime.timedelta(hours=7))

    # Clean and transform data to enable word frequency
    content = ' '.join(df["text"])
    content = re.sub(r"http\S+", "", content)
    content = content.replace('RT ', ' ').replace('&amp;', 'and')
    content = re.sub('[^A-Za-z0-9]+', ' ', content)
    content = content.lower()

    # Filter constants for states in US
    STATES = ['Alabama', 'AL', 'Alaska', 'AK', 'American Samoa', 'AS', 'Arizona', 'AZ', 'Arkansas', 'AR', 'California', 'CA', 'Colorado', 'CO', 'Connecticut', 'CT', 'Delaware', 'DE', 'District of Columbia', 'DC', 'Federated States of Micronesia', 'FM', 'Florida', 'FL', 'Georgia', 'GA', 'Guam', 'GU', 'Hawaii', 'HI', 'Idaho', 'ID', 'Illinois', 'IL', 'Indiana', 'IN', 'Iowa', 'IA', 'Kansas', 'KS', 'Kentucky', 'KY', 'Louisiana', 'LA', 'Maine', 'ME', 'Marshall Islands', 'MH', 'Maryland', 'MD', 'Massachusetts', 'MA', 'Michigan', 'MI', 'Minnesota', 'MN', 'Mississippi', 'MS', 'Missouri', 'MO', 'Montana', 'MT', 'Nebraska', 'NE', 'Nevada', 'NV', 'New Hampshire', 'NH', 'New Jersey', 'NJ', 'New Mexico', 'NM', 'New York', 'NY', 'North Carolina', 'NC', 'North Dakota', 'ND', 'Northern Mariana Islands', 'MP', 'Ohio', 'OH', 'Oklahoma', 'OK', 'Oregon', 'OR', 'Palau', 'PW', 'Pennsylvania', 'PA', 'Puerto Rico', 'PR', 'Rhode Island', 'RI', 'South Carolina', 'SC', 'South Dakota', 'SD', 'Tennessee', 'TN', 'Texas', 'TX', 'Utah', 'UT', 'Vermont', 'VT', 'Virgin Islands', 'VI', 'Virginia', 'VA', 'Washington', 'WA', 'West Virginia', 'WV', 'Wisconsin', 'WI', 'Wyoming', 'WY']
    STATE_DICT = dict(itertools.zip_longest(*[iter(STATES)] * 2, fillvalue=""))
    INV_STATE_DICT = dict((v,k) for k,v in STATE_DICT.items())

    # Clean and transform data to enable geo-distribution
    is_in_US=[]
    geo = df[['user_location']]
    df = df.fillna(" ")
    for x in df['user_location']:
        check = False
        for s in STATES:
            if s in x:
                is_in_US.append(STATE_DICT[s] if s in STATE_DICT else s)
                check = True
                break
        if not check:
            is_in_US.append(None)

    geo_dist = pd.DataFrame(is_in_US, columns=['State']).dropna().reset_index()
    geo_dist = geo_dist.groupby('State').count().rename(columns={"index": "Number"}) \
        .sort_values(by=['Number'], ascending=False).reset_index()
    geo_dist["Log Num"] = geo_dist["Number"].apply(lambda x: math.log(x, 2))


    geo_dist['Full State Name'] = geo_dist['State'].apply(lambda x: INV_STATE_DICT[x])
    geo_dist['text'] = geo_dist['Full State Name'] + '<br>' + 'Num: ' + geo_dist['Number'].astype(str)


    tokenized_word = word_tokenize(content)
    stop_words=set(stopwords.words("english"))
    filtered_sent=[]
    for w in tokenized_word:
        if (w not in stop_words) and (len(w) >= 3):
            filtered_sent.append(w)
    fdist = FreqDist(filtered_sent)
    fd = pd.DataFrame(fdist.most_common(16), columns = ["Word","Frequency"]).drop([0]).reindex()
    fd['Polarity'] = fd['Word'].apply(lambda x: TextBlob(x).sentiment.polarity)
    fd['Marker_Color'] = fd['Polarity'].apply(lambda x: 'rgba(255, 50, 50, 0.6)' if x < -0.1 else \
        ('rgba(184, 247, 212, 0.6)' if x > 0.1 else 'rgba(131, 90, 241, 0.6)'))
    fd['Line_Color'] = fd['Polarity'].apply(lambda x: 'rgba(255, 50, 50, 1)' if x < -0.1 else \
        ('rgba(184, 247, 212, 1)' if x > 0.1 else 'rgba(131, 90, 241, 1)'))



    # Create the graph 
    children = [
                html.Div([
                    dcc.Graph(
                        id='x-time-series',
                        figure = {
                            'data':[
                                go.Bar(                          
                                    x=fd["Frequency"].loc[::-1],
                                    y=fd["Word"].loc[::-1], 
                                    name="Neutrals", 
                                    orientation='h',
                                    marker_color=fd['Marker_Color'].loc[::-1].to_list(),
                                    marker=dict(
                                        line=dict(
                                            color=fd['Line_Color'].loc[::-1].to_list(),
                                            width=1),
                                        ),
                                )
                            ],
                            'layout':{
                                'hovermode':"closest"
                            }
                        }        
                    )
                ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 0 0 20'}),
                html.Div([
                    dcc.Graph(
                        id='y-time-series',
                        figure = {
                            'data':[
                                go.Choropleth(
                                    locations=geo_dist['State'], # Spatial coordinates
                                    z = geo_dist['Log Num'].astype(float), # Data to be color-coded
                                    locationmode = 'USA-states', # set of locations match entries in `locations`
                                    #colorscale = "Blues",
                                    text=geo_dist['text'], # hover text
                                    geo = 'geo',
                                    colorbar_title = "Num in Log2",
                                    marker_line_color='white',
                                    colorscale = ["#fdf7ff", "#835af1"],
                                    #autocolorscale=False,
                                    #reversescale=True,
                                ) 
                            ],
                            'layout': {
                                'title': "Geographic Segmentation for US",
                                'geo':{'scope':'usa'}
                            }
                        }
                    )
                ], style={'display': 'inline-block', 'width': '49%'})
            ]
        
    return children

'''

# Helper Functions 
def to_sentiment(polarity):
    if polarity > 0.5:
        return 'positive'
    elif polarity > -0.5:
        return 'neutral'
    else:
        return 'negative'

if __name__ == '__main__':
    app.run_server(debug=True)