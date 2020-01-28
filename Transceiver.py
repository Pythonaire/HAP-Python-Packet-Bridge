#!/usr/bin/env python3
import board
import busio
import logging
import asyncio
import digitalio
import json
#import adafruit_rfm69
import rfm69_driver
import RPi.GPIO as io
import requests


logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")
received_data = None # global variable to share received value 


class Radio():
    RADIO_FREQ_MHZ = 433.0
    CS = digitalio.DigitalInOut(board.CE1)
    RESET = digitalio.DigitalInOut(board.D25)
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)    
    rfm69 = rfm69_driver.RFM69(spi, CS, RESET, RADIO_FREQ_MHZ)
    #rfm69 = adafruit_rfm69.RFM69(spi, CS, RESET, RADIO_FREQ_MHZ) 
    #rfm69.tx_power= 20 # for RFM69HCW can by set between -2 and 20
    header = rfm69.preamble_length #set to default length of RadioHead RFM69 library
    # Optionally set an encryption key (16 byte AES key). MUST match both
     # on the transmitter and receiver (or be set to None to disable/the default).
    rfm69.encryption_key = b'\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08'

    
    url = "http://PiRadio.local:8001/postjson"

    def __init__(self):
        self.server_id = 1 # Server header
        self.client_id = None
        io.setmode(io.BCM)

    def detect_dio(self, dio0_pin=None):
        self.dio0_pin = dio0_pin
        self.rfm69.listen()
        io.setup(self.dio0_pin, io.IN,pull_up_down=io.PUD_DOWN)
        logging.info("Start event detection on Pin: {0}".format(self.dio0_pin))
        io.add_event_detect(self.dio0_pin, io.RISING, callback = self.get_data)
       
        
    def get_data(self, irq):
        global received_data
        self.irq = irq
        data = self.rfm69.receive(keep_listening= True, with_header= True, rx_filter=self.server_id)
        if data != None:
            self.client_id = data[1] #client_id 10 
            logging.info('data coming from: {0} with RSSI: {1}'.format(self.client_id, self.rfm69.rssi))
            del data[0:4] # delete the header, just take the payload
            received_data = json.loads(data.decode('utf8').replace("'", '"')) # replace ' with " and convert from json to python dict
            try:
                response = requests.post(self.url, json=json.dumps(received_data)) # create json format and send
                logging.info('**** requests.post got : {}'.format(response))
            except Exception as e:
                logging.info('**** catched Exception is: {}'.format(e))
                pass 
            return received_data
            
    def check_data(self):
        global received_data
        return received_data



