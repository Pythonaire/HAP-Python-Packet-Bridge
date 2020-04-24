// Messageing client with the RH_RF69 class. Using RHDatagram for addressing.
// Packet header contains to, from, if and flags.
#include <Arduino.h>
#include <RH_RF69.h>
#include <RHDatagram.h>
#include <Adafruit_LPS35HW.h>
#include <RTCZero.h>

/// Feather M0 w/Radio
#define RF69_FREQ 433.0
#define RFM69_CS      8
#define RFM69_INT     7
#define RFM69_RST     4

#define POW_AIR A1 //A1
#define POW_WATER A2 //A2
#define CLIENT_ADDRESS 11 // RHDatagram
#define SERVER_ADDRESS 1 // RHDatagram
#define VBATPIN  A7 // measuring battery
#define I2C_WATER 0x5C // LPS35HW Water i2c address
#define I2C_AIR 0x5D // LPS35HW AIR i2c address

RH_RF69 rf69(RFM69_CS, RFM69_INT);
RHDatagram manager(rf69, CLIENT_ADDRESS);
Adafruit_LPS35HW Water = Adafruit_LPS35HW();
Adafruit_LPS35HW Air = Adafruit_LPS35HW();

int sensorVoltage;
float sensor_values[2];
bool state;
/* Create an rtc object */
RTCZero rtc;
const byte seconds = 00;
const byte minutes = 00;
const byte hours = 10;    
const byte day = 1;
const byte month = 1;
const byte year = 20;

int ReadBattery() {
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
  int result = roundf(100*(measuredvbat-2.4f)/(4.2f-2.4f));
  return result; // value back in percent
 };

void ReadSensors(float sensor_values[]) {
  float pressure = 0.00;
  digitalWrite(POW_WATER, HIGH);delay(10);
  Water.begin_I2C(I2C_WATER);
  Water.setDataRate(LPS35HW_RATE_ONE_SHOT);
  Water.takeMeasurement();
  for (int i=0; i < 3; i++){
    pressure = pressure + Water.readPressure();
    delay(500);
  }
  sensor_values[0]=pressure/3;
  digitalWrite(POW_WATER, LOW);
  pressure = 0.00;
  digitalWrite(POW_AIR, HIGH);delay(10);
  Air.begin_I2C(I2C_AIR);
  Air.setDataRate(LPS35HW_RATE_ONE_SHOT);
  Air.takeMeasurement();
  for (int i=0; i < 3; i++){
    pressure = pressure + Air.readPressure();
    delay(500);
  }
  sensor_values[1]=pressure/3;
  //sensor_values[1]=Air.readPressure();
  digitalWrite(POW_AIR, LOW);
};
void setup() {
  //Serial.begin(115200);
  //while (!Serial) { delay(1);}
  pinMode(VBATPIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT); digitalWrite(LED_BUILTIN, LOW); // LED off
  pinMode(POW_WATER, OUTPUT);pinMode(POW_AIR, OUTPUT);
  // manual reset the radio
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, HIGH); delay(10);
  digitalWrite(RFM69_RST, LOW); delay(10);
  if (!manager.init()) {
    //Serial.println("init failed"); 
    while (1);}
  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250,
  //  +13dbM (for low power module) and No encryption
  if (!rf69.setFrequency(RF69_FREQ)) 
  { 
    //Serial.println("setFrequency failed"); 
    }
  // If you are using a high power RF69 eg RFM69HW, you *must* set a Tx power with the
  // ishighpowermodule flag set like this:
  rf69.setTxPower(17, true);  // range from 14-20 for power, 2nd arg must be true for 69HCW
  // The encryption key has to be the same as the one in the server
  uint8_t key[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 
                    0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};
  rf69.setEncryptionKey(key);
};
void alarmMatch() {
  delay(10);
};
void loop() {
  sensorVoltage = ReadBattery();
  ReadSensors(sensor_values);
  int WaterPressure = roundf(sensor_values[0]);
  int AirPressure = roundf(sensor_values[1]);
  int PressureDiff = WaterPressure - AirPressure;
  //Serial.print("Pressure Diff: ");
  //Serial.print(PressureDiff);
  //Serial.println(" hPa");
  char rpacket[60]; // max packet length RFM69 60 Byte
   // create JSON Form to easier produce on Server side
  int n = sprintf(rpacket, "{'Charge':%d,'AP': %d,'WP':%d,'DP':%d}", sensorVoltage,AirPressure,WaterPressure,PressureDiff);
  //Serial.print("packet length: ");
  //Serial.print(n);
  //Serial.print(",  data: ");
  //Serial.println(rpacket);
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