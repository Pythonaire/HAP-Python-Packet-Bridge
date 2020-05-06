#!/usr/bin/env python3
import logging, signal, json
from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from Transceiver import RFMTransceiver
import Devices
logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

"""
read defined devices from Device.json once on startup

devices --> device number

example:
{ "device1": device1 number, "device2": device2 number, ... } 

Each device (" ex. device1", etc.) refering to a device class, which needed to found by import 
The bridge will loading the refering device class as accessory

"""
file = open("Devices.json","r")
devices = json.load(file)
file.close()

logging.info(" *** initializing the RFM69 Transmitter ***")
RFMTransceiver().start_recv()


def get_bridge(driver):
    # define and store accessory <--> RFM69_node id's 
    bridge = Bridge(driver, 'RFM69Gateway')
    for item in devices:
        num = devices[item]
        my_class = getattr(Devices,item)
        bridge.add_accessory(my_class(num, driver, item))
        logging.info('****** load Accessory: {0}, Number: {1} *****'.format(item, num))
    #for manually use, example: bridge.add_accessory(your class(driver, 'your device name', node number))
    return bridge

driver = AccessoryDriver(port=51826, persist_file='home.state')
driver.add_accessory(accessory=get_bridge(driver))
signal.signal(signal.SIGTERM, driver.signal_handler)
driver.start()