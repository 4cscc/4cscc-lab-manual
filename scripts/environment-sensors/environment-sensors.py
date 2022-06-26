#!/usr/bin/python3

# This script depends on the pimoroni-sgp30 and sparkfun-qwiic-bme280
# python libraries. These can be installed with the command:
# python3 -m pip install pimoroni-sgp30 sparkfun-qwiic-bme280

from time import sleep, time
import sys
import urllib.request
import urllib.parse
import urllib.error
import socket
import math
import qwiic_bme280
import sgp30

import click

class EnvironmentSensors:

    _units = {'tempF': 'degrees Fahrenheit',
              'humidity': '% relative humdity',
              'pressure': 'Pascals',
              'co2': 'parts per million',
              'voc': 'parts per billion'}

    def __init__(self, inst_access_key=None, inst_bucket_key=None,
                 host_identifier=None, report_to_inst=False,
                 report_to_terminal=True):

        self._report_to_inst = report_to_inst
        self._report_to_terminal = report_to_terminal

        if self._report_to_inst:
            if inst_access_key is None:
                raise ValueError(
                    'inst_access_key is required when reporting to Initial State.')

            if inst_bucket_key is None:
                raise ValueError(
                    'inst_bucket_key is required when reporting to Initial State.')

            self._inst_api_endpoint = \
                "https://groker.init.st/api/events?accessKey=%s&bucketKey=%s" % \
                    (inst_access_key, inst_bucket_key)
            self._reporting_frequency = 60
        elif self._report_to_terminal:
            self._inst_api_endpoint = None
            self._reporting_frequency = 5
        else:
            raise ValueError(
                "Not reporting to Initial State or terminal, so there's nothing to do.")

        if host_identifier is None:
            self._host_identifier = socket.gethostname()
        else:
            self._host_identifier = host_identifier

    def _urlopen(self, url, retries=10, delay=6, error_tolerant=True,
                 verbose=False, debug=False):
        if verbose:
            print('Requesting URL: %s' % url)

        if debug:
            return (-1, url)

        i = 0
        for i in range(retries):
            try:
                urllib.request.urlopen(url)
                return (0, "Success")
            except urllib.error.URLError as err:
                current_delay = delay * i
                print('Request of URL failed: %s' % url)
                print('Trying again in %d seconds.' % current_delay)
                #print('HTTP error code: %s %s' % (err.code, err.reason))
                sleep(current_delay)

        if not error_tolerant:
            raise urllib.error.URLError
        else:
            print("** Error encountered trying to send data to InitialState. " +\
                "Let's ignore it, and maybe it'll go away...\n")
            return (1, "Failure")


    def _report_status_inst(self, value, verbose=False, debug=False):
        url_components = [self._inst_api_endpoint]
        parameter = '%s-status=%s' % \
            (urllib.parse.quote(self._host_identifier),
            urllib.parse.quote(value))
        url_components.append(parameter)
        url = '&'.join(url_components)

        return self._urlopen(url, verbose=verbose, debug=debug)


    def _report_data_inst(self, data, verbose=False, debug=False):
        url_components = [self._inst_api_endpoint]
        for key, value in data.items():
            parameter = '%s-%s=%1.2f' % \
                (urllib.parse.quote(self._host_identifier),
                 urllib.parse.quote(key),
                 value)
            url_components.append(parameter)
        url = '&'.join(url_components)

        return self._urlopen(url, verbose=verbose, debug=debug)


    def _report_status_terminal(self, value):
        print('%s status: %s' % (self._host_identifier, value))


    def _report_data_terminal(self, data):
        for key, value in data.items():
            print('%s: %1.2f %s' % (key.title(), value, self._units[key]))

    def _warmup_tph_sensor(self, sensor, warmup_time, debug):
        if warmup_time < 1:
            return

        start_time = time()

        while True:
            current_time = time()
            runtime = current_time - start_time
            if runtime < warmup_time:
                remaining_warmup_time_s = warmup_time - runtime
                remaining_warmup_time_m = math.ceil(remaining_warmup_time_s/60)

                if remaining_warmup_time_m < 3:
                    message = "%s warming up (about %d seconds left)." %\
                                    (self._host_identifier,
                                     remaining_warmup_time_s)
                else:
                    message = "%s warming up (about %d minutes left)." %\
                                    (self._host_identifier,
                                     remaining_warmup_time_m)

                _ = sensor.temperature_fahrenheit
                _ = sensor.pressure
                _ = sensor.humidity

                if self._report_to_inst: self._report_status_inst(message, debug)
                if self._report_to_terminal: self._report_status_terminal(message)

                sleep(self._reporting_frequency)
            else:
                return


    def __call__(self, tph_warmup_time=60, verbose=False, debug=False,
                 tph_sensor=None, aq_sensor=None):

        if tph_sensor is None:
            message = "Starting atomospheric sensor (BME280) on %s." % self._host_identifier
            if self._report_to_inst: self._report_status_inst(message, debug)
            if self._report_to_terminal: self._report_status_terminal(message)
            tph_sensor = qwiic_bme280.QwiicBme280()
            if not tph_sensor.is_connected():
                message = "BME280 device not detected. Is it connected?"
                if self._report_to_inst: self._report_status_inst(message, debug)
                if self._report_to_terminal: self._report_status_terminal(message)
                return
            else:
                tph_sensor.begin()
                self._warmup_tph_sensor(tph_sensor, tph_warmup_time, debug)


        if aq_sensor is None:
            message = "Starting air quality sensor (SGP30) on %s." % self._host_identifier
            if self._report_to_inst: self._report_status_inst(message, debug)
            if self._report_to_terminal: self._report_status_terminal(message)
            aq_sensor = sgp30.SGP30()
            aq_sensor.start_measurement()


        message = "Sensors sensing on %s." % self._host_identifier
        if self._report_to_inst: self._report_status_inst(message, debug)
        if self._report_to_terminal: self._report_status_terminal(message)


        try:
            while True:
                data = {}
                data['tempF'] = tph_sensor.temperature_fahrenheit
                data['pressure'] = tph_sensor.pressure
                data['humidity'] = tph_sensor.humidity

                aq_data = aq_sensor.get_air_quality()
                data['co2'] = aq_data.equivalent_co2
                data['voc'] =  aq_data.total_voc

                if self._report_to_inst: self._report_data_inst(data, debug)
                if self._report_to_terminal: self._report_data_terminal(data)

                if self._report_to_terminal: print('')

                sleep(self._reporting_frequency)

        except (KeyboardInterrupt, SystemExit):
            # We won't always get in this block on program termination, but we
            # can try to send a message.
            message = "%s offline." % self._host_identifier
            if self._report_to_inst: self._report_status_inst(message, debug)
            if self._report_to_terminal: self._report_status_terminal(message)
            exit(1)

@click.command()
@click.option('--access-key', name='inst_access_key', default=None,
              help='Initial State access key.')
@click.option('--bucket-key', name='inst_bucket_key',  default=None,
              help='Initial State bucket key.')
@click.option('--host-identifier', default=socket.gethostname(),
              help='Optional identifier for this machine.')
@click.option('--report-to-inst', default=False,
              help='Report sensor data to Initial State.')
@click.option('--report-to-terminal', default=False,
              help='Report sensor data to terminal.')
@click.option('--debug', default=False, help='Run in debug mode.')
@click.option('--verbose', default=False, help='Run in verbose mode.')
def run(inst_access_key=None,
        inst_bucket_key=None,
        host_identifier=None,
        report_to_inst=False,
        report_to_terminal=True,
        debug=False,
        verbose=False):

    if report_to_inst:
        if inst_access_key is not None:
            click.echo("Must provide access key to write to Initial State.")
        if inst_bucket_key is not None:
            click.echo("Must provide bucket key to write to Initial State.")

    # e = EnvironmentSensors(inst_access_key=inst_access_key,
    #                        inst_bucket_key=inst_bucket_key,
    #                        host_identifier=None,
    #                        report_to_inst=report_to_inst,
    #                        report_to_terminal=report_to_terminal)
    # e(verbose=verbose, debug=debug)

if __name__ == "__main__":
    run()
