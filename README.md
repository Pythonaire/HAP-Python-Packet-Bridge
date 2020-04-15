# HAP-Python-Packet-Radio

Python Homebridge and 433 MHz Sensors - measuring Soil Humidity, Air Humidity and Temperature and send data to the Apple Homekit and other http connected devices.


![Image of hardware](Image1.png)


This repository put together the HAP-Python code from <https://github.com/ikalchev/HAP-python> and the chip driver  <https://github.com/adafruit/Adafruit_CircuitPython_RFM69> with some modification.
Use the linked repository to install these basic libraries. 

Put the files into your prefered path. Instead of "main.py", delivered by HAP-Python, use "async_main.py" to startup.
It is tested with a Raspberry Pi Zero W as a bridge and 3 devices, based on Adafruit Feather 433 MHz RFM69 (M0 SAMD21 mcu and 32u4 mcu).

To change sensor devices, services or characteristics or add additional sensor devices, just place new classes into Sensors.py or change the existing. Changes or new classes needed to declared in "async_main.py" (bridge.add_accessory(your class (driver, 'your name to be displayed')))

## Significant changes/modification

### HAP-Python

* separate the homebridge communication from the sensor device communication
* data buffering and handover by nested python dictionary, no "pickle" or other methods needed (to prevent File read error on SD cards)

* By default, HAP-Python transfer characteristics and services unchanged/transparent. Here, each sensor device has different functions and partially mixed characteristics and services. Ex.: for measuring the water left in a cistern, i use two pressure sensors, calculate the difference. The value could be calculated between 0 and 100 and pushed to the Homekit as CurrentRelativeHumidity, to get the "drop sign" and percent value.

* Each device will be identified by a client id to get the assigned sensor type and characteristic. (client_id -->> sensor classes --->> characteristics -->> values). Using the RHDatagram functionality.

### Adafruit CPython RFM69 driver

* instead of permament looping to read the buffer, GPIO event state is used to detect incoming data.


## Working principals

The sensor device measure and send data along 433 Mhz to the HAP-Python Bridge. To save battery capacity, the sensor unit is set into "deep sleep mode" the finishing the measurement and data transmitting. The sensor unit will waked up by its own RTC clock with a defined interval. (see sensor examples).
The HAP-Python bridge detect incoming data by DIO interrupt (see Transceiver.py). Then convert the data and send them to the Apple Homekit (see Sensor.py).
The Apple Homekit app (user GUI) could check the sensor state at any time. Because of a probably sleeping device the last/actually data are stored in a nested dictionary.  

### additional (if needed)

* send the sensor data to other http connected units (request.get/post). You can uses this method to control http-connected devices (ex. switch characteristics) too.
* to speed up the data exchange between transceiver process and HAP-Python (here a raspberry zero w - single core cpu) in case off multiple sensor devices, the transceiver process runs as python thread (see async_main.py)
