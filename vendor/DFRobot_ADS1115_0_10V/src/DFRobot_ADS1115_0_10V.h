/*!
 * @file DFRobot_ADS1115_0_10V.h
 * @brief Define the basic structure of class DFRobot_ADS1115
 * @copyright	Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
 * @license The MIT License (MIT)
 * @author [LR]<rong.li@dfrobot.com>
 * @version V1.0.0
 * @date 2024-07-23
 * @url https://github.com/DFRobot/DFRobot_ADS1115_0_10V
 */
#ifndef __DFRobot_ADS1115_0_10V_H
#define __DFRobot_ADS1115_0_10V_H

#include "Arduino.h"
#include "Wire.h"


#if defined(ARDUINO_AVR_UNO) || defined(ESP8266)
#include "SoftwareSerial.h"
#else
#include "HardwareSerial.h"
#endif


// #define ENABLE_DBG ///< Enable this macro to see the detailed running process of the program
#ifdef ENABLE_DBG
#define DBG(...) {Serial.print("[");Serial.print(__FUNCTION__); Serial.print("(): "); Serial.print(__LINE__); Serial.print(" ] "); Serial.println(__VA_ARGS__);}
#else
#define DBG(...)
#endif



class DFRobot_ADS1115
{
protected:
  /**
   * @fn writeReg
   * @brief Write register function, designed as virtual function, implemented by derived class
   * @param reg  Register address 8bits
   * @param pBuf Storage and buffer for data to be written
   * @param size Length of data to be written
   * @return None
   */
  virtual void writeReg(uint8_t reg, void* pBuf, size_t size) = 0;

  /**
   * @fn readReg
   * @brief Read register function, designed as virtual function, implemented by derived class
   * @param reg  Register address 8bits
   * @param pBuf Storage and buffer for data to be read
   * @param size Length of data to be read
   * @return None
   */
  virtual void readReg(uint8_t reg, void* pBuf, size_t size) = 0;

public:
  #define CHANNEL_SELECT_ADDRESS  0x20 //Channel address
  #define CHANNEL_DATA_ADDRESS  0x31 //Read data address: 0x30 data bits, 0x31-0x33 data
  /**
   * @fn begin
   * @brief subclass initialization function
   * @return bool type, means returning initialization status
   * @retval true NO_ERROR
   */
  int begin(void);
    /**
   * @fn get_value
   * @brief Getting voltage values
   * @param channel Choose channel 1 or channel 2
   * @return Voltage values
   */
  double getValue(uint8_t channel);
  DFRobot_ADS1115();
};



class DFRobot_ADS1115_UART:public DFRobot_ADS1115{
public:
#define UART_READ_REGBUF    0xBB
#define UART_WRITE_REGBUF   0xCC
  bool begin(void);

#if defined(ARDUINO_AVR_UNO) || defined(ESP8266)
  DFRobot_ADS1115_UART(SoftwareSerial* sSerial);
  SoftwareSerial* _serial;
#else
  DFRobot_ADS1115_UART(HardwareSerial* hSerial, uint8_t rxpin = 0, uint8_t txpin = 0);
  HardwareSerial* _serial;
#endif
private:
  uint32_t _baud;
  uint8_t _rxpin;
  uint8_t _txpin;
protected:
  virtual void writeReg(uint8_t reg, void* pBuf, size_t size);
  virtual void readReg(uint8_t reg, void* pBuf, size_t size);
  
};


class DFRobot_ADS1115_I2C:public DFRobot_ADS1115{
public:
  DFRobot_ADS1115_I2C(TwoWire* Wire, uint8_t MODULE_I2C_ADDRESS);
  bool begin(void);
private:
	TwoWire* _Wire;
  uint8_t deviceAddr;
protected:
  virtual void writeReg(uint8_t reg, void* pBuf, size_t size);
  virtual void readReg(uint8_t reg, void* pBuf, size_t size);  
  
};

#endif