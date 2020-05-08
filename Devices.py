#!/usr/bin/env python3
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR, CATEGORY_SPRINKLER
from Transceiver import RFMTransceiver
import logging, time, threading, asyncio

"""Each class represent a device. 
value = Radio().check_data() 'node#' and "key: key value"
format (python dictionary):
{node1:{'key1': key1 value, ...}, node2:{'key1': key1 value,...}, node3:{...}}
"""

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

class SoilSensor(Accessory):
    """Humidity / Soil Sensor, check incoming new data every 60 seconds."""
    category = CATEGORY_SENSOR
    def __init__(self, node,  *args, **kwargs): # with injected rfm69_values
        super().__init__(*args, **kwargs)
        self.name = args[1] # args[1] contained the Sensor Name given
        self.number = node # node number
        serv_soil = self.add_preload_service('HumiditySensor', chars=['CurrentRelativeHumidity'])
        serv_batt = self.add_preload_service('BatteryService', chars=['BatteryLevel','StatusLowBattery'])
        self.hum_char = serv_soil.configure_char('CurrentRelativeHumidity')
        self.battlevel_char = serv_batt.configure_char('BatteryLevel')
        self.battstatus_char = serv_batt.configure_char('StatusLowBattery')

    @Accessory.run_at_interval(30)
    async def run(self):
        received = RFMTransceiver().receive_cache()
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

class AM2302(Accessory):
    """AM2302 combined Sensor"""

    category = CATEGORY_SENSOR
    def __init__(self, node, *args, **kwargs): # with injected rfm69_values
        super().__init__(*args, **kwargs)
        self.name = args[1] # args[1] contained the Sensor Name given
        self.number = node # args[1] contained the Sensor Number given
        serv_temp = self.add_preload_service('TemperatureSensor', chars=['CurrentTemperature'])
        serv_hum = self.add_preload_service('HumiditySensor', chars=['CurrentRelativeHumidity'])
        serv_batt = self.add_preload_service('BatteryService', chars=['BatteryLevel','StatusLowBattery'])
        self.temp_char = serv_temp.configure_char('CurrentTemperature')
        self.hum_char = serv_hum.configure_char('CurrentRelativeHumidity')
        self.battlevel_char = serv_batt.configure_char('BatteryLevel')
        self.battstatus_char = serv_batt.configure_char('StatusLowBattery')

    @Accessory.run_at_interval(30)
    async def run(self):
        received = RFMTransceiver().receive_cache()
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


class LPS33HW(Accessory):
    """Distance Sensor, CurrentRelativeHumidity to give back the water value in percent"""
    category = CATEGORY_SENSOR
    def __init__(self, node, *args, **kwargs): # with injected rfm69_values
        super().__init__(*args, **kwargs)
        self.name = args[1] # args[1] contained the Sensor Name given
        self.number = node # args[1] contained the Sensor Number given
        serv_cist = self.add_preload_service('HumiditySensor', chars=['CurrentRelativeHumidity'])
        serv_batt = self.add_preload_service('BatteryService', chars=['BatteryLevel','StatusLowBattery'])
        self.cist_char = serv_cist.configure_char('CurrentRelativeHumidity')
        self.battlevel_char = serv_batt.configure_char('BatteryLevel')
        self.battstatus_char = serv_batt.configure_char('StatusLowBattery')

    @Accessory.run_at_interval(30)
    async def run(self):
        received = RFMTransceiver().receive_cache()
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
        # the sensor stands on 1,15 meter beneath cistern top (plus 50 cm maintenance tube = 165 cm) = 113 hPa
        DiffPressure = value["WP"] - value["AP"]
        if DiffPressure <=0: 
            WaterPercent = 0
        elif DiffPressure >= 113:
            WaterPercent = 100
        else:
            WaterPercent = DiffPressure * 100 / 113
        self.cist_char.set_value(WaterPercent)


class WaterPump(Accessory):
    """Switch for immension pump, state request with FF, switch with 0 and 1 """
    category = CATEGORY_SPRINKLER

    @classmethod
    def requestrfm(_cls, cmd, node):
        RFMTransceiver().mcu_send(cmd, node)
        while not node in RFMTransceiver().receive_cache():
            time.sleep(0.1)
        ACK = RFMTransceiver().receive_cache()[node]["ACK"]
        return ACK
    
    def __init__(self, node, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.name = args[1] # args[1] contained the device/class Name given
        self.node = node # args[2] contained the device number given
        confirm = self.requestrfm( 0, self.node) # startup value
        serv_valve = self.add_preload_service('Valve',[
            'Active',
            'ValveType',
            'InUse',
            'SetDuration',
            'RemainingDuration',
            'IsConfigured',
            'Name'
        ])
        serv_valve.configure_char('Name', value = "Immension Pump")
        serv_valve.configure_char('ValveType', value = 1)
        serv_valve.configure_char('IsConfigured', value = 1)
        self.active_on = serv_valve.configure_char('Active', setter_callback=self.set_state)
        self.active_state = serv_valve.configure_char('Active', getter_callback=self.get_state)
        self.inUse = serv_valve.configure_char('InUse', value = confirm)
        self.duration = serv_valve.configure_char('SetDuration', value = 0) # value in seconds
        self.rem_duration = serv_valve.configure_char('RemainingDuration')

    def duration_off(self):
        confirm = self.requestrfm(0, self.node)
        self.active_on.set_value(0)
        self.inUse.set_value(confirm)
        self.inUse.notify()
        self.rem_duration.set_value(0)
        self.duration.set_value(0)


    def set_state(self, value):
        duration = self.duration.get_value()
        self.rem_duration.set_value(duration)
        if value ==1 and duration > 0:
            confirm = self.requestrfm(value, self.node)
            self.inUse.set_value(confirm)
            self.inUse.notify()
            timer = threading.Timer(duration, self.duration_off)
            timer.start()
        else:
            self.rem_duration.set_value(0)
            confirm = self.requestrfm(value, self.node)
            self.inUse.set_value(confirm)
            self.inUse.notify()
        return value

    def get_state(self):
        if self.node not in RFMTransceiver().receive_cache():
            cached = self.requestrfm("FF", self.node)
        else:
            cached = RFMTransceiver().receive_cache()[self.node]['ACK']
            self.active_state.set_value(cached)
            self.inUse.set_value(cached)
            self.inUse.notify()
            return cached