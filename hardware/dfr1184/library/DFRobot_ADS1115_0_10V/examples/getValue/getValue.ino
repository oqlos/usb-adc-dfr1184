/*!
 * @file get_advalue.ino
 * @brief Run this routine to get the voltage
 * @copyright    Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
 * @license      The MIT License (MIT)
 * @author [lr](rong.li@dfrobot.com)
 * @version V1.0.0
 * @date 2024-07-23
 * @url https://github.com/DFRobot/DFRobot_ADS1115_0_10V
 */
#include <DFRobot_ADS1115_0_10V.h>

//use I2C for communication, but use the serial port for communication if the line of codes were masked
// #define I2C_COMMUNICATION 

#define MODULE_I2C_ADDRESS 0x4A
#ifdef  I2C_COMMUNICATION
  DFRobot_ADS1115_I2C ads1115(&Wire, MODULE_I2C_ADDRESS);
  
 /* ---------------------------------------------------------------------------------------------------------------------
  *    board   |             MCU                | Leonardo/Mega2560/M0 |    UNO    | ESP8266 | ESP32 |  microbit  |   m0  |
  *     VCC    |            3.3V/5V             |        VCC           |    VCC    |   VCC   |  VCC  |     X      |  vcc  |
  *     GND    |              GND               |        GND           |    GND    |   GND   |  GND  |     X      |  gnd  |
  *     RX     |              TX                |     Serial1 TX1      |     5     |   5/D6  | 26/D3 |     X      |  tx1  |
  *     TX     |              RX                |     Serial1 RX1      |     4     |   4/D7  | 25/D2 |     X      |  rx1  |
  * ----------------------------------------------------------------------------------------------------------------------*/

#elif defined(ARDUINO_AVR_UNO) || defined(ESP8266)
  SoftwareSerial mySerial1(4, 5); 
  DFRobot_ADS1115_UART ads1115(&mySerial1);
#elif defined(ESP32)
  DFRobot_ADS1115_UART ads1115(&Serial1,/*rxD2*/25,/*txD3*/26);
#else
  DFRobot_ADS1115_UART ads1115(&Serial1);
#endif

void setup() {
    Serial.begin(9600);
    while (!ads1115.begin())
    {
      Serial.println(" Error, please check connection and mode!");
      delay(1000);  
    }  
}

void loop() {
  double data;
  unsigned char channel = 1;
  data= ads1115.getValue(channel);
  Serial.print(" channel:");
  Serial.print(channel);
  Serial.print(" adValue::");
  Serial.print(data);
  Serial.println("mv");

//  delay(1000);
  channel = 2;
  data= ads1115.getValue(channel);
  Serial.print(" channel:");
  Serial.print(channel);
  Serial.print(" adValue::");
  Serial.print(data);
  Serial.println("mv");

//  delay(1000);
}
