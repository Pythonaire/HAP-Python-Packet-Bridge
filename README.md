# HAP-Python-Packet-Radio
Python Homebridge and 433 MHz Sensors

This repository put together the HAP-Python code from https://github.com/ikalchev/HAP-python and  https://github.com/adafruit/Adafruit_CircuitPython_RFM69 with some modification.
Use the linked repository to install these basic libraries. 

Put the files into your prefered path. Instead of "main.py", delivered by HAP-Python, use "ansync_main.py" to startup.

1) HAP-Python modification
    - separate the homebridge communication from the sensor communication
    - data handover by global variable, no "pickle" or other methods needed

2) Adafruit Circuit Python RFM69 library modification

    - instead of permament looping to read the buffer, i use the GPIO event state to detect incoming data

3)  additional

    - send the sensor data to other http connected units

The actually Adafruit driver version doesnt support the RHReliableDatagram functions. On other hand, i made this repository to transmit data from a battery powered sensor devices (Adafruit Feather M0 RFM69) - battery capacity is important. In case of bad transmissions, the handling of "bad packets" can leads into long cycles of send/receive actions until the packet is reliable transmitted, that could drain the battery fast.
Because of that, on the sensor side i use the RHDatagram library, a bit higher "Reliability" than the pure RHGeneric driver, but without SEND/ACK etc.
By using the GPIO event control, it's a good idea to debounce the signal detection on the receiver. 200ms works good for me.
