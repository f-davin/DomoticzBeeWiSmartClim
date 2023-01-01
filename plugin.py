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

import subprocess
from builtins import str
from datetime import datetime
from datetime import timedelta
from enum import Enum, unique
from subprocess import check_output, STDOUT

import DomoticzEx as Domoticz


@unique
class LogLevel ( Enum ):
    """
    Enumeration of the different log levels
    """
    Notice = 0
    Error = 1
    Debug = 2


@unique
class HumidityStatus:
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
    enabled = False

    # Delay in minutes between two measures
    iDelayInMin = 1
    # Default delay in minutes between two measures
    iDefaultDelayInMin = 15
    # date time of the next measure
    nextMeasure = datetime.now ( )
    # Index of the device
    iUnit = 1
    # Default HCI device
    hci_device = 'hci0'
    # MAC address of the device
    device_address = "xx"

    def setNextMeasure ( self ):
        self.nextMeasure = datetime.now ( ) + timedelta ( minutes = self.iDelayInMin )

    def __init__ ( self ):
        return

    def onStart ( self ):
        log_message ( LogLevel.Notice, "onStart called" )
        # Check if debug mode is active
        self.device_address = Parameters [ "Mode1" ]
        if Parameters [ "Mode6" ] == "Debug":
            Domoticz.Debugging ( 1 )
            log_message ( LogLevel.Debug, "Debugger started, use 'telnet 0.0.0.0 4444' to connect" )
            import rpdb
            rpdb.set_trace ( )
        if len ( Devices ) == 0:
            Domoticz.Device ( Name = "SmartClim", Unit = self.iUnit, TypeName = "Temp+Hum", Subtype = 1, Switchtype = 0,
                              Description = "Capteur SmartClim", Used = 1
                              ).Create ( )
            log_message ( LogLevel.Notice, "Device created." )
        log_message ( LogLevel.Notice, "Plugin has " + str ( len ( Devices ) ) + " devices associated with it." )

        try:
            temperature, humidity, battery = self.getActualValues ( self.hci_device, self.device_address )
            Devices [ self.iUnit ].Update ( nValue = 0, sValue = str ( temperature ) + ";" + str ( humidity ),
                                            TypeName = "Temp+Hum"
                                            )
            self.nextMeasure = datetime.now ( ) + timedelta ( minutes = random.randrange ( 1, self.iDelayInMin, 1 ) )
        except (RuntimeError, NameError, TypeError):
            log_message ( LogLevel.Error, "Error" )

        dump_config_to_log ( )
        Domoticz.Heartbeat ( 30 )

        # Update the delay between the measures
        try:
            self.iDelayInMin = int ( Parameters [ "Mode2" ] )
        except ValueError:
            self.iDelayInMin = self.iDefaultDelayInMin
        log_message ( LogLevel.Notice, "Delay between measures " + str ( self.iDelayInMin ) + " minutes." )
        log_message ( LogLevel.Notice, "Leaving on start" )

    def onStop ( self ):
        log_message ( LogLevel.Notice, "onStop called" )

    def onConnect ( self, Connection, Status, Description ):
        log_message ( LogLevel.Notice, "onConnect called" )

    def onMessage ( self, Connection, Data ):
        log_message ( LogLevel.Notice, "onMessage called" )

    def onCommand ( self, Unit, Command, Level, Hue ):
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
        if datetime.now ( ) > self.nextMeasure:
            # We immediatly program next connection for tomorrow, if there is a problem, we will reprogram it sooner
            try:
                self.setNextMeasure ( )
                self.onGetSmartClimValues ( )
            except:

                try:
                    log_message ( LogLevel.Notice, "Restart the Bluetooth device" )
                    self.cycleHci ( )
                    log_message ( LogLevel.Notice, "Bluetooth device restarted" )
                except:
                    log_message ( LogLevel.Error, "Error on restart" )

    def onGetSmartClimValues ( self ):
        temperature, humidity, battery = self.getActualValues ( self.hci_device, self.device_address )
        humStat = self.__get_humidity_status ( temperature, humidity )
        sValue = str ( temperature ) + ";" + str ( humidity ) + ";" + str ( humStat )
        self.updateDevice ( 0, sValue, battery )

    def updateDevice ( self, nValue, sValue, batteryLevel ):
        Devices [ self.iUnit ].Update ( nValue = 0, sValue = str ( sValue ), BatteryLevel = batteryLevel )
        log_message ( LogLevel.Notice,
                      "Update " + str ( nValue ) + ":'" + str ( sValue ) + "' (" + Devices [ self.iUnit ].Name + ")"
                      )

    def getActualValues ( self, s_hci, s_mac ):
        # read the value characteristic (read handle is 0x003f)
        # handle returns 10 byte hex block containing temperature, humidity and batery level
        # the temperature consists of 3 bytes
        # Posivive value: byte 1 & 2 present the tenfold of the temperature
        # Negative value: byte 2 - byte 3 present the tenfold of the temperature
        try:
            raw_input = check_output ( [ 'gatttool', '-i', s_hci, '-b', s_mac, '--char-read', '--handle=0x003f' ],
                                       shell = False, stderr = STDOUT
                                       );
        except subprocess.CalledProcessError as e:
            raise RuntimeError (
                "command '{}' return with error (code {}): {}".format ( e.cmd, e.returncode, e.output )
                )
        if ':' in str ( raw_input ):
            raw_list = str ( raw_input ).split ( ':' )
            raw_data = raw_list [ 1 ].split ( '\\n' ) [ 0 ]
            raw_data = raw_data.strip ( )
            octet_list = raw_data.split ( ' ' )
            t0 = int ( octet_list [ 0 ], 16 )
            t1 = int ( octet_list [ 1 ], 16 )
            t2 = int ( octet_list [ 2 ], 16 )
            temperature = ((t2 * 255) + t1) / 10.0
            humidity = int ( octet_list [ 4 ], 16 )
            battery = int ( octet_list [ 9 ], 16 )
        return (temperature, humidity, battery)

    @staticmethod
    def __get_humidity_status ( temperature: float, humidity: int ) -> HumidityStatus:
        """
        Convert the humidity percent in Domoticz value
        :param temperature: Current temperature of the room in degree celsius
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
