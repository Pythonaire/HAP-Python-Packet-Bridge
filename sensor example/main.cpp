// Messageing client with the RH_RF69 class. Using RHDatagram for addressing.
// Packet header contains to, from, if and flags.
#include <Arduino.h>
#include <RHDatagram.h>
#include <RH_RF69.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>
#include "RTCZero.h"

/// Feather M0 w/Radio
#define RF69_FREQ 433.0
#define RFM69_CS      8
#define RFM69_INT     3
#define RFM69_RST     4
#define CLIENT_ADDRESS 10 // RHDatagram
#define SERVER_ADDRESS 1 // RHDatagram

#define VBATPIN       A7 // measuring battery
#define HUMPIN A2 // Pin A2
#define HUMPOWER 12
#define DHTPOWER 11
#define DHTTYPE DHT22
#define DHTPIN A3 // Pin A3, maybe with 10kOhm
DHT_Unified dht(DHTPIN, DHTTYPE);

// Singleton instance of the radio driver
RH_RF69 rf69(RFM69_CS, RFM69_INT);
RHDatagram manager(rf69, CLIENT_ADDRESS);

int sensorHumidity;
int sensorTemperature;
int sensorSoil;
float dhtValues[2];
int sensorVoltage;
uint32_t delayMS;

/* Create an rtc object */
RTCZero rtc;
const bool resetTime = true;
const uint8_t wait = 30;

int ReadBattery() {
  pinMode(VBATPIN, OUTPUT);delay(10);digitalWrite(VBATPIN, HIGH);delay(100);
  float measuredvbat = analogRead(VBATPIN);
  digitalWrite(VBATPIN, LOW);
  measuredvbat *=2; // we divided by 2, so multiply back
  measuredvbat *=3.3; // Multiply by 3.3V, our reference voltage
  measuredvbat /= 1024; // convert to voltage
  // min ADC at 2 Volt = 621 (ignore 0,001)
  // max ADC at 4,2 Volt = 1303 (ignore 0,0009)
  if (measuredvbat > 4.2f) {measuredvbat = 4.2f;}
  if (measuredvbat < 2.4f) {measuredvbat = 2.4f;}
  int result = roundf(100*(measuredvbat-2.4f)/(4.2f-2.4f));
  return result; // value back in percent
 };
 int SoilHumidity() {
  pinMode(HUMPOWER, OUTPUT);delay(10);digitalWrite(HUMPOWER, HIGH);delay(100);
  float measuredsoil = analogRead(HUMPIN);
  digitalWrite(HUMPOWER, LOW);
  float maxvalue = 575; //dry
  float minvalue =275; // difference 300, easier by deviding
  if (measuredsoil > maxvalue){measuredsoil = maxvalue;} 
  else if (measuredsoil < minvalue){measuredsoil = minvalue;} 
  int result = roundf(((-measuredsoil)+maxvalue)/3);
  return result;
 };
 void dht22(float dhtValues[]) {
  pinMode(DHTPOWER, OUTPUT);delay(10);digitalWrite(DHTPOWER, HIGH);delay(100);
  dht.begin();
  sensor_t sensor;
  dht.temperature().getSensor(&sensor);
  dht.humidity().getSensor(&sensor);
  delayMS = sensor.min_delay / 1000;
  delay(delayMS);
  sensors_event_t event;
  dht.temperature().getEvent(&event);
  if (isnan(event.temperature)) {
    //Serial.println(F("Error reading temperature!"));
                               }
      else {
    dhtValues[0] = event.temperature;
          }
  dht.humidity().getEvent(&event);
  if (isnan(event.relative_humidity)) {
    //Serial.println(F("Error reading humidity!"));
            }
  else {
    dhtValues[1] = event.relative_humidity;
      }
  digitalWrite(DHTPOWER, LOW);
 };

void alarmMatch() {
  delay(100);
};

void setup() {
  //Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT); digitalWrite(LED_BUILTIN, LOW); // LED off
  //manual reset the radio
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, HIGH); delay(10);
  digitalWrite(RFM69_RST, LOW); delay(10);
  if (!manager.init()) {
    //Serial.println("init failed"); 
    while (1);};
  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250,
  //  +13dbM (for low power module) and No encryption
  if (!rf69.setFrequency(RF69_FREQ)) { 
    //Serial.println("setFrequency failed"); 
    };
  // If you are using a high power RF69 eg RFM69HW, you *must* set a Tx power with the
  // ishighpowermodule flag set like this:
  rf69.setTxPower(17, true);  // range from 14-20 for power, 2nd arg must be true for 69HCW
  // The encryption key has to be the same as the one in the server
  uint8_t key[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                    0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};
                    rf69.setEncryptionKey(key);

};
void loop() {
  sensorVoltage = ReadBattery();
  sensorSoil = SoilHumidity();
  dht22(dhtValues);
  sensorTemperature = roundf(dhtValues[0]);
  sensorHumidity = roundf(dhtValues[1]);
  char rpacket[60]; // max packet length RFM69 60 Byte
  // create JSON Form to easier produce on Server side
  int n = sprintf(rpacket, "{'Charge':%d,'Soil':%d,'Hum':%d,'Temp':%d}", sensorVoltage,sensorSoil,sensorHumidity,sensorTemperature);
  //Serial.printf("[%s] is a string %d chars long\n",rpacket,n);
  uint8_t radiopacket[n]; // reduce to the needed packet size 'n'
  memcpy(radiopacket, (const char*)rpacket, sizeof(rpacket));
  if (manager.sendto(radiopacket, sizeof(radiopacket), SERVER_ADDRESS))
      {
        manager.waitPacketSent(); // block until the packet is sent
      }
delay(50);
rf69.sleep(); 
rtc.begin(resetTime);
rtc.setAlarmMinutes(wait);
rtc.setAlarmSeconds(0);
rtc.enableAlarm(rtc.MATCH_MMSS);
rtc.attachInterrupt(alarmMatch);
rtc.standbyMode();
};
