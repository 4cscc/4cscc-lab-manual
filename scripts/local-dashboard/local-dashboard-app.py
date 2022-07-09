# Adapted from: 
#  https://dash.plotly.com/live-updates
#  https://dash.plotly.com/dash-core-components/store

## TODO
# - fill more of browser window with graphs
# - why is slicing data through the previous hour not working? 
# - set reasonable default values for ymin and ymax on each graph?

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


## Initialize data dashboard
_initial_data_store = pd.DataFrame(
        [],
        columns=['Temperature', 'Humidity', 'Pressure', 'VOC'])

app = dash.Dash(__name__)
app.layout = html.Div(
    html.Div([
        html.H4('4CSCC: Data sensor live feed'),
        html.Div(id='live-text'),
        dcc.Graph(id='live-temperature-graph',),
        dcc.Graph(id='live-humidity-graph',),
        dcc.Graph(id='live-pressure-graph',),
        dcc.Graph(id='live-voc-graph',),
        dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        ),
        dcc.Store(id='sensor-data', data=_initial_data_store.to_json(date_format='iso', orient='split')),
        ])
    )

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
def update_metrics(jsonified_data):
    df = _load_data(jsonified_data)
    most_recent_entry = df.tail(1)
    style = {'padding': '5px', 'fontSize': '16px'}
    dt = pd.Timestamp(most_recent_entry.index[0]).strftime('%-d %B %Y %-I:%M:%S %p')
    
    return [
        html.Span('Most recent reading: {}'.format(dt), style=style),
        html.Br(),
        html.Span('Temperature: {0:0.2f} F'.format(most_recent_entry['Temperature'][0]), style=style),
        html.Span('Relative humidity: {0:0.2f}%'.format(most_recent_entry['Humidity'][0]), style=style),
        html.Span('Air pressure: {0:0.4f} atm'.format(most_recent_entry['Pressure'][0]), style=style),
        html.Span('VOC: {0:0.2f} ppb'.format(most_recent_entry['VOC'][0]), style=style),
        html.Hr(),
    ]


@app.callback(Output('live-temperature-graph', 'figure'),
              Input('sensor-data', 'data'))
def live_temperature_graph(jsonified_data):
    df = _load_data(jsonified_data)
    return px.line(df, x=df.index, y=df['Temperature'], height=500)

@app.callback(Output('live-humidity-graph', 'figure'),
              Input('sensor-data', 'data'))
def live_humidity_graph(jsonified_data):
    df = _load_data(jsonified_data)
    return px.line(df, x=df.index, y=df['Humidity'], height=500)

@app.callback(Output('live-pressure-graph', 'figure'),
              Input('sensor-data', 'data'))
def live_pressure_graph(jsonified_data):
    df = _load_data(jsonified_data)
    return px.line(df, x=df.index, y=df['Pressure'], height=500)

@app.callback(Output('live-voc-graph', 'figure'),
              Input('sensor-data', 'data'))
def live_voc_graph(jsonified_data):
    df = _load_data(jsonified_data)
    return px.line(df, x=df.index, y=df['VOC'], height=500)





if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=True)
