# Atmospheric sensing

In this lesson we'll collect temperature, humidity, and air pressure data from
a sensor and present it in a Python terminal.

## Parts list

For this exercise you'll need:
* [Raspberry Pi 400](https://www.sparkfun.com/products/17377) computer
* Sparkfun [Qwiic pHAT Extension](https://www.sparkfun.com/products/17512)
* Sparkfun [BME280 Atmospheric Sensor](https://www.sparkfun.com/products/15440)
* Sparkfun [Qwiic cable (500mm)](https://www.sparkfun.com/products/14429)

## Wire pHAT and sensor

Your set-up might look slightly different than this. This image shows only the BME280 atomospheric sensor attached to the pHAT.

![Completed pHAT](images/pHAT-1.jpg)

## Write a Python 3 program

To use the following code, open a command terminal. Then enter the following command:

```
source ~/code/4cscc-ln/venv/bin/activate
```

Then, enter the following command to start an ipython terminal:

```
ipython
```

Finally, copy paste the following code into the ipython terminal. This will collect temperature, air pressure, and relative humidity readings from your BME280 sensor every 2 seconds and display them on the screen. It will run until you press "Control-c" (i.e., press the "control" and "c" keys at the same time).

```python
from time import sleep
import qwiic_bme280

tph_sensor = qwiic_bme280.QwiicBme280()
if not tph_sensor.begin():
    print('BME 280 Atmospheric sensor doesn\'t seem to be connected to the system.')
    exit(-1)
else:
    # discard first readings from the sensor as they tend to be unreliable
    _ = tph_sensor.temperature_fahrenheit
    _ = tph_sensor.pressure
    _ = tph_sensor.humidity

while True:
    t = tph_sensor.temperature_fahrenheit
    p_pascal = tph_sensor.pressure
    p_atm = p_pascal / 101325 # conversion Pascals to atmospheres
    h = tph_sensor.humidity

    print('Temperature (F): %1.2f' % t)
    print('Pressure (atm): %1.2f' % p_atm)
    print('Humidity (%%): %1.2f' % h)
    print('-')
    sleep(2) # pause for 2 seconds before collecting the next reading
```