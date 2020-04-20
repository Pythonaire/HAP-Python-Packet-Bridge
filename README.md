# HAP-Python-Packet-Radio

Python Homebridge with 433 MHz based Sensors - measuring and send data to the Apple Homekit and other http connected devices.


![Image of hardware](Image1.png)


This repository put together the HAP-Python code from <https://github.com/ikalchev/HAP-python> and the chip driver  <https://github.com/adafruit/Adafruit_CircuitPython_RFM69> with some modification.
Use the linked repository to install these basic libraries. 

Put the files into your prefered path. Instead of "main.py", delivered by HAP-Python, use "async_main.py" to startup. 
It is tested with a Raspberry Pi Zero W as a bridge and 3 devices, based on Adafruit Feather 433 MHz RFM69 (M0 SAMD21 mcu and 32u4 mcu).

To change sensor devices, services or characteristics or add additional sensor devices, just place new classes into Sensors.py or change the existing. Changes or new classes needed to declared in "async_main.py" (bridge.add_accessory(your class (driver, 'your name to be displayed'))).
The sensor units send data in a defined json-like format (see: examples). If you using your own data description, you need to customize that on both sides - the sensor c++ code and the 'sensor.py'.

## Significant changes/modification

### HAP-Python

* separate the homebridge communication from the sensor device communication
* data buffering and handover by nested python dictionary, no "pickle" or other methods needed (to prevent file read error on Raspberry Pi SD cards)

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

## example SoilHumidity

The sensor measure the battery capacity, air temperature, air humidity and soil humidity - all in percent (0-100) and store them into a json-like format: {'Charge':%d,'Soil':%d,'Hum':%d,'Temp':%d}".
Then transmit the data to the defined server. The sensor itself is defines as client 10, the brigde (RFM69 server) is defined as 1. The packet header contain 'from, to' value.
After that, the sensor go into deep sleep mode until the RTC wake up in the defined time "const uint8_t wait".
The Transceiver.py detect incoming data, decode/convert and store them into nested dictionary (client id and values).In parallel, the data are send with http to a second device (here a OLED display).

The HAP-Python code (Sensor.py) continuously check the dictionary and push the data to the Apple Homekit along the HAP API definition "BatteryService", "HumiditySensor" and "TemperatureSensor".

## HttP notification

If Homekit devices are able to be switched manually, we need the state too. "http_notification example" contain a http-brigde to foreward a notification, send by the switch. In this example, a radio can be switched on/off by the homekit app ( see Actor.py -> SwitchRadio). If the radio is switched on/off manually, it send the state update to the bridge (HttpAccessory.py) 
        notification example form:  {"aid":2,"services": 
                                    {"Switch": 
                                    {"On": true}}} (or "On": false)

