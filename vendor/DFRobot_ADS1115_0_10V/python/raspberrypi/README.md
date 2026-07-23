# DFRobot_ADS1115_0_10V
- [中文版](./README_CN.md)

The product is a module that integrates the ADS1115 chip. The I2C and UART communication modes can be selected by the dial switch, and the I2C address of the module can also be switched by the dial switch. The external device can obtain two sets of voltage data with a resolution of 0.01mv through the gravity interface. This module can be used to accurately measure the DC voltage from 0 to 10v.


![effect picture](../../resources/images/DFR1184-1.png) 

## Product Link(https://www.dfrobot.com/)

## Table of Contents

* [Summary](#Summary)
* [Installation](#Installation)
* [Methods](#Methods)
* [Compatibility](#Compatibility)
* [History](#History)
* [Credits](#Credits)

## Summary

  * Get the voltage and choose to get the voltage of channel 1 or channel 2
  * Measurement voltage accuracy, 0.01mv


## Installation
To use this library, first download it to Raspberry Pi and then open the use case folder. To execute a use case demox.py, enter python demox.py in the command line. For example, to execute the control32k.py use case, you need to enter:<br>

```
python get_advalue.py
```



## Methods

```python
'''!
  @fn begin
  @brief Initializes the communication method
  @return Ture or False
'''
  def begin(self)
'''
  @fn get_value(uint8_t channel)
  @brief Getting voltage values
  @param select channel 1/ channel 2
  @note You can only enter 1 or 2, and any other values will always return 0
  @return voltage values
'''
  def get_value(uint8_t channel);

```

## Compatibility
|              |           |            |          |         |
| ------------ | --------- | ---------- | -------- | ------- |
| MCU          | Work Well | Work Wrong | Untested | Remarks |
| RaspberryPi2 |           |            | √        |         |
| RaspberryPi3 |           |            | √        |         |
| RaspberryPi4 | √         |            |          |         |

- Python version

| Python  | Work Well | Work Wrong | Untested | Remarks |
| ------- | --------- | ---------- | -------- | ------- |
| Python2 | √         |            |          |         |
| Python3 | √         |            |          |         |


## History

- 2024/07/23 - Version 1.0.0 released.

## Credits

Written by lr(rong.li@dfrobot.com), 2024. (Welcome to our website)
