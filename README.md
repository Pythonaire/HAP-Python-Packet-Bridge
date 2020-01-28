# HAP-Python-Packet-Radio
Python Homebridge and 433 MHz Sensors

This repository put together the HAP-Python code from https://github.com/ikalchev/HAP-python, https://github.com/adafruit/Adafruit_CircuitPython_RFM69 and contained some modification.

1) HAP-Python modification
    - separate the homebridge communication from the sensor communication
    - enable 433 MHz radio packet
    - enable silent sensor values updates; means, trigger incoming data in the background and provide them to the homekit interface. Send the data each 30 minutes  to Apple homekit

2) Adafruit Circuit Python RFM69 Tranceiver

    - instead of permament looping to read the buffer, trigger the GPIO event state DIO of incoming data

3)  additional

    - send the sensor data to other http connected units

