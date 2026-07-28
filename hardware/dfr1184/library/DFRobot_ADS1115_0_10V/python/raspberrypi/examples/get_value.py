'''
    @file get_advalue.py
    @brief Run this routine to get the voltage
    @copyright	Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
    @license The MIT License (MIT)
    @author [lr](rong.li@dfrobot.com)
    @version V1.0.0
    @date 2024-07-23
    @url https://github.com/DFRobot/DFRobot_ADS1115_0_10V
'''
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
SLAVE_ADDRESS = 0x48

# I2C_UART_FLAG = "I2C"
I2C_UART_FLAG = "UART"
if I2C_UART_FLAG == "I2C":
    from DFRobot_ADS1115_0_10V import DFRobot_ADS1115_I2C
    ads1115 = DFRobot_ADS1115_I2C(1, SLAVE_ADDRESS)
else:
    from DFRobot_ADS1115_0_10V import DFRobot_ADS1115_UART
    ads1115 = DFRobot_ADS1115_UART("/dev/serial0")


def setup():
    while not ads1115.begin():
        print("Failed to init chip, please check if the chip connection is fine.")
        time.sleep(1)
    print("Successfully connected.")

def loop():
    channel = 1 #1 A1 2 A2
    print("channel%d adVaule:%.2f  mv" %(channel ,ads1115.get_value(channel)))
    channel = 2 #1 A1 2 A2
    print("channel%d adVaule:%.2f  mv" %(channel ,ads1115.get_value(channel)))
    # time.sleep(1)


if __name__ == "__main__":
    try:
        setup()
        while True:
            loop()
    except KeyboardInterrupt:
        exit()
