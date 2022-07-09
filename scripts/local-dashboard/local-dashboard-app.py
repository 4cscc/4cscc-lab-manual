# Adapted from: 
#  https://dash.plotly.com/live-updates
#  https://dash.plotly.com/dash-core-components/store

import datetime

import dash
from dash import dcc, html
import plotly
from dash.dependencies import Input, Output
import pandas as pd

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
_initial_data_store = pd.DataFrame([], 
    columns=['Time', 'Temperature', 'Humidity', 'Pressure', 'VOC'])

app = dash.Dash(__name__)
app.layout = html.Div(
    html.Div([
        html.H4('4CSCC: Data sensor live feed'),
        html.Div(id='live-update-text'),
        dcc.Graph(id='live-update-graph',),
        dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        ),
        dcc.Store(id='sensor-data', data=_initial_data_store.to_json(date_format='iso', orient='split')),
        ])
)


@app.callback(Output('sensor-data', 'data'), 
        Input('sensor-data', 'data'), 
        Input('interval-component', 'n_intervals'))
def collect_sensor_data(data, n):
    # load data collected in the last hour (3599 seconds, 
    # and we'll add one more in this call)
    df = pd.read_json(data, orient='split').tail(3599)
    
    dt = datetime.datetime.now()
    tempF = tph_sensor.temperature_fahrenheit
    humidity = tph_sensor.humidity
    pressure_pa = tph_sensor.pressure
    pressure_atm = pressure_pa / 101325 # conversion Pascals to atmospheres
    voc = voc_sensor.get_VOC_index()

    new_entry = pd.DataFrame([[dt, tempF, humidity, pressure_atm, voc]], 
                             columns=['Time', 'Temperature', 'Humidity', 'Pressure', 'VOC'])

    df = pd.concat([df, new_entry])
    return df.to_json(date_format='iso', orient='split')

@app.callback(Output('live-update-text', 'children'),
              Input('sensor-data', 'data'))
def update_metrics(jsonified_data):
    df = pd.read_json(jsonified_data, orient='split')
    most_recent_entry = df.tail(1)
    style = {'padding': '5px', 'fontSize': '16px'}
    dt = pd.Timestamp(most_recent_entry['Time'][0]).strftime('%-d %B %Y %-I:%M:%S %p')
    
    return [
            html.Span('Most recent reading: {}'.format(dt), style=style),
        html.Br(),
        html.Span('Temperature: {0:0.2f} F'.format(most_recent_entry['Temperature'][0]), style=style),
        html.Span('Relative humidity: {0:0.2f}%'.format(most_recent_entry['Humidity'][0]), style=style),
        html.Span('Air pressure: {0:0.4f} atm'.format(most_recent_entry['Pressure'][0]), style=style),
        html.Span('VOC: {0:0.2f} ppb'.format(most_recent_entry['VOC'][0]), style=style),
        html.Hr(),
    ]


@app.callback(Output('live-update-graph', 'figure'),
              Input('sensor-data', 'data'))
def update_graph_live(jsonified_data):
    df = pd.read_json(jsonified_data, orient='split')
    
    # Create the graph with subplots
    fig = plotly.tools.make_subplots(rows=4, cols=1, vertical_spacing=0.2)
    fig['layout']['margin'] = {
        'l': 30, 'r': 10, 'b': 30, 't': 10
    }
    fig['layout']['legend'] = {'x': 0, 'y': 1.02, 'xanchor': 'left', 'yanchor':'bottom', 'orientation':'v'}

    fig.append_trace({
        'x': df['Time'],
        'y': df['Temperature'],
        'name': 'Temperature (F)',
        'mode': 'lines',
        'type': 'scatter'
    }, 1, 1)

    fig.append_trace({
        'x': df['Time'],
        'y': df['Humidity'],
        'name': 'Percent relative humidity',
        'mode': 'lines',
        'type': 'scatter'
    }, 2, 1)

    fig.append_trace({
        'x': df['Time'],
        'y': df['Pressure'],
        'name': 'Air pressure (atmospheres)',
        'mode': 'lines',
        'type': 'scatter'
        }, 3, 1)

    fig.append_trace({
        'x': df['Time'],
        'y': df['VOC'],
        'name': 'Volatile Organic Compounds (parts per billion)',
        'mode': 'lines',
        'type': 'scatter'
        }, 4, 1)

    return fig


if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=True)
