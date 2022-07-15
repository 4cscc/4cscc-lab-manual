# VOC sensing

In this lesson you'll collect readings on air quality as measured by the concentration of volatile organic compounds, or VOCs, in the air around your computer (and around you, if you're sitting near your computer). You can learn more about VOCs on [this page](https://en.wikipedia.org/wiki/Volatile_organic_compound), and about the VOC Index, which the sensor we'll be using in this experiment provides, in [this document](https://bit.ly/3AE9qdE).

## Parts list

For this exercise you'll need:
* [Raspberry Pi 400](https://www.sparkfun.com/products/17377) computer
* Sparkfun [Qwiic pHAT Extension](https://www.sparkfun.com/products/17512)
* Sparkfun [SGP40 Air Quality Sensor](https://www.sparkfun.com/products/18345)
* Sparkfun [Qwiic cable (50mm)](https://www.sparkfun.com/products/17260)

## Python 3 code

To use the following code, open a command terminal. Then enter the following command:

```
source ~/code/4cscc-ln/venv/bin/activate
```

Then, enter the following command to start an ipython terminal:

```
ipython
```

Finally, copy paste the following code into the ipython terminal. This will collect from your SGP40 sensor every 2 seconds and display them on the screen. It will run until you press "Control-c" (i.e., press the "control" and "c" keys at the same time).

```python
from time import sleep
import qwiic_sgp40

voc_sensor = qwiic_sgp40.QwiicSGP40()

if voc_sensor.begin() != 0:
    print('SGP 40 VOC sensor doesn\'t seem to be connected to the system.')
    exit(-1)

while True:
    voc_index = voc_sensor.get_VOC_index()
    print('VOC Index: %d' % voc_index)
    sleep(2) # pause for 2 seconds before collecting the next reading
```