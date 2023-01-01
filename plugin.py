#           Beewi SmartClim Plugin
#
#           Author: 
#                       Copyright (C) 2019 DavTechNet
#
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
<plugin key="BeeWiSmartClim" name="BeeWi SmartClim" author="DavTechNet" version="0.5.0" externallink="https://github.com/DavTechNet/DomoticzBeeWiSmartClim">
    <description>
        <h2>BeeWi SmartClim</h2><br/>
        This plugin permits the following actions:
        <ul style="list-style-type:square">
            <li>Read the temperature</li>
            <li>Read the humidity</li>
            <li>Read the battery level</li>
        </ul>
    </description>
    <params>
        <param field="Mode1" label="MAC address" required="true" default="XX:XX:XX:XX:XX:XX" width="300px" />
        <param field="Mode2" label="Time between to measures in minutes" width="300px" required="true" default="15"/>
        <param field="Mode6" label="Debug" width="300px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""

import asyncio
from builtins import str
from datetime import datetime
from datetime import timedelta
from enum import Enum, unique

import DomoticzEx as Domoticz
from bleak import BleakClient

# BLE UUID
UUID_MANUFACTURER_NAME = "00002a29-0000-1000-8000-00805f9b34fb"  # Handle 0x0025
UUID_SOFTWARE_REV = "00002a28-0000-1000-8000-00805f9b34fb"  # Handle 0x0023
UUID_SERIAL_NUMBER = "00002a25-0000-1000-8000-00805f9b34fb"  # Handle 0x001d
UUID_MODEL = "00002a24-0000-1000-8000-00805f9b34fb"  # Handle 0x001b
UUID_FIRMWARE_REV = "00002a26-0000-1000-8000-00805f9b34fb"  # Handle 0x001f
UUID_HARDWARE_REV = "00002a27-0000-1000-8000-00805f9b34fb"  # Handle 0X0021
UUID_GET_VALUES = "a8b3fb43-4834-4051-89d0-3de95cddd318"  # Handle 0x003f


@unique
class LogLevel ( Enum ):
    """
    Enumeration of the different log levels
    """
    Notice = 0
    Error = 1
    Debug = 2


@unique
class HumidityStatus ( Enum ):
    """
    Enumeration of the different status of humidity
    """
    normal = 0
    comfort = 1
    dry = 2
    wet = 3


class SensorData:
    def __init__ ( self, raw_data: bytearray ):
        """
        Initialize the values
        :param raw_data: Data from the sensor
        """
        self.__temperature = 0.0
        self.__humidity = 0
        self.__battery = 0
        self.parse_data ( raw_data )

    def __init__ ( self ):
        """
        Initialize the values
        """
        self.__temperature = 0.0
        self.__humidity = 0
        self.__battery = 0

    def get_temperature ( self ) -> float:
        """
        Get the current temperature
        :return: The current temperature
        """
        return self.__temperature

    def get_humidity ( self ) -> int:
        """
        Get the current humidity
        :return: The current humidity
        """
        return self.__humidity

    def get_battery_level ( self ) -> int:
        """
        Get the current battery level
        :return: The current battery level
        """
        return self.__battery

    def parse_data ( self, raw_data: bytearray ):
        """
        Parse the dta from the sensor to extract the different values
        :param raw_data: Data from sensor
        :return: Nothing
        """
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


class BasePlugin:
    # __enabled = False
    # MAC address
    __mac_addr: str = "xx"
    # date time of the next measure
    __next_measure: datetime
    # Delay in minutes between two measures
    __delay_in_minutes: int = 15

    # Index of the device
    iUnit = 1
    # Default HCI device
    hci_device = 'hci0'

    def __init__ ( self ):
        self.__next_measure = datetime.now ( )
        return

    def onStart ( self ):
        log_message ( LogLevel.Notice, "onStart called" )
        # Parse parameters
        self.__mac_addr = Parameters [ "Mode1" ]
        try:
            config_val = int ( Parameters [ "Mode2" ] )
            self.__delay_in_minutes = config_val
        except ValueError:
            pass
        log_message ( LogLevel.Notice, "Delay between measures " + str ( self.__delay_in_minutes ) + " minutes." )

        # Check if debug mode is activated
        if Parameters [ "Mode6" ] == "Debug":
            Domoticz.Debugging ( 1 )
            dump_config_to_log ( )
            # log_message ( LogLevel.Debug, "Debugger started, use 'telnet 0.0.0.0 4444' to connect" )
            # import rpdb
            # rpdb.set_trace ( )
        if len ( Devices ) == 0:
            Domoticz.Device ( Name = "SmartClim", Unit = self.iUnit, TypeName = "Temp+Hum", Subtype = 1, Switchtype = 0,
                              Description = "Capteur SmartClim", Used = 1
                              ).Create ( )
            log_message ( LogLevel.Notice, "Device created." )
        log_message ( LogLevel.Notice, "Plugin has " + str ( len ( Devices ) ) + " devices associated with it." )

        try:
            temperature, humidity, battery = self.getActualValues ( self.hci_device, self.__mac_addr )
            Devices [ self.iUnit ].Update ( nValue = 0, sValue = str ( temperature ) + ";" + str ( humidity ),
                                            TypeName = "Temp+Hum"
                                            )
            self.__next_measure = datetime.now ( ) + timedelta (
                minutes = random.randrange ( 1, self.__delay_in_minutes, 1 )
                )
        except (RuntimeError, NameError, TypeError):
            log_message ( LogLevel.Error, "Error" )

        Domoticz.Heartbeat ( 20 )
        log_message ( LogLevel.Notice, "Leaving on start" )

    def onStop ( self ):
        log_message ( LogLevel.Notice, "onStop called" )

    def onConnect ( self, Connection, Status, Description ):
        log_message ( LogLevel.Notice, "onConnect called" )

    def onMessage ( self, Connection, Data ):
        log_message ( LogLevel.Notice, "onMessage called" )

    def onCommand ( self, Unit, Command, Level, Color ):
        log_message ( LogLevel.Notice,
                      "onCommand called for Unit " + str ( Unit ) + ": Parameter '" + str ( Command
                                                                                            ) + "', Level: " + str (
                          Level
                          )
                      )

    def onNotification ( self, Name, Subject, Text, Status, Priority, Sound, ImageFile ):
        log_message ( LogLevel.Notice,
                      "Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str ( Priority
                                                                                                        ) + "," + Sound + "," + ImageFile
                      )

    def onDisconnect ( self, Connection ):
        log_message ( LogLevel.Notice, "onDisconnect called" )

    def onHeartbeat ( self ):
        log_message ( LogLevel.Notice, "onHeartbeat called" )
        if datetime.now ( ) > self.__next_measure:
            # We immediately program next connection for tomorrow, if there is a problem, we will reprogram it sooner
            self.__set_next_measure ( )
            asyncio.run ( self.__read_smart_clim_values_and_update ( ) )

    async def __read_smart_clim_values_and_update ( self ) -> None:
        """
        Read current values and update domoticz database
        :return: Nothing
        """
        async with BleakClient ( self.__mac_addr ) as client:
            resp = await client.read_gatt_char ( UUID_GET_VALUES )
            sensor_data = SensorData ( resp )
            humStat = self.__get_humidity_status ( sensor_data.get_temperature ( ),
                                                   sensor_data.get_humidity ( )
                                                   )
            sValue = str ( sensor_data.get_temperature ( ) ) + ";" + str ( sensor_data.get_humidity ( )
                                                                           ) + ";" + str ( humStat )
            Devices [ self.iUnit ].Update ( nValue = 0, sValue = sValue,
                                            BatteryLevel = sensor_data.get_battery_level ( ), Log = True
                                            )

    def __set_next_measure ( self ):
        """
        Calculate the next date and time for read the sensor values
        :return:
        """
        self.__next_measure = datetime.now ( ) + timedelta ( minutes = self.__delay_in_minutes )

    @staticmethod
    def __get_humidity_status ( temperature: float, humidity: int ) -> HumidityStatus:
        """
        Convert the humidity percent in Domoticz value
        :param temperature: Current temperature of the room in degree Celsius
        :param humidity: Current humidity of the room in percent
        :return: The humidity status
        """
        c1 = -8.78469475556
        c2 = 1.61139411
        c3 = 2.33854883889
        c4 = -0.14611605
        c5 = -0.012308094
        c6 = -0.0164248277778
        c7 = 0.002211732
        c8 = 0.00072546
        c9 = -0.000003582
        ret = HumidityStatus.normal

        val = c1 + c2 * temperature + c3 * humidity + c4 * temperature * humidity + c5 * (
                temperature * temperature) + c6 * (humidity * humidity)
        val = val + c7 * (temperature * temperature) * humidity + c8 * temperature * (humidity * humidity) + c9 * (
                temperature * temperature) * (humidity * humidity)

        if 27 <= val < 32:
            ret = 1
        elif 32 <= val < 41:
            ret = 2
        elif val >= 41:
            ret = 3
        return ret


global _plugin
_plugin = BasePlugin ( )


def onStart ( ):
    global _plugin
    _plugin.onStart ( )


def onStop ( ):
    global _plugin
    _plugin.onStop ( )


def onConnect ( Connection, Status, Description ):
    global _plugin
    _plugin.onConnect ( Connection, Status, Description )


def onMessage ( Connection, Data ):
    global _plugin
    _plugin.onMessage ( Connection, Data )


def onCommand ( Unit, Command, Level, Color ):
    global _plugin
    _plugin.onCommand ( Unit, Command, Level, Color )


def onNotification ( Name, Subject, Text, Status, Priority, Sound, ImageFile ):
    global _plugin
    _plugin.onNotification ( Name, Subject, Text, Status, Priority, Sound, ImageFile )


def onDisconnect ( Connection ):
    global _plugin
    _plugin.onDisconnect ( Connection )


def onHeartbeat ( ):
    global _plugin
    _plugin.onHeartbeat ( )


# Generic helper functions
def log_message ( level: LogLevel, message: str ):
    """
    Add a message in the log
    :param level: Level of the message to log
    :param message: Message to log
    :return: Nothing
    """
    if level == LogLevel.Debug:
        Domoticz.Debug ( message )
    elif level == LogLevel.Error:
        Domoticz.Error ( message )
    elif level == LogLevel.Notice:
        Domoticz.Log ( message )


def dump_config_to_log ( ):
    """
    Copy the current configuration in the log at debug level
    :return: Nothing
    """
    for x in Parameters:
        if Parameters [ x ] != "":
            log_message ( LogLevel.Debug, "'" + x + "':'" + str ( Parameters [ x ] ) + "'" )
    log_message ( LogLevel.Debug, "Device count: " + str ( len ( Devices ) ) )
    for x in Devices:
        log_message ( LogLevel.Debug, "Device:           " + str ( x ) + " - " + str ( Devices [ x ] ) )
        log_message ( LogLevel.Debug, "Device ID:       '" + str ( Devices [ x ].ID ) + "'" )
        log_message ( LogLevel.Debug, "Device Name:     '" + Devices [ x ].Name + "'" )
        log_message ( LogLevel.Debug, "Device nValue:    " + str ( Devices [ x ].nValue ) )
        log_message ( LogLevel.Debug, "Device sValue:   '" + Devices [ x ].sValue + "'" )
        log_message ( LogLevel.Debug, "Device LastLevel: " + str ( Devices [ x ].LastLevel ) )
