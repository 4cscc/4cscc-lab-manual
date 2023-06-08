(pm-1)=
# Particulate matter sensing to assess indoor air quality

## Introduction

In this lesson you will learn how to set up your PMS5003 particular matter, or
PM, sensor with the hardware provided. You will learn how to connect it to your
Raspberry Pi 400 and the basics of how to get the sensor readings from it using
Python 3. If you are interested in learning more about particulate matter
sensing see [this](https://en.wikipedia.org/wiki/Particulates) page.
    ![pm-sensor-lesson-photos](images/00-pm-sensor-lesson-photo.jpeg)

## Parts list

For this exercise you'll need:
* [Raspberry Pi 400](https://www.sparkfun.com/products/17377) computer
* Sparkfun [Qwiic pHAT Extension](https://www.sparkfun.com/products/17512)
* PMS5003 particular matter sensor
* [Breadboard](https://www.sparkfun.com/products/12002)
* 4 [male to female jumper wires](https://www.sparkfun.com/products/9385)

## 1. Assemble the sensor

The PM sensor has two openings on one side, the air inlet and fan air outlet.

![PM Sensor inlet and fan](images/01-pm-sensor-fan.png)

The PM sensor has a cable connection on the other side. If there is not a cable already connected, follow the _1a. Connecting the PM sensor cable_ instructions. Otherwise, skip that section.

![PM Sensor cable connector](images/02-pm-sensor-connection.png)

#### 1a. Connecting the PM sensor cable

A small green board with 8 pins will connect to the breadboard via a cable connection.

![Small green board](images/03-pm-pin-and-cable.png)

Take the female end (white) of the cable and insert it into the green board connector.
    ![Small green board with cable](images/04-pm-connecting-8pin-and-cable.png)

Take the other female end (white) of the cable and insert it into the PM Sensor.

![PM Sensor with cable](images/06-pm-connecting-to-cable.png)

#### 1b. Assembled sensor

You should now have a pm sensor with the cable attached as shown. On the other end of the cable there should be a green board with 8 pins.

![PM Sensor connected via cable with small green board](images/07-final-pm-connected-to-8pin-by-cable.png)

### 2. Connect the sensor to the breadboard

Insert the 8 pins from the small green board along a column on the breadboard as shown below.

![Breadboard and 8 pins](images/08-8pin-plugged-breadboard.png)

* Collect 4 male-to-female jumper wires. On the small green board, identify the labels TXD, RXD, GND, and VCC.

* Insert the male ends of the into the the following breadboard on the same rows of the breadboard.

![Breadboard with jumper wires](images/breadboard-closeup-pm-sensor-lesson-04-steps-.jpeg)

### 3. Connect the breadboard to the pHAT
* Connect the female end of the GND wire to GND on the pHAT. 

    ![pHAT Extention and GND wire](images/phat-closeup-pm-sensor-lesson-01-steps-.jpeg)

* Connect the female end of the VCC wire to 5V on the pHAT. 
    ![pHAT Extention and VCC wire](images/phat-closeup-pm-sensor-lesson-02-steps-.jpeg)

* Connect the female end of the RXD wire to 14/TXO on the
pHAT.
    ![pHAT Extention Pin 14/TXO](images/phat-closeup-pm-sensor-lesson-03-steps-.jpeg)

* Connect the female end of the TXD wire to 15/RXI on the pHAT. 
    ![pHAT Extention and VCC wire](images/phat-closeup-pm-sensor-lesson-04-steps-.jpeg)


### 4. Final Particulate Matter Diagram
Our complete product of the pm sensor is shown below, our PM sensor is wired to the breadboard and we use jumper wires to connect to the pHAT.

![Finished](images/4pm-sensor-lesson-steps-.jpeg)

## Python 3 code

To use the following code, open a command terminal. Then enter the following command:

```
source ~/code/4cscc-ln/venv/bin/activate
```

If this works you should see `(venv)` on the far left of the text in
your terminal.

Then, enter the following command to start an ipython terminal:

```
ipython
```

Finally, copy paste the following code into the ipython terminal. This will collect data from your PM sensor every 1 second and display the data on the screen. It will run until you press "Control-c" (i.e., press the "control" and "c" keys at the same time).

```python
# Import the library we use to access the sensor
from pms5003 import PMS5003
# We are going to wait between sensor readings so we don't spam too many
from time import sleep


# Create an object representing our sensor
pms5003 = PMS5003()

# Repeat this as long as the program is running
while True:
    # Read the data from the sensor
    pms_reading = pms5003.read()

    # Access and print three specific pieces of data returned by the PM sensor
    print("PM 1.0: %d" % pms_reading.pm_ug_per_m3(1.0))
    print("PM 2.5: %d" % pms_reading.pm_ug_per_m3(2.5))
    print("PM 10.0: %d" % pms_reading.pm_ug_per_m3(10))
    print("")

    # Wait for one second before attempting to read from the sensor again
    sleep(1)

```

This code was adapted from the files found
[here](https://github.com/pimoroni/pms5003-python/tree/master/examples). This
repo contains the source for the pms5003 module we use to read from the sensor.



[def]: images/00pm-sensor-lesson-photo.jpeg