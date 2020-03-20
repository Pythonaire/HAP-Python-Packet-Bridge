from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR
from Transceiver import Radio
import logging

"""Each class represent a sensor with values and the sensor powering battery state. 
self.value = Radio().check_data() deliver the data sended by a device and contain 'client_id', 
that represent the device. 
If a device contained any different sensor types, powered by the same battery,
the battery state might be duplicate.
The data sended by a device are stored in a nested python dictionary and will be automaticcaly updated.
nested dict: {client_id1:{'data1': xxx, ...}, client_id2:{'data1:...}, ....}
The right assignment "client_id" and awaiting value iss needed. 
"""

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

class SoilSensor(Accessory):
    """Humidity / Soil Sensor, check incoming new data every 60 seconds."""
    category = CATEGORY_SENSOR
    def __init__(self, *args, **kwargs): # with injected rfm69_values
        super().__init__(*args, **kwargs)
        self.name = args[1] # args[1] contained the Sensor Name given
        serv_soil = self.add_preload_service('HumiditySensor', chars=['CurrentRelativeHumidity'])
        serv_batt = self.add_preload_service('BatteryService', chars=['BatteryLevel','StatusLowBattery'])
        self.hum_char = serv_soil.configure_char('CurrentRelativeHumidity')
        self.battlevel_char = serv_batt.configure_char('BatteryLevel')
        self.battstatus_char = serv_batt.configure_char('StatusLowBattery')

    @Accessory.run_at_interval(30)
    async def run(self):
        self.received = Radio().check_data()
        if 10 not in self.received: # prevent error on bridge startup / restart
            self.value = {"Charge": 0, "Soil":0}
        else:
            self.value = self.received[10]

        self.battlevel_char.set_value(self.value["Charge"])
        # the sensor actually defined 2.4 V as 0, 4.2 V ass 100, the SAMD21/RFM69 needs 1.89 V
        # if 0 --> 0.51 V left, that shoud be enough to signaling low Power
        if self.value["Charge"] <= 0: #  notify StatusLowBattery
            self.battstatus_char.set_value(1)
        else:
            self.battstatus_char.set_value(0)
        self.hum_char.set_value(self.value["Soil"])
            
    
    def stop(self):
        logging.info("Stopping accessory.")

class AM2302(Accessory):
    """AM2302 combined Sensor"""

    category = CATEGORY_SENSOR
    def __init__(self, *args, **kwargs): # with injected rfm69_values
        super().__init__(*args, **kwargs)
        self.name = args[1] # args[1] contained the Sensor Name given
        serv_temp = self.add_preload_service('TemperatureSensor', chars=['CurrentTemperature'])
        serv_hum = self.add_preload_service('HumiditySensor', chars=['CurrentRelativeHumidity'])
        serv_batt = self.add_preload_service('BatteryService', chars=['BatteryLevel','StatusLowBattery'])
        self.temp_char = serv_temp.configure_char('CurrentTemperature')
        self.hum_char = serv_hum.configure_char('CurrentRelativeHumidity')
        self.battlevel_char = serv_batt.configure_char('BatteryLevel')
        self.battstatus_char = serv_batt.configure_char('StatusLowBattery')

    @Accessory.run_at_interval(30)
    async def run(self):
        self.received = Radio().check_data()
        if 10 not in self.received: # prevent error on bridge startup / restart
            self.value = {"Charge": 0, "Hum":0, "Temp":0}
        else:
            self.value = self.received[10]

        self.battlevel_char.set_value(self.value["Charge"])
        # the sensor actually defined 2.4 V as 0, 4.2 V ass 100, the SAMD21/RFM69 needs 1.89 V
        # if 0 --> 0.51 V left, that shoud be enough to signaling low Power
        if self.value["Charge"] <= 0: # notify StatusLowBattery
            self.battstatus_char.set_value(1)
        else:
            self.battstatus_char.set_value(0)
        self.hum_char.set_value(self.value["Hum"] - 2) # - 2 precision
        self.temp_char.set_value(self.value["Temp"])

    def stop(self):
        logging.info("Stopping accessory.")