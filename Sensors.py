from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR
from Transceiver import Radio
import logging


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
        self.value = Radio().check_data()
        if self.value == None:
            self.value = {"Charge": 0, "Soil":0, "Hum":0, "Temp":0 }
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
    """AM2302 combined Sensor, check incoming new data every 60 seconds."""

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
        self.value = Radio().check_data()
        if self.value == None:
            self.value = {"Charge": 0, "Soil":0, "Hum":0, "Temp":0 }
        self.battlevel_char.set_value(self.value["Charge"])
        # the sensor actually defined 2.4 V as 0, 4.2 V ass 100, the SAMD21/RFM69 needs 1.89 V
        # if 0 --> 0.51 V left, that shoud be enough to signaling low Power
        if self.value["Charge"] <= 0: # notify StatusLowBattery
            self.battstatus_char.set_value(1)
        else:
            self.battstatus_char.set_value(0)
        self.hum_char.set_value(self.value["Hum"])
        self.temp_char.set_value(self.value["Temp"])

    def stop(self):
        logging.info("Stopping accessory.")
        
