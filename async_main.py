#!/usr/bin/env python3
import logging
import signal
from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_SENSOR
from Transceiver import Radio
from Sensors import SoilSensor, AM2302

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

DIO_0 = 24

proc = Radio().detect_dio(DIO_0)

def get_bridge(driver):
    bridge = Bridge(driver, 'RFMBridge')
    bridge.add_accessory(SoilSensor(driver, 'SoilMoisture'))
    bridge.add_accessory(AM2302(driver, 'AM2302'))
    return bridge

driver = AccessoryDriver(port=51826, persist_file='home.state')
driver.add_accessory(accessory=get_bridge(driver))
signal.signal(signal.SIGTERM, driver.signal_handler)
driver.start()

      




