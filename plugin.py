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
import time

class BasePlugin:
    enabled = False

    # Delay in minutes between two measures
    iDelayInMin = 1
    # Defaukt delay in minutes between two measures
    iDefaultDelayInMin = 15

    def setNextMeasure(self):
        self.nextMeasure = datetime.now() + timedelta(minutes=self.iDelayInMin) 


    def __init__(self):
        return


    def onStart(self):
        Domoticz.Log("onStart called")
        # Check if debug mmode is active
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        if (len(Devices) == 0):
            Domoticz.Device(Name="SmartClim",  Unit=1, TypeName="Temp+Hum", Description="Capteur SmartClim").Create()
            Domoticz.Log("Device created.")
        Domoticz.Log("Plugin has " + str(len(Devices)) + " devices associated with it.")
        DumpConfigToLog()

        # Update the delay between the measures
        try:
            self.iDelayInMin = int(Parameters["Mode2"])
        except ValueError:
            self.iDelayInMin = self.iDefaultDelayInMin
        Domoticz.Log("Delay between measures " + str(self.iDelayInMin) + " minuts.")
        Devices[0].Update(nValue=Devices[Device].nValue, sValue=Devices[Device].sValue, TimedOut=1)
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
        ## TODO get values
        UpdateDevice(0, "10;45%", 127)

    def UpdateDevice(nValue, sValue, batteryLevel):
        Devices[0].Update(nValue=nValue, sValue=str(sValue), BatteryLevel=batteryLevel)
        Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[0].Name+")")


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
