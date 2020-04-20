from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SWITCH
import logging
import requests, socket

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

class SwitchRadio(Accessory):
    """Turn a local Radio on/off."""
    category = CATEGORY_SWITCH
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        serv_switch = self.add_preload_service('Switch')
        self.char_on = serv_switch.configure_char('On', setter_callback=self.set_switch)
        #self.state = None
        self.urlSetState = "http://PiRadio.local:8001/setState"

    def set_switch(self, value):
        try:
            requests.post(self.urlSetState)
        except socket.error as e:
            logging.info('**** request.post got exception {0}'.format(e)) 

    def stop(self):
        super().stop()
