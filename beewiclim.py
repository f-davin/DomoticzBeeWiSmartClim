#!/usr/bin/env python3

#   A python script to read actual vales from the BeeWi 'BBW200 - Smart Temperature & Humidity Sensor'
#   BeeWi website: http://www.bee-wi.com/en.cfm
#
#   Missing: Read the historical temperature & humidity data (0x0039)
#
#   Tested on elelentary OS elementary OS 0.3.2 Freya >> BLE hardware: Broadcom Corp. BCM2045B (BDC-2.1) USB dongle
#   Tested on Raspberry 3
#
#   Don't kill me for the source, it's the first time I did something in Python.
#
#
#   Script based on the beewibulb.py script by Stephanie Maks >> Controlling a BeeWi SmartLite
#     https://www.raspberrypi.org/forums/viewtopic.php?f=37&t=117729
#     Used the modicications of Gerrit Hannaert
#
#   Some fiddling with the bluetooth packet capture on Android, Wireshark, hcitool, hciconfig, GATTTool, apktool and testing, testing, testing.....
#
#   Many thanks to Stephanie Maks & Gerrit Hannaert
#
#   Stephanie Maks figured out with help from -- and thanks to -- the following sources:
#      http://stackoverflow.com/questions/24853597/ble-gatttool-cannot-connect-even-though-device-is-discoverable-with-hcitool-lesc
#      http://mike.saunby.net/2013/04/raspberry-pi-and-ti-cc2541-sensortag.html
#      https://github.com/sandeepmistry/node-yeelight-blue
#      https://www.nowsecure.com/blog/2014/02/07/bluetooth-packet-capture-on-android-4-4/
#
#   note: this needs to be called with 'sudo' or by root in order to work with some of the hci commands

import asyncio
import sys

from bleak import BleakClient

# Text for the commands
STAT_COMMAND = 'stat'
RAW_COMMAND = 'raw'
VAL_COMMAND = 'val'

UUID_MANUFACTURER_NAME = "00002a29-0000-1000-8000-00805f9b34fb"  # Handle 0x0025
UUID_SOFTWARE_REV = "00002a28-0000-1000-8000-00805f9b34fb"  # Handle 0x0023
UUID_SERIAL_NUMBER = "00002a25-0000-1000-8000-00805f9b34fb"  # Handle 0x001d
UUID_MODEL = "00002a24-0000-1000-8000-00805f9b34fb"  # Handle 0x001b
UUID_FIRMWARE_REV = "00002a26-0000-1000-8000-00805f9b34fb"  # Handle 0x001f
UUID_HARDWARE_REV = "00002a27-0000-1000-8000-00805f9b34fb"  # Handle 0X0021
UUID_GET_VALUES = "a8b3fb43-4834-4051-89d0-3de95cddd318"  # Handle 0x003f


class SensorData ( ):
    def __init__ ( self ):
        self.__temperature = 0.0
        self.__humidity = 0
        self.__battery = 0

    def __init__ ( self, raw_data: bytearray ):
        self.__temperature = 0.0
        self.__humidity = 0
        self.__battery = 0
        self.parse_data ( raw_data )

    def get_temperature ( self ) -> float:
        return self.__temperature

    def get_humidity ( self ) -> int:
        return self.__humidity

    def get_battery_level ( self ) -> int:
        return self.__battery

    def parse_data ( self, raw_data: bytearray ):
        if len ( raw_data ) != 10:
            raise Exception ( 'Wrong size to decode data' )
        # handle returns 10 byte hex block containing temperature, humidity and battery level
        # the temperature consists of 3 bytes
        # Positive value: byte 1 & 2 present the tenfold of the temperature
        # Negative value: byte 2 - byte 3 present the tenfold of the temperature
        # t0 = val [ 0 ]
        # t1 = val [ 1 ]
        # t2 = val [ 2 ]
        # if t2 == 255:
        #   temperature = (t1 - t2) / 10.0
        # else:
        #   temperature = ((t0 * 255) + t1) / 10.0
        temperature = raw_data [ 2 ] + raw_data [ 1 ]
        if temperature > 0x8000:
            temperature = temperature - 0x10000
        self.__temperature = temperature / 10.0
        self.__humidity = raw_data [ 4 ]
        self.__battery = raw_data [ 9 ]


def printHelp ( ):
    print ( 'Correct usage is "beewiclim.py <device address> <command> [argument]"' )
    print ( '       <device address> in the format XX:XX:XX:XX:XX:XX' )
    print ( '       Commands:  stat          - Get status' )
    print ( '       Commands:  val           - Get values (temperature, humidity, battery)' )
    print ( '       Commands:  raw           - Get values (temperature, humidity, battery)' )
    print ( '' )


async def exec ( argv ):
    client_mac_addr = argv [ 0 ]
    command = argv [ 1 ].lower ( )

    # Check the MAC address length
    if len ( client_mac_addr ) != 17:
        raise Exception ( 'ERROR: device address must be in the format NN:NN:NN:NN:NN:NN' )

    # Check the command
    if command != STAT_COMMAND and command != VAL_COMMAND and command != RAW_COMMAND:
        raise Exception ( 'Invalid command utilization!' )

    # Start the command
    async with BleakClient ( client_mac_addr ) as client:
        resp = await client.read_gatt_char ( UUID_GET_VALUES )
        current_values = SensorData ( resp )
        if RAW_COMMAND in command:
            print ( str ( current_values.get_temperature ( ) ), str ( current_values.get_humidity ( ) ),
                    str ( current_values.get_battery_level ( ) )
                    )
        elif VAL_COMMAND in command:
            print ( '-------------------------------------' )
            degree: str = u'\u2103'.encode ( "utf-8" )
            print ( 'Temperature       = ' + str ( current_values.get_temperature ( ) ) + degree )
            print ( 'Humidity          = ' + str ( current_values.get_humidity ( ) ) + '%' )
            print ( 'Battery           = ' + str ( current_values.get_battery_level ( ) ) + '%' )
            print ( '-------------------------------------' )
        else:
            manufacturer = await client.read_gatt_char ( UUID_MANUFACTURER_NAME )
            model = await client.read_gatt_char ( UUID_MODEL )
            serial = await client.read_gatt_char ( UUID_SERIAL_NUMBER )
            frevision = await client.read_gatt_char ( UUID_FIRMWARE_REV )
            hrevision = await client.read_gatt_char ( UUID_HARDWARE_REV )
            srevision = await client.read_gatt_char ( UUID_SOFTWARE_REV )
            degree: str = u'\u2103'.encode ( "utf-8" )
            print ( '-------------------------------------' )
            # print ( 'Device name       = ' + name )
            print ( 'Model number      = ' + model )
            print ( 'Serial number     = ' + serial )
            print ( 'Firmware revision = ' + frevision )
            print ( 'Hardware revision = ' + hrevision )
            print ( 'Software revision = ' + srevision )
            print ( 'Manufacturer      = ' + manufacturer )
            print ( '-------------------------------------' )
            print ( 'Temperature       = ' + str ( current_values.get_temperature ( ) ) + degree )
            print ( 'Humidity          = ' + str ( current_values.get_humidity ( ) ) + '%' )
            print ( 'Battery           = ' + str ( current_values.get_battery_level ( ) ) + '%' )
            print ( '-------------------------------------' )


if __name__ == '__main__':
    if len ( sys.argv ) != 3:
        printHelp ( )
        exit ( -1 )
    else:
        asyncio.run ( exec ( argv = sys.argv [ 1: ] ) )
        exit ( 0 )
