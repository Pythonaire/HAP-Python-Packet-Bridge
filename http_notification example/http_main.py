#!/usr/bin/env python3
import logging, signal
from pyhap.accessory import Accessory
from HttpAccessory import HttpBridge, HttpBridgeHandler
from pyhap.accessory_driver import AccessoryDriver
from Actors import SwitchRadio
import pyhap.loader as loader

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

dev_loader = loader.get_loader()

def get_bridge(driver):
    http_bridge = HttpBridge(driver=driver,display_name="HTTP Bridge", address=("", 51111))
    #PiRadio = Accessory(display_name="PiRadio",driver=driver, aid=2)  # aid must be unique for all acc. in a bridge
    #PiRadio.add_service(dev_loader.get_service("Switch"))
    #PiRadio.add_characteristic(dev_loader.get_char("On"))
    #PiRadio.add_preload_service('Switch')
    #self.char_on = serv_switch.configure_char('On', setter_callback=self.set_switch)
    #http_bridge.add_accessory(PiRadio)
    http_bridge.add_accessory(SwitchRadio(driver=driver, display_name='PiRadio', aid= 2))
    return http_bridge

driver = AccessoryDriver(port=51826, persist_file='http.state')
driver.add_accessory(accessory=get_bridge(driver))
signal.signal(signal.SIGTERM, driver.signal_handler)
driver.start()

















