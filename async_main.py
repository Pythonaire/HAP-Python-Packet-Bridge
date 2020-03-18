#!/usr/bin/env python3
import logging
import signal, threading
from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_SENSOR
from Transceiver import Radio
from Sensors import SoilSensor, AM2302, Ultrasonic

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

proc = Radio()
proc_thread = threading.Thread(target=proc.start())
proc_thread.daemon = True
proc_thread.start()

def get_bridge(driver):
    bridge = Bridge(driver, 'RFMBridge')
    bridge.add_accessory(SoilSensor(driver, 'SoilMoisture'))
    bridge.add_accessory(AM2302(driver, 'AM2302'))
    bridge.add_accessory(Ultrasonic(driver, 'Cistern'))
    return bridge

driver = AccessoryDriver(port=51826, persist_file='home.state')
driver.add_accessory(accessory=get_bridge(driver))
signal.signal(signal.SIGTERM, driver.signal_handler)
driver.start()

      




