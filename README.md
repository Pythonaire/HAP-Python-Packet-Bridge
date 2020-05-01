# HAP-Python-Packet-Bridge

Python Homebridge for 433 MHz based sensors and actors .

![Image of hardware](Image1.png)

This repository put together the HAP-Python code from <https://github.com/ikalchev/HAP-python> and the chip driver  <https://github.com/adafruit/Adafruit_CircuitPython_RFM69> with some modification.

## Installation

install HAP-Python

```
pip3 install HAP-python[QRCode]
```

* copy "main.py", "rfm69_driver.py", "Transceiver.py", "Devices.py" and "Devices.json" to you prefered path,
* Prepare/modify "Devices.py" and "Device.json" with your own devices,
* Create your own remote devices, see "sensor_example",
* start the bridge as systemd service.

All is tested with a Raspberry Pi Zero W as a bridge and 3 devices, based on Adafruit Feather 433 MHz RFM69 (M0 SAMD21 mcu and 32u4 mcu).

## Working principle (Device.json, Devices.py and main.py)

"Device.json" have to contain all device, you like to use. "Device.json" is json-like formated : {"device name": node number, "device name": node number, ....}". The key "device name" must correspond to the class name in "Device.py". Once defined and started the "main.py" will read "Devices.json", load all devices, node id's and publish them to the Apple Homekit. For testing, you can bypass the automatic, see "main.py" function "get_bridge()". The communication to 433 Mhz binded devices is separated in "Transceiver.py" and will started automatically.

## one way or two way communication - Transceiver.py

The 433 MHz packet communication is separated in "Transceiver.py". Incomimg data are detected by interrupt (here GPIO(BCM) 24) and cached in a dictionary to prevent useless network traffic.

### one way - example CATEGORY_SENSOR

The mcu device itself send data in a needed interval - see "sensor example". The transceiver store the data in a dictionary. The bridge HAP side check continously the transceiver cache, here in a 30 seconds interval, and push the values to the homekit - see CATEGORY_SENSOR example. This helps to preserve capacity on battery powered devices, because this devices can go into deep sleep until the next, self defined, send action. The mcu state will never be triggered.

### two way - example CATEGORY_SWITCH

Switches, for example, often be controlled manually and per software in parallel. To get the real state, a "send/confim/state" interaction is needed. Here, we using "FF" for a status request, "0" for Off, "1" for On. The correct state will be confirmed by the mcu with a {"ACK": value}. Additional on bridge startup, the switch start state will be checked - see class "WaterPump" and the corresponding "switch.cpp" for the mcu, how it can work.

## RFM69 driver

"rfm69_driver" is a modied driver version (original adafruit driver mention above) for the RFM69 chip set to work with a interrupt set by the RFM69 chip, instead of continuously checking the chip buffer.

## AddOn - forward weather data

"Transceiver.py" contained a function "http_forwarder" to transmit weather data to a additional http device to display data in a interval of 30 minutes (setInterval function).
