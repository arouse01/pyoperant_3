import sys  # We need sys so that we can pass argv to QApplication
import os
import serial  # To connect directly to Teensys for water control
import time


def start(boxnumber):
    device_name = '/dev/teensy{:02d}'.format(boxnumber)
    device = serial.Serial(port=device_name, baudrate=115200, timeout=5)
    device.readline()
    device.flushInput()
    print("Successfully opened device {}".format(device_name))
    return device
    # device.write("".join([chr(41), chr(3)]))  # set channel 16 (solenoid) as output
    # # device.write("".join([chr(16), chr(2)]))  # close solenoid, just in case
    # device.write("".join([chr(41), chr(1)]))  # open solenoid


def set_high(device, channel):
    device.write("".join([chr(channel), chr(3)]))  # set channel as output
    output = device.readline()  # open solenoid
    print(output)
    device.write("".join([chr(channel), chr(1)]))  # write high


def set_low(device, channel):
    device.write("".join([chr(channel), chr(3)]))  # set channel as output
    device.write("".join([chr(channel), chr(2)]))  # write low


def read(device, channel):
    device.write("".join([chr(channel), chr(4)]))  # set channel as input
    device.write("".join([chr(channel), chr(0)]))  # read
    output = device.read()  # open solenoid
    print(output)


def id(device):
    device.write("".join([chr(0), chr(6)]))  # set channel as input
    # output = device.readline()  # open solenoid
    # print(output)


def close(device):
    device.close()


selectDevice = start(7)
# set_high(selectDevice, 38)
# time.sleep(1)
# set_low(selectDevice, 38)
read(selectDevice,36)
# id(selectDevice)
close(selectDevice)
