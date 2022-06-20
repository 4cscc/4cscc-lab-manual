# VOC and CO2 sensing

In this lesson...

## Parts list

For this exercise you'll need:
* [Raspberry Pi 400](https://www.sparkfun.com/products/17377) computer
* Sparkfun [Qwiic pHAT Extension](https://www.sparkfun.com/products/17512)
* Sparkfun [SGP30 Air Quality Sensor](https://www.sparkfun.com/products/16531)
* Sparkfun [Qwiic cable (500mm)](https://www.sparkfun.com/products/14429)
* [Initial State](https://www.initialstate.com/) access and bucket keys
* An internet connection

If you haven't used Initial State before, start with their [_Getting Started_ documentation](https://support.initialstate.com/hc/en-us/categories/360000428291-Using-Initial-State).

## Python 3 code

```python
from sgp30 import SGP30
from time import sleep, time
import sys
import urllib.request
import urllib.parse
import socket
import math

hostname = socket.gethostname()

# The following values should be added from your Initial State account.
# See https://www.initialstate.com/
access_key = '' # EDIT: Add your Initial State API endpoint access key
bucket_key = ''  # EDIT: Add your Initial State API endpoint bucket key
inst_api_endpoint = "https://groker.init.st/api/events?accessKey=%s&bucketKey=%s" % (access_key, bucket_key)


def report_string_inst(name, value):
    name = urllib.parse.quote(name)
    value = urllib.parse.quote(value)
    urllib.request.urlopen(inst_api_endpoint + '&%s=%s' % (name, value))


def report_status(value,quiet=False):
    if not quiet:
        print(value)
    report_string_inst("status", value)


def report_aq_inst(sensor):
        result = sensor.get_air_quality()
        print(result)

        urllib.request.urlopen(inst_api_endpoint +\
                               "&co2=%1.2f" % result.equivalent_co2 +\
                               "&voc=%1.2f" % result.total_voc)



def run(reporting_frequency=10):
    print("Air quality sensor (SGP30) on %s:\n" % hostname)
    sensor = SGP30()

    # if not sensor.is_connected():
    #     print("SGP30 device not detected. Is it connected?", \
    #         file=sys.stderr)
    #     return

    sensor.start_measurement()
    report_status("%s online." % hostname)

    try:
        while True:
            sleep(reporting_frequency)
            report_aq_inst(sensor)
            report_status("%s reporting." % hostname, quiet=True)
    except (KeyboardInterrupt, SystemExit):
        report_status("%s offline." % hostname)

if __name__ == "__main__":
    run()
```