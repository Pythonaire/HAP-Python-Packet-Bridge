from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR, CATEGORY_SWITCH
from Transceiver import RFMTransceiver
import logging, time

"""Each class represent a device. 
value = Radio().check_data() 'node#' and "key: key value"
format (python dictionary):
{node1:{'key1': key1 value, ...}, node2:{'key1': key1 value,...}, node3:{...}}
"""

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

class SoilSensor(Accessory):
    """Humidity / Soil Sensor, check incoming new data every 60 seconds."""
    category = CATEGORY_SENSOR
    def __init__(self, *args, **kwargs): # with injected rfm69_values
        super().__init__(*args, **kwargs)
        self.name = args[1] # args[1] contained the Sensor Name given
        self.number = args[2] # args[1] contained the Sensor Number given
        serv_soil = self.add_preload_service('HumiditySensor', chars=['CurrentRelativeHumidity'])
        serv_batt = self.add_preload_service('BatteryService', chars=['BatteryLevel','StatusLowBattery'])
        self.hum_char = serv_soil.configure_char('CurrentRelativeHumidity')
        self.battlevel_char = serv_batt.configure_char('BatteryLevel')
        self.battstatus_char = serv_batt.configure_char('StatusLowBattery')

    @Accessory.run_at_interval(30)
    async def run(self):
        received = RFMTransceiver().check_data()
        if self.number not in received: # prevent error on bridge startup / restart
            value = {"Charge": 0, "Soil":0}
        else:
            value = received[self.number]

        self.battlevel_char.set_value(value["Charge"])
        # the sensor actually defined 2.4 V as 0, 4.2 V ass 100, the SAMD21/RFM69 needs 1.89 V
        # if 0 --> 0.51 V left, that shoud be enough to signaling low Power
        if value["Charge"] <= 0: #  notify StatusLowBattery
            self.battstatus_char.set_value(1)
        else:
            self.battstatus_char.set_value(0)
        self.hum_char.set_value(value["Soil"])

    def stop(self):
        logging.info("Stopping accessory.")

class AM2302(Accessory):
    """AM2302 combined Sensor"""

    category = CATEGORY_SENSOR
    def __init__(self, *args, **kwargs): # with injected rfm69_values
        super().__init__(*args, **kwargs)
        self.name = args[1] # args[1] contained the Sensor Name given
        self.number = args[2] # args[1] contained the Sensor Number given
        serv_temp = self.add_preload_service('TemperatureSensor', chars=['CurrentTemperature'])
        serv_hum = self.add_preload_service('HumiditySensor', chars=['CurrentRelativeHumidity'])
        serv_batt = self.add_preload_service('BatteryService', chars=['BatteryLevel','StatusLowBattery'])
        self.temp_char = serv_temp.configure_char('CurrentTemperature')
        self.hum_char = serv_hum.configure_char('CurrentRelativeHumidity')
        self.battlevel_char = serv_batt.configure_char('BatteryLevel')
        self.battstatus_char = serv_batt.configure_char('StatusLowBattery')

    @Accessory.run_at_interval(30)
    async def run(self):
        received = RFMTransceiver().check_data()
        if self.number not in received: # prevent error on bridge startup / restart
            value = {"Charge": 0, "Hum":0, "Temp":0}
        else:
            value = received[self.number]

        self.battlevel_char.set_value(value["Charge"])
        # the sensor actually defined 2.4 V as 0, 4.2 V ass 100, the SAMD21/RFM69 needs 1.89 V
        # if 0 --> 0.51 V left, that shoud be enough to signaling low Power
        if value["Charge"] <= 0: # notify StatusLowBattery
            self.battstatus_char.set_value(1)
        else:
            self.battstatus_char.set_value(0)
        self.hum_char.set_value(value["Hum"])
        self.temp_char.set_value(value["Temp"])

    def stop(self):
        logging.info("Stopping accessory.")

class LPS33HW(Accessory):
    """Distance Sensor, CurrentRelativeHumidity to give back the water value in percent"""
    category = CATEGORY_SENSOR
    def __init__(self, *args, **kwargs): # with injected rfm69_values
        super().__init__(*args, **kwargs)
        self.name = args[1] # args[1] contained the Sensor Name given
        self.number = args[2] # args[1] contained the Sensor Number given
        serv_cist = self.add_preload_service('HumiditySensor', chars=['CurrentRelativeHumidity'])
        serv_batt = self.add_preload_service('BatteryService', chars=['BatteryLevel','StatusLowBattery'])
        self.cist_char = serv_cist.configure_char('CurrentRelativeHumidity')
        self.battlevel_char = serv_batt.configure_char('BatteryLevel')
        self.battstatus_char = serv_batt.configure_char('StatusLowBattery')

    @Accessory.run_at_interval(30)
    async def run(self):
        received = RFMTransceiver().check_data()
        if self.number not in received: # prevent error on bridge startup / restart
            value = {"Charge":0,"AP": 0,"WP":0,"DP":0}
        else:
            value = received[self.number]
        self.battlevel_char.set_value(value["Charge"])
        # the sensor actually defined 2.4 V as 0, 4.2 V ass 100, the SAMD21/RFM69 needs 1.89 V
        # if 0 --> 0.51 V left, that shoud be enough to signaling low Power
        if value["Charge"] <= 0: #  notify StatusLowBattery
            self.battstatus_char.set_value(1)
        else:
            self.battstatus_char.set_value(0)
        # value["DP"] is the difference between AP and WP, the measured pressure 
        # the sensor stands on 1,1 meter beneath the cistern top = 108 hPa + air pressure
        maxValue = 108
        if value["DP"] <= 0:
            WaterPercent = 0
        else:
            WaterPercent = value["DP"] * 100 / maxValue
        self.cist_char.set_value(WaterPercent)

    def stop(self):
        logging.info("Stopping accessory.")

class WaterPump(Accessory):
    """Switch for immension pump, state request with FF, switch with 0 and 1 by HAP switch characteristics"""
    category = CATEGORY_SWITCH
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.name = args[1] # args[1] contained the device/class Name given
        self.number = args[2] # args[2] contained the device number given
        serv_switch = self.add_preload_service('Switch')
        self.char_on = serv_switch.configure_char('On', setter_callback=self.set_switch)
        logging.info("**** Check the state of node #{}, found in Device.json ***".format(self.number))
        self.get_switch() # get the initial state for faster startup
        self.char_on = serv_switch.configure_char('On', getter_callback=self.get_switch)
        
    def set_switch(self, value): #value can be 1 or 0
        #start = time.monotonic()
        RFMTransceiver().mcu_send(value, self.number)
        r = self.request_state()
        #end = time.monotonic() - start
        #logging.info("**** run time: {} ***".format(end))
        self.char_on.set_value(r)

    def get_switch(self):
        value = "FF"
        RFMTransceiver().mcu_send(value, self.number)
        r = self.request_state()
        self.char_on.set_value(r)
        return r

    def request_state(self):
        ACK = None
        while ACK == None:
            try:
                ACK = RFMTransceiver().check_data()[self.number]['ACK']
            except:
                time.sleep(0.1)
        return ACK
        
    def stop(self):
        logging.info("Stopping accessory.")
