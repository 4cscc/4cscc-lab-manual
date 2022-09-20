# Adapted from:
#  our sensor-dashboard.py script. It basically collects all the data that collects but doesn't render a webpage

import datetime

import os
import pandas as pd
import time

import qwiic_bme280
import qwiic_sgp40
import pms5003


# The location we are automatically logging data to over time
log_file_path = '/home/pi/code/sensor-log.csv'

## Initialize data dashboard
_initial_data_store = pd.DataFrame(
        [],
        columns=['Temperature', 'Humidity', 'Pressure', 'VOC', 'PM1.0', 'PM2.5', 'PM10'])

timestamp_fmt = '%-d %B %Y at %-I:%M:%S %p.'
start_time = pd.Timestamp.now()


## Helpers for reading from all sensors if they are connected and working
def _get_tph_sensor(tph_sensor):
    if not tph_sensor.is_connected():
        print("It looks like the tph sensor isn't connected. Please connect it.")
        return float('nan'), float('nan'), float('nan')

    # This sensor won't start reading again after unplugging unless reinitialized
    if not tph_sensor.is_measuring():
        if not _wrapped_begin(tph_sensor, 'tph'):
            return float('nan'), float('nan'), float('nan')
        # Wait a bit to try to get the thing reading correctly b/c it reads garbage initially
        time.sleep(.1)

    return tph_sensor.temperature_fahrenheit, tph_sensor.humidity, tph_sensor.pressure / 101325 # convert Pascals to atmospheres 


def _get_voc_sensor(voc_sensor):
    if not voc_sensor.is_connected():
        print("It looks like the voc sensor isn't connected. Please connect it.")
        return float('nan')

    return voc_sensor.get_VOC_index()


def _get_pm_sensor(pm_sensor):
    try:
        pm_sensor.reset()
        pm_reading = pm_sensor.read()
        return pm_reading.pm_ug_per_m3(1.0), pm_reading.pm_ug_per_m3(2.5), pm_reading.pm_ug_per_m3(10.0)
    except (pms5003.ChecksumMismatchError, pms5003.ReadTimeoutError, pms5003.SerialTimeoutError):
        print("It looks like the pm sensor isn't conencted. Please connect it.")
        return float('nan'), float('nan'), float('nan')
## End helpers


## Init the sensors and complain if they aren't connected
def _wrapped_begin(sensor, sensor_type):
    try:
        started = sensor.begin()

        # This always claims the voc sensor failed to start... Yet it works fine
        if not started:
            print(f"The {sensor_type} sensor failed to start. Please check the connection.")
    # This is what I was getting when I had the sensor completely disconnected
    except OSError as e:
        if e.errno == 121:
            print(f"It looks like the {sensor_type} sensor isn't connected. Please connect it. Please note the voc sensor must be connected on boot.")
        else:
            raise e
    else:
        return started

    return False


tph_sensor = qwiic_bme280.QwiicBme280()
_wrapped_begin(tph_sensor, 'tph')

voc_sensor = qwiic_sgp40.QwiicSGP40()
_wrapped_begin(voc_sensor, 'voc')

pm_sensor = pms5003.PMS5003()
_get_pm_sensor(pm_sensor)
## End init


if __name__ == '__main__':
    while True:
        dt = pd.Timestamp.now()
        tempF, humidity, pressure_atm = _get_tph_sensor(tph_sensor)
        voc = _get_voc_sensor(voc_sensor)
        pm1, pm2_5, pm10 = _get_pm_sensor(pm_sensor)

        new_entry = pd.DataFrame([[tempF, humidity, pressure_atm, voc, pm1, pm2_5, pm10]],
                                 index=[dt],
                                 columns=['Temperature', 'Humidity', 'Pressure', 'VOC', 'PM1.0', 'PM2.5', 'PM10'])
        new_entry.index.name = 'Time'
        new_entry.to_csv(log_file_path, mode='a', header=not os.path.exists(log_file_path))
        # Only read every 5 seconds
        time.sleep(5)

