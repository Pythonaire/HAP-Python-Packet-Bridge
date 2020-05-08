
#include <RH_RF69.h>
#include <RHDatagram.h>
#include <Adafruit_LPS35HW.h>
#include <RTCZero.h>

#define POW_AIR A1 //A1
#define POW_WATER A2 //A2
#define VBATPIN  A7 // measuring battery
#define I2C_WATER 0x5C // LPS35HW Water i2c address
#define I2C_AIR 0x5D // LPS35HW AIR i2c address

/// Feather M0 w/Radio
#define RF69_FREQ 433.0
#define RFM69_CS      8
#define RFM69_INT     7
#define RFM69_RST     4

#define CLIENT_ADDRESS 11 // RHDatagram
#define SERVER_ADDRESS 1 // RHDatagram

RH_RF69 rf69(RFM69_CS, RFM69_INT);
RHDatagram manager(rf69, CLIENT_ADDRESS);
Adafruit_LPS35HW Water = Adafruit_LPS35HW();
Adafruit_LPS35HW Air = Adafruit_LPS35HW();

/* Create an rtc object */
RTCZero rtc;
const byte seconds = 00;
const byte minutes = 00;
const byte hours = 10;    
const byte day = 1;
const byte month = 1;
const byte year = 20;

uint8_t sensorVoltage;
int WaterPressure;
int AirPressure;


uint8_t ReadBattery() {
  digitalWrite(VBATPIN, HIGH);delay(10);
  float measuredvbat = analogRead(VBATPIN);
  digitalWrite(VBATPIN, LOW);
  measuredvbat *=2; // we divided by 2, so multiply back
  measuredvbat *=3.3; // Multiply by 3.3V, our reference voltage
  measuredvbat /= 1024; // convert to voltage
  // min ADC at 2 Volt = 621 (ignore 0,001)
  // max ADC at 4,2 Volt = 1303 (ignore 0,0009)
  if (measuredvbat > 4.2f) {measuredvbat = 4.2f;}
  if (measuredvbat < 2.4f) {measuredvbat = 2.4f;}
  uint8_t result = roundf(100*(measuredvbat-2.4f)/(4.2f-2.4f));
  return result; // value back in percent
 };


void setup() {
  //Serial.begin(115200);
  // Wait until serial port is opened
  //while (!Serial) { delay(10); }
  pinMode(LED_BUILTIN, OUTPUT); digitalWrite(LED_BUILTIN, LOW); // LED off
  pinMode(POW_WATER, OUTPUT);pinMode(POW_AIR, OUTPUT);
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, HIGH); delay(10);
  digitalWrite(RFM69_RST, LOW); delay(10);
  if (!manager.init()) {
    //Serial.println("init failed"); 
    while (1);}
  if (!rf69.setFrequency(RF69_FREQ)) 
  { 
    //Serial.println("setFrequency failed"); 
    }
  rf69.setTxPower(18, true);  // range from 14-20 for power, 2nd arg must be true for 69HCW
  // The encryption key has to be the same as the one in the server
  uint8_t key[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 
                    0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};
  rf69.setEncryptionKey(key);
};
void alarmMatch() {
  delay(10);
};
void loop() {
  digitalWrite(POW_WATER, HIGH);delay(500);
  digitalWrite(POW_AIR, HIGH);delay(500);
  if (!Water.begin(I2C_WATER)) {
    //Serial.println("Couldn't find Water chip");
    while (1);
  }
  if (!Air.begin(I2C_AIR)) {
    //Serial.println("Couldn't find Air chip");
    while (1);
  }
  Air.reset();Water.reset();
  sensorVoltage = ReadBattery();
  WaterPressure = roundf(Water.readPressure())+3; // "3" seems this sensor values differing
  AirPressure = roundf(Air.readPressure());
  digitalWrite(POW_WATER, LOW);
  digitalWrite(POW_AIR, LOW);
  char rpacket[60]; // max packet length RFM69 60 Byte
  int n = sprintf(rpacket, "{'Charge': %d,'AP': %d,'WP': %d}",sensorVoltage,AirPressure,WaterPressure);
  //Serial.printf("[%s] is a string %d chars long\n",rpacket,n);
  uint8_t radiopacket[n]; // reduce to the needed packet size 'n'
  memcpy(radiopacket, (const char*)rpacket, sizeof(rpacket));
  manager.sendto(radiopacket, sizeof(radiopacket), SERVER_ADDRESS);
  delay(50);
  rf69.sleep();
  rtc.begin(true);
  rtc.setTime(hours, minutes, seconds);
  rtc.setDate(day, month, year);
  rtc.setAlarmTime(13, 00, 00);
  rtc.enableAlarm(rtc.MATCH_HHMMSS);
  rtc.attachInterrupt(alarmMatch);
  rtc.standbyMode();
};