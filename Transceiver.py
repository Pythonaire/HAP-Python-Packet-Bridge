#!/usr/bin/env python3
import board
import busio
import logging
import digitalio
import json
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
            io.add_event_detect(self.dio0_pin, io.RISING, callback = self.get_data)
        except RuntimeError:
            pass

    def send(self, value, to_node):
        value = bytes("{}".format(value),"UTF-8")
        to_node = to_node
        if to_node in RCV_DEV_VALUES: # delete old state
            del RCV_DEV_VALUES[to_node]
        self.stop()
        self.rfm69.send(value, to_node=to_node, from_node= self.NODE, identifier= None, flags= None)
        self.start()

    def stop(self):
        io.remove_event_detect(self.dio0_pin)

    def get_data(self, irq):
        global RCV_DEV_VALUES
        data = self.rfm69.receive(keep_listening= True, rx_filter=self.NODE)
        if data != None:
            from_node = data[1] # header information "from"
            payload = data [4:]
            received_data = json.loads(payload.decode('utf8').replace("'", '"')) # replace ' with " and convert from json to python dict
            logging.info('*** from: {0} with RSSI: {1} got : {2}'.format(from_node, self.rfm69.last_rssi, received_data))
            RCV_DEV_VALUES[from_node] = received_data

    def check_data(self):
        global RCV_DEV_VALUES
        return RCV_DEV_VALUES
