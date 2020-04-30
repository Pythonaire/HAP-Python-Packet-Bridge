#!/usr/bin/env python3
import logging
import signal
from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from Transceiver import RFMTransceiver
from Devices import SoilSensor, AM2302, LPS33HW, WaterPump
import json

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

"""
read defined devices from Device.json once on startup

devices --> device number

example:
{ "device1": device1 number, "device2": device2 number, ... } 

Each device (" ex. device1", etc.) refering to a device class, which needed to found by import 
The bridge will loading the refering device class as accessory
The device number refering to the physical node in the network. it could have any "devices"/sensors/actors
"""
file = open("Devices.json","r")
devices = json.load(file)
file.close()

logging.info(" *** initializing the RFM69 Transmitter ***")
RFMTransceiver().start()

def get_bridge(driver):
    # define and store accessory <--> RFM69_node id's 
    bridge = Bridge(driver, 'RFMTest')
    for item in devices:
        num = devices[item]
        bridge.add_accessory(globals()[item](driver, item, num))
        logging.info('****** load Accessory: {0}, Number: {1} *****'.format(item, num))
    # for manually import devices:
    # example: bridge.add_accessory(AM2302(driver, 'AM2302', <here the node number>))
    return bridge

driver = AccessoryDriver(port=51826, persist_file='home.state')
driver.add_accessory(accessory=get_bridge(driver))
signal.signal(signal.SIGTERM, driver.signal_handler)
driver.start()
