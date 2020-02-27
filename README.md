# HAP-Python-Packet-Radio
Python Homebridge and 433 MHz Sensors

This repository put together the HAP-Python code from https://github.com/ikalchev/HAP-python, https://github.com/adafruit/Adafruit_CircuitPython_RFM69 and contained some modification.

1) HAP-Python modification
    - separate the homebridge communication from the sensor communication
    - data handover by gobal variable, no "pickle" or other methods needed

2) Adafruit Circuit Python RFM69 Tranceiver

    - instead of permament looping to read the buffer, i use the GPIO event state to detect incoming data

3)  additional

    - send the sensor data to other http connected units


Because of maximize the battery capacitiy, i dispence the reliable rfm69 transmission protocol, just use the RH datagram version (no waiting and processing ACK messages from the receiver). In this case, it's a good idea to debounce the signal detection on the receiver. 200 ms works good for me.  
