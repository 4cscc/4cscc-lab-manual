# Adapted from: 
#  https://dash.plotly.com/live-updates
#  https://dash.plotly.com/dash-core-components/store

import datetime

import dash
from dash import dcc, html
import plotly
from dash.dependencies import Input, Output
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px

import qwiic_bme280
import qwiic_sgp40



## Initialize data dashboard
_initial_data_store = pd.DataFrame(
        [],
        columns=['Temperature', 'Humidity', 'Pressure', 'VOC'])

timestamp_fmt = '%-d %B %Y at %-I:%M:%S %p.'
start_time = pd.Timestamp.now()
span_style = {'padding': '5px', 'fontSize': '16px'}

app = dash.Dash(
    __name__,
    title = "4CSCC sensor dashboard",
    update_title=None,
)

app.layout = html.Div([
    html.Div([
        dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        ),
        dcc.Store(
            id='sensor-data', 
            data=_initial_data_store.to_json(date_format='iso', orient='split')
        ),
        html.H1('Data sensor live feed', style={'padding':'5px'}),
        html.Span('Collection initiated on {}'.format(start_time.strftime(timestamp_fmt)), style=span_style),
        html.Hr()
    ]),
    html.Div([
        html.Div(id='live-text'),
        dcc.Graph(id='live-temperature-graph', style={'background-color':'#f1f1f1'}),
        dcc.Graph(id='live-humidity-graph',),
        dcc.Graph(id='live-pressure-graph',),
        dcc.Graph(id='live-voc-graph',),
        html.Hr(),
        html.Span(
            ("* VOC index range is 0-500, with 100 representing " 
             "typical air quality and larger numbers indicating "
             "worse air quality."), style=span_style),
        html.A(
            "Learn more about VOCs and VOC sensing here",
            href="https://bit.ly/3AE9qdE",
            target="_blank"),
        html.Span(".")
     ]),
     html.Div([
        html.Hr(),
        html.Span("Developed by the ", style=span_style),
        html.A(
            "Four Corners Science and Computing Club (4CSCC)",
            href="https://github.com/gregcaporaso/4cscc-ln", 
            target="_blank"),
        html.Span(". 🐢")
    ])
])

## Initialize data sensors
tph_sensor = qwiic_bme280.QwiicBme280()
if not tph_sensor.begin():
    print('BME 280 Atmospheric sensor doesn\'t seem to be connected to the system.')
    exit(-1)
else:
    # discard first readings from the sensor as they tend to be unreliable
    _ = tph_sensor.temperature_fahrenheit
    _ = tph_sensor.pressure
    _ = tph_sensor.humidity

voc_sensor = qwiic_sgp40.QwiicSGP40()
if voc_sensor.begin() != 0:
    print('SGP 40 VOC sensor doesn\'t seem to be connected to the system.')
    exit(-1)
else:
    # discard first reading from the sensor as it tends to be unreliable
    _ = voc_sensor.get_VOC_index()

## Define callbacks and help functions
def _load_data(jsonified_data):
    df = pd.read_json(jsonified_data, orient='split')
    df.index = pd.DatetimeIndex(df.index)
    df.index.name = 'Time'
    return df

@app.callback(Output('sensor-data', 'data'), 
        Input('sensor-data', 'data'), 
        Input('interval-component', 'n_intervals'))
def collect_sensor_data(jsonified_data, n):
    df = _load_data(jsonified_data)
    df = df.last('3600S')
    
    dt = pd.Timestamp.now()
    tempF = tph_sensor.temperature_fahrenheit
    humidity = tph_sensor.humidity
    pressure_pa = tph_sensor.pressure
    pressure_atm = pressure_pa / 101325 # conversion Pascals to atmospheres
    voc = voc_sensor.get_VOC_index()

    new_entry = pd.DataFrame([[tempF, humidity, pressure_atm, voc]],
                             index=[dt],
                             columns=['Temperature', 'Humidity', 'Pressure', 'VOC'])

    df = pd.concat([df, new_entry])
    return df.to_json(orient='split')

@app.callback(Output('live-text', 'children'),
              Input('sensor-data', 'data'))
def update_current_values(jsonified_data):
    df = _load_data(jsonified_data)
    most_recent_entry = df.tail(1)
    dt = pd.Timestamp(most_recent_entry.index[0]).strftime(timestamp_fmt)
    
    return [
        html.Span('Most recent reading on {}'.format(dt), style=span_style),
        html.Br(),
        html.Span('Temperature: {0:0.2f} F'.format(most_recent_entry['Temperature'][0]), style=span_style),
        html.Span('Relative humidity: {0:0.2f}%'.format(most_recent_entry['Humidity'][0]), style=span_style),
        html.Span('Air pressure: {0:0.4f} atm'.format(most_recent_entry['Pressure'][0]), style=span_style),
        html.Span('VOC index: {0:0.2f}*'.format(most_recent_entry['VOC'][0]), style=span_style),
        html.Hr(),
    ]

@app.callback(Output('live-temperature-graph', 'figure'),
              Output('live-humidity-graph', 'figure'),
              Output('live-pressure-graph', 'figure'),
              Output('live-voc-graph', 'figure'),
              Input('sensor-data', 'data'))
def update_graphs(jsonified_data):
    df = _load_data(jsonified_data)
    temp_fig = px.line(
            df,
            x=df.index,
            y=df['Temperature'],
            title='Temperature (F) 🌡️',
            range_y=(10,110),
            height=500)
    humidity_fig = px.line(
            df,
            x=df.index,
            y=df['Humidity'],
            title='Percent relative humidity ☁️',
            range_y=(0,100),
            height=500)
    pressure_fig = px.line(
            df, 
            x=df.index, 
            y=df['Pressure'], 
            title='Pressure (atmospheres) ⛰️',
            range_y=(0,2),
            height=500) 
    voc_fig = px.line(
            df, 
            x=df.index, 
            y=df['VOC'],
            title='Volatile organic compounds (VOC) index* 😷',
            range_y=(0,500),
            height=500)
    return temp_fig, humidity_fig, pressure_fig, voc_fig


if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=True)
