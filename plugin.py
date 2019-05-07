#           Beewi SmartClim Plugin
#
#           Author: 
#                       Copyright (C) 2019 Flo1987
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
<plugin key="BeewiSmartClim" name="BeeWi SmartClim" author="Flo1987" version="0.1.0" externallink="https://github.com/Flo1987/DomoticzBeeWiSmartClim">
    <description>
        <h2>BeeWi SmartClim</h2><br/>
        This plugin permits the following actions:
        <ul style="list-style-type:square">
            <li>Read the temperature</li>
            <li>Read the humidity</li>
            <li>Read the battery level</li>
        </ul>
        <h3>Configuration</h3>
        One parameter exist, it's the MAC address of the device
    </description>
    <params>
        <param field="Mode1" label="MAC address" required="true" default="XX:XX:XX:XX:XX:XX" width="200px" />
        <param field="Mode2" label="Time between to measures in minuts" width="50px" required="true" default="15"/>
        <param field="Mode6" label="Debug" width="100px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
from datetime import datetime
from datetime import timedelta
import time
from builtins import str
from builtins import chr
import os
import sys
from subprocess import call, check_output, STDOUT

class BasePlugin:
    enabled = False

    # Delay in minutes between two measures
    iDelayInMin = 1
    # Default delay in minutes between two measures
    iDefaultDelayInMin = 15
    # date time of the next measure
    nextMeasure = datetime.now()
    # Index of the device
    iUnit = 1
    # Default HCI device
    hci_device = 'hci0'
    # MAC address of the device
    device_address = "xx"

    def setNextMeasure(self):
        self.nextMeasure = datetime.now() + timedelta(minutes=self.iDelayInMin) 

    def __init__(self):
        return

    def onStart(self):
        Domoticz.Log("onStart called")
        # Check if debug mmode is active
        self.device_address = Parameters["Mode1"]
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            Domoticz.Log("Debugger started, use 'telnet 0.0.0.0 4444' to connect")
            #import rpdb
            #rpdb.set_trace()
        if (len(Devices) == 0):
            Domoticz.Device(Name="SmartClim",  Unit=self.iUnit, TypeName="Temp+Hum", Subtype=1, Switchtype=0, Description="Capteur SmartClim", Used=1).Create()
            Domoticz.Log("Device created.")
        Domoticz.Log("Plugin has " + str(len(Devices)) + " devices associated with it.")
        
        temperature, humidity, battery = self.getActualValues(self.hci_device, self.device_address)
        Devices[self.iUnit].Update(nValue=0, sValue= str(temperature) + ";" + str(humidity), TypeName="Temp+Hum")
        DumpConfigToLog()
        Domoticz.Heartbeat(30)

        # Update the delay between the measures
        try:
            self.iDelayInMin = int(Parameters["Mode2"])
        except ValueError:
            self.iDelayInMin = self.iDefaultDelayInMin
        Domoticz.Log("Delay between measures " + str(self.iDelayInMin) + " minuts.")
        Domoticz.Log("Leaving on start")

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")
        if datetime.now() > self.nextMeasure:
            # We immediatly program next connection for tomorrow, if there is a problem, we will reprogram it sooner
            self.setNextMeasure()
            self.onGetSmartClimValues()

    def onGetSmartClimValues(self):
        temperature, humidity, battery = self.getActualValues(self.hci_device, self.device_address)
        humStat = self.getHumidityStatus(temperature, humidity)
        sValue = str(temperature) + ";" + str(humidity) + ";" + str(humStat)
        self.updateDevice(0, sValue, battery)

    def updateDevice(self, nValue, sValue, batteryLevel):
        Devices[self.iUnit].Update(nValue=0, sValue=str(sValue), BatteryLevel=batteryLevel)
        Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[self.iUnit].Name+")")

    def getActualValues(self, s_hci, s_mac) :
        # read the value characteristic (read handle is 0x003f)
        # handle returns 10 byte hex block containing temperature, humidity and batery level
        # the temperature consists of 3 bytes
        # Posivive value: byte 1 & 2 present the tenfold of the temperature
        # Negative value: byte 2 - byte 3 present the tenfold of the temperature
        raw_input = check_output(['gatttool', '-i', s_hci, '-b', s_mac, '--char-read', '--handle=0x003f']);
        if ':' in str(raw_input):
            raw_list    = str(raw_input).split(':')
            raw_data    = raw_list[1].split('\\n')[0]
            raw_data    = raw_data.strip()
            octet_list  = raw_data.split(' ')
            t0 = int(octet_list[0], 16)
            t1 = int(octet_list[1], 16)
            t2 = int(octet_list[2], 16)
            if t2 == 255:
                temperature = (t1-t2)/10.0
            else:
                temperature = ((t0*255)+t1)/10.0
            humidity    = int(octet_list[4], 16)
            battery     = int(octet_list[9], 16)
        return (temperature, humidity, battery)

    def getHumidityStatus(self, temperature, humidity):
        # Temprature in °C
        # Humudity in %
        c1 = −8.78469475556
        c2 = 1.61139411
        c3 = 2.33854883889
        c4 = -0.14611605
        c5 = -0.012308094
        c6 = -0.0164248277778
        c7 = 0.002211732
        c8 = 0.00072546
        c9 = -0.000003582
        humStat = 0
        
        HI = c1 + c2 * temperature + c3 * humidity + c4 * temperature * humidity + c5 *(temperature*temperature) + c6 * (humidity * humidity) 
        HI = HI + c7 * (temperature * temperature) * humidity + c8 * temperature * (humidity * humidity) + c9 * (temperature * temperature) * (humidity * humidity)
        
        if HI >= 27 and HI < 32:
            humStat = 1
        if HI >= 32 and HI < 41:
            humStat = 2
        if HI >= 41:
            humStat = 3
            
        return humStat

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def LogMessage(Message):
    if Parameters["Mode6"] != "Normal":
        Domoticz.Log(Message)
    elif Parameters["Mode6"] != "Debug":
        Domoticz.Debug(Message)
    else:
        f = open("http.html","w")
        f.write(Message)
        f.close()   

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
