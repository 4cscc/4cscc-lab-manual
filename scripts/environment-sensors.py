#!/usr/bin/python3

# This script depends on the pimoroni-sgp30 and sparkfun-qwiic-bme280
# python libraries. These can be installed with the command:
# python3 -m pip install pimoroni-sgp30 sparkfun-qwiic-bme280

from time import sleep, time
import sys
from tkinter import FALSE
import urllib.request
import urllib.parse
import urllib.error
import socket
import math

import qwiic_bme280
import sgp30


UNITS = {'tempF': 'degrees Fahrenheit',
         'humidity': '%% relative humdity',
         'pressure': 'Pascals',
         'co2': 'parts per million',
         'voc': 'parts per billion'}

hostname = socket.gethostname()

# The following values should be added from your Initial State account.
# See https://www.initialstate.com/
access_key = '' # EDIT: Add your Initial State API endpoint access key
bucket_key = ''  # EDIT: Add your Initial State API endpoint bucket key
inst_api_endpoint = "https://groker.init.st/api/events?accessKey=%s&bucketKey=%s" % (access_key, bucket_key)


def _urlopen(url, retries=10, delay=6, error_tolerant=True):
    # What's a better way to handle this so that an intermittent internet
    # outage doesn't shut the service down?
    i = 0
    for i in range(retries):
        try:
            urllib.request.urlopen(url)
            return
        except urllib.error.URLError as err:
            current_delay = delay * i
            print('URL request failed. Trying again in %d seconds.'\
                  % current_delay)
            print('Error message:')
            print(err)
            print()
            sleep(current_delay)
    if not error_tolerant:
        raise urllib.error.URLError
    else:
        print("** Error encountered trying to send data to InitialState. " +\
              "Let's ignore it, and maybe it'll go away...\n")


def _report_status_inst(value, debug=False):
    url_components = [inst_api_endpoint]
    parameter = '%s-status=%s' % (hostname, value)
    url_components.append(urllib.parse.quote(parameter))
    url = '&'.join(url_components)
    if debug:
        print('Requesting URL: %s' % url)
    _urlopen(url)


def _report_data_inst(data, debug=False):
    url_components = [inst_api_endpoint]
    for key, value in data.items():
        parameter = '%s-%s=%1.2f' % (hostname, key, value)
        url_components.append(urllib.parse.quote(parameter))
    url = '&'.join(url_components)
    if debug:
        print('Requesting URL: %s' % url)
    _urlopen(url)

def _report_status_terminal(value):
    print('System status: %s' % value)

def _report_data_terminal(data):
    for key, value in data.items():
        print('%s: %1.2f %s' % (key.titlecase(), value, UNITS[key]))

def _warmup_tph_sensor(sensor, reporting_frequency, warmup_time,
                       report_to_inst, report_to_terminal, debug):
    if warmup_time < 1:
        return

    start_time = time()

    while True:
        current_time = time()
        runtime = current_time - start_time
        if runtime < warmup_time:
            remaining_warmup_time_s = warmup_time - runtime
            remaining_warmup_time_m = math.ceil(remaining_warmup_time_s / 60)

            if remaining_warmup_time_m == 1:
                unit = "minute"
            else:
                unit = "minutes"

            _ = sensor.temperature_fahrenheit
            _ = sensor.pressure
            _ = sensor.humidity

            message = "%s warming up (about %d %s left)." %\
                            (hostname, remaining_warmup_time_m, unit)
            if report_to_inst: _report_status_inst(message, debug)
            if report_to_terminal: _report_status_terminal(message)

            sleep(reporting_frequency)
        else:
            return


def run(reporting_frequency=10, warmup_time=60,
        report_to_inst=True, report_to_terminal=True, debug=FALSE):

    message = "Starting atomospheric sensor (BME280) on %s." % hostname
    if report_to_inst: _report_status_inst(message, debug)
    if report_to_terminal: _report_status_terminal(message)
    tph_sensor = qwiic_bme280.QwiicBme280()
    if not tph_sensor.is_connected():
        message = "BME280 device not detected. Is it connected?"
        if report_to_inst: _report_status_inst(message, debug)
        if report_to_terminal: _report_status_terminal(message)
        return
    tph_sensor.begin()
    _warmup_tph_sensor(tph_sensor, reporting_frequency, warmup_time)


    message = "Starting air quality sensor (SGP30) on %s." % hostname
    if report_to_inst: _report_status_inst(message, debug)
    if report_to_terminal: _report_status_terminal(message)
    aq_sensor = sgp30.SGP30()
    aq_sensor.start_measurement()


    message = "Sensors sensing on %s." % hostname
    if report_to_inst: _report_status_inst(message, debug)
    if report_to_terminal: _report_status_terminal(message)


    sleep(reporting_frequency)


    try:
        while True:
            data = {}
            data['tempF'] = tph_sensor.temperature_fahrenheit
            data['pressure'] = tph_sensor.pressure
            data['humidity'] = tph_sensor.humidity

            aq_data = aq_sensor.get_air_quality()
            data['co2'] = aq_data.equivalent_co2
            data['voc'] =  aq_data.total_voc

            if report_to_inst: _report_data_inst(data, debug)
            if report_to_terminal: _report_data_terminal(data)

            message = "%s reporting." % hostname
            if report_to_inst: _report_status_inst(message, debug)
            if report_to_terminal: _report_status_terminal(message)

            sleep(reporting_frequency)

    except (KeyboardInterrupt, SystemExit):
        # We won't always get in this block on program termination, but we
        # can try to send the message.
        message = "%s offline." % hostname
        if report_to_inst: _report_status_inst(message, debug)
        if report_to_terminal: _report_status_terminal(message)


if __name__ == "__main__":
    run(report_to_inst=False,
        report_to_terminal=True,
        debug=FALSE)