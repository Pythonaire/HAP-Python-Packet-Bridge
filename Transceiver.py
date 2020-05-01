#!/usr/bin/env python3
import board
import busio
import logging
import digitalio
import logging, json, threading, requests, socket
import rfm69_driver
import RPi.GPIO as io

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")
"""
RCV_DEV_VALUES used to cache/store the actual, last values, received by the 433 MHz devices.
format (python dictionary):
{node1:{'key1': key1 value, ...}, node2:{'key1': key1 value,...}, node3:{...}}
"""
RCV_DEV_VALUES = {}

class RFMTransceiver():
    RADIO_FREQ_MHZ = 433.0
    CS = digitalio.DigitalInOut(board.CE1)
    RESET = digitalio.DigitalInOut(board.D25)
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    rfm69 = rfm69_driver.RFM69(spi, CS, RESET, RADIO_FREQ_MHZ)
    rfm69.tx_power= 14 # for RFM69HCW can by set between -2 and 20
    header = rfm69.preamble_length #set to default length of RadioHead RFM69 library
    # Optionally set an encryption key (16 byte AES key). MUST match both
    # on the transmitter and receiver (or be set to None to disable/the default).
    rfm69.encryption_key = b'\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08'
    dio0_pin = 24 # Pin connected to the RFM69 chip DIO0
    NODE = 2 # bridge node id

    def __init__(self):
        io.setmode(io.BCM)
        io.setup(self.dio0_pin, io.IN,pull_up_down=io.PUD_DOWN) # set dio0 on GROUND as default

    def start(self): # start DIO detection for reading
        self.rfm69.listen()
        try:
            io.add_event_detect(self.dio0_pin, io.RISING, callback = self.mcu_recv)
        except RuntimeError:
            pass

    def stop(self):
        io.remove_event_detect(self.dio0_pin)

    def mcu_send(self, value, to_node):
        value = bytes("{}".format(value),"UTF-8")
        to_node = to_node
        if to_node in RCV_DEV_VALUES: # delete old state
            del RCV_DEV_VALUES[to_node]
        self.stop()
        self.rfm69.send(value, to_node=to_node, from_node= self.NODE, identifier= None, flags= None)
        self.start()

    def mcu_recv(self, irq):
        global RCV_DEV_VALUES
        data = self.rfm69.receive(keep_listening= True, rx_filter=self.NODE)
        if data != None:
            from_node = data[1] # header information "from"
            payload = data [4:]
            received_data = json.loads(payload.decode('utf8').replace("'", '"')) # replace ' with " and convert from json to python dict
            logging.info('*** from: {0} with RSSI: {1} got : {2}'.format(from_node, self.rfm69.last_rssi, received_data))
            RCV_DEV_VALUES[from_node] = received_data

    def setInterval(interval): # for anync looping the rfm69.receiver
        def decorator(function):
            def wrapper(*args, **kwargs):
                stopped = threading.Event()
                def loop(): # executed in another thread
                    while not stopped.wait(interval): # until stopped
                        called_thread = threading.Thread(target=function(*args, **kwargs)) # function(*args, **kwargs) for decorator
                        called_thread.start()
                        called_thread.join() # wait for finishing 
                t = threading.Thread(target=loop)
                t.daemon = True # stop if the program exits
                t.start()
                return stopped
            return wrapper
        return decorator

    @setInterval(1800)
    def http_forwarder(self):
        global RCV_DEV_VALUES
        url = "http://PiRadio.local:8001/postjson"
    
        if "10" not in RCV_DEV_VALUES: # prevent error on bridge startup / restart
            value = { "Hum":0, "Temp":0}
        else:
            value = RCV_DEV_VALUES["10"]
        try:
            requests.post(url, json=json.dumps(value)) # create json format and send
        except socket.error as e:
            logging.info('**** request.post got exception {0}'.format(e))
        except:
            logging.info("**** Something else went wrong ****")

    def check_data(self):
        global RCV_DEV_VALUES
        return RCV_DEV_VALUES
