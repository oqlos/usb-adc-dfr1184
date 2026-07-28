/*!
 * @file DFRobot_ADS1115_0_10V.cpp
 * @brief Define the basic structure of class DFRobot_ADS1115
 * @copyright	Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
 * @license The MIT License (MIT)
 * @author [LR]<rong.li@dfrobot.com>
 * @version V1.0.0
 * @date 2024-07-23
 * @url https://github.com/DFRobot/DFRobot_ADS1115_0_10V
 */
#include"DFRobot_ADS1115_0_10V.h"

#ifdef DEBUG  
#define LOG(msg) std::cout << msg << std::endl  
#else  
#define LOG(msg) // No debugging information is output  
#endif  


DFRobot_ADS1115::DFRobot_ADS1115()
{
}

int DFRobot_ADS1115::begin(void)
{
	return 0;
}

double DFRobot_ADS1115::getValue(uint8_t channel)
{
	uint8_t pBuf[3]={0};
	double ad_value=0;
 	writeReg(CHANNEL_SELECT_ADDRESS,  &channel, 1);
	readReg(CHANNEL_DATA_ADDRESS, pBuf, 3);
	ad_value = pBuf[1];//bug 
	ad_value=pBuf[0]*65536+(ad_value*256)+pBuf[2];
	return ad_value/100.0;
}


#if defined(ARDUINO_AVR_UNO) || defined(ESP8266)
DFRobot_ADS1115_UART::DFRobot_ADS1115_UART(SoftwareSerial* sSerial)
{
	_serial = sSerial;
	_baud=9600;
}
#else
DFRobot_ADS1115_UART::DFRobot_ADS1115_UART(HardwareSerial* hSerial, uint8_t rxpin, uint8_t txpin)
{
	_serial = hSerial;
	_baud=9600;
	_rxpin = rxpin;
	_txpin = txpin;
}
#endif

bool DFRobot_ADS1115_UART::begin(void)
{
#ifdef ESP32
  _serial->begin(_baud, SERIAL_8N1, _rxpin, _txpin);//ESP32 Serial->begin need  _rxpin, _txpin
#else
  _serial->begin(_baud);  
#endif
	_serial->write("AT\r\n");
	size_t i=0;
	uint8_t buf[5]={0};
	uint32_t nowtime = millis();
	while (millis() - nowtime < 200) {
		while (_serial->available()) {
			buf[i++] = _serial->read();
			if((strcmp("OK\r\n",(char *)buf)==0)&&(i==4))
				return 1;
		} 
		if(i==4)return 0;;
	}
	return 0;
}

void DFRobot_ADS1115_UART::writeReg(uint8_t reg, void* pBuf, size_t size)
{
	if (pBuf == NULL) {
   		DBG("pBuf ERROR!! : null pointer");
 	}
	uint8_t * _pBuf = (uint8_t *)pBuf;
	_serial->write(UART_WRITE_REGBUF);
	_serial->write(reg);
	_serial->write(size);
	for (size_t i = 0; i < size; i++) {
		_serial->write(_pBuf[i]);
    }
	delay(20);
}

void DFRobot_ADS1115_UART::readReg(uint8_t reg, void* pBuf, size_t size)
{	
	if (pBuf == NULL) {
   		DBG("pBuf ERROR!! : null pointer");
 	}
	uint8_t * _pBuf =(uint8_t *)pBuf;
	while (_serial->available()) {  //Clear the cache
    	_serial->read(); 
  	}
	_serial->write(UART_READ_REGBUF);   // read type
 	_serial->write(reg);   // read reg
  	_serial->write(size);   // read len
	delay(20);
	size_t i=0;
 	uint32_t nowtime = millis();
	while (millis() - nowtime < 200) 
	{
		while (_serial->available()) {
			_pBuf[i++] = _serial->read();
			if(i==size)break;
		} 
		if(i==size)break;
	}
}

DFRobot_ADS1115_I2C::DFRobot_ADS1115_I2C(TwoWire* Wire, uint8_t MODULE_I2C_ADDRESS)
{
	_Wire=Wire;
	deviceAddr=MODULE_I2C_ADDRESS;
}

bool DFRobot_ADS1115_I2C::begin(void){
	_Wire->begin();
	_Wire->beginTransmission(deviceAddr);
//	_Wire->setClock(400000);
	if(_Wire->endTransmission())
		return 0;
	return 1;	
}

void DFRobot_ADS1115_I2C:: writeReg(uint8_t reg, void* pBuf, size_t size)
{
	uint8_t * _pBuf = (uint8_t *)pBuf;
	for(uint16_t i = 0; i < size; i++){
		_Wire->beginTransmission(deviceAddr);            
		_Wire->write(reg);                               
		_Wire->write(_pBuf[i]);
		_Wire->endTransmission();
 	}
	delay(50);
}

void DFRobot_ADS1115_I2C:: readReg(uint8_t reg, void* pBuf, size_t size)
{
	if (pBuf == NULL) {
   		DBG("pBuf ERROR!! : null pointer");
  	}
	size_t i = 0;
	uint8_t * _pBuf = (uint8_t *)pBuf;
	_Wire->beginTransmission(deviceAddr);             // transmit to device Address
	_Wire->write(reg); 
	if (_Wire->endTransmission() != 0) {
		DBG("endTransmission ERROR!!");
  	}                              
	_Wire->endTransmission();
	_Wire->requestFrom(deviceAddr, size);
	while (_Wire->available())                      
	{
		_pBuf[i++] = _Wire->read();
		if(i==size)break;
	}	
}
