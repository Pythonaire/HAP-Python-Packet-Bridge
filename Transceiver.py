##!/usr/bin/env python3
import board
import busio
import logging
import digitalio
import logging, json,requests, socket, time, asyncio
import rfm69_driver
import RPi.GPIO as io

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")
"""
RCV_DEV_VALUES used to cache/store the actual, last values, received by the 433 MHz devices.
format (python dictionary):
{node1:{'key1': key1 value, ...}, node2:{'key1': key1 value,...}, node3:{...}}
"""
RCV_CACHE = {}

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
    NODE = 1 # bridge node id

    @classmethod
    async def http_forwarder(_cls, httpsend):
        url = "http://PiRadio.local:8001/postjson"
        try:
            requests.post(url, json=json.dumps(httpsend)) # create json format and send
        except socket.error as e:
            logging.info('**** request.post got exception {0}'.format(e))
        except:
            logging.info("**** Something else went wrong ****") 

    def __init__(self):
        io.setmode(io.BCM)
        io.setup(self.dio0_pin, io.IN,pull_up_down=io.PUD_DOWN) # set dio0 on GROUND as default


    def start_recv(self): # start DIO detection for reading
        self.rfm69.listen()
        io.add_event_detect(self.dio0_pin, io.RISING, callback = self.mcu_recv)

    def stop_recv(self):
        io.remove_event_detect(self.dio0_pin)

    def mcu_send(self, cmd, node):
        global RCV_CACHE
        ret_counter = 0
        if node in RCV_CACHE:
            del RCV_CACHE[node]
        value = bytes("{}".format(cmd),"UTF-8")
        while not node in RCV_CACHE:
            self.stop_recv()
            self.rfm69.send(value, node, self.NODE, 0, 0)
            self.start_recv()
            time.sleep(0.4) ## 200 ms is set on mcu + 200 ms for server
            ret_counter+=1
        if ret_counter > 1:
            logging.info("**** send/ack retry counter : {0} to node {1} ****".format(ret_counter-1, node)) 

    def mcu_recv(self, irq):
        global RCV_CACHE
        data = self.rfm69.receive(keep_listening= True, rx_filter=self.NODE)
        if data != None:
            from_node = data[1] # header information "from"
            payload = data [4:]
            received_data = json.loads(payload.decode('utf8').replace("'", '"')) # replace ' with " and convert from json to python dict
            logging.info('*** from: {0} with RSSI: {1} got : {2}'.format(from_node, self.rfm69.last_rssi, received_data))
            RCV_CACHE[from_node] = received_data
            if from_node == 10:
                asyncio.run(self.http_forwarder(received_data))

    def receive_cache(self):
        global RCV_CACHE
        return RCV_CACHE