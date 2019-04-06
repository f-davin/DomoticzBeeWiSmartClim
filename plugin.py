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
        <param field="Mode6" label="Debug" width="100px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
                <option label="Logging" value="File"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz

class BasePlugin:
    enabled = False

    # boolean: to check that we are started, to prevent error messages when disabling or restarting the plugin
    isStarted = None

    # string: name of the Linky device
    sDeviceName = "SmartClim"

    # string: description of the Linky device
    sDescription = "Capteur SmartClim"

    # string: typename
    sTypename = "Temp+Hum"

    # boolean: debug mode
    iDebugLevel = None

    




    def __init__(self):
        self.isStarted = False

    def myDebug(self, message):
        if self.iDebugLevel:
            Domoticz.Log(message)

     # ask data to the device
    def getData(self, resource_id, start_date, end_date, ):
        Domoticz.Log(resource_id + " " + str(end_date))

    # Create Domoticz device
    def createDevice(self):
        # Only if not already done
        if not self.iIndexUnit in Devices:
            Domoticz.Device(Name=self.sDeviceName,  Unit=self.iIndexUnit, TypeName=sTypename, Description=self.sDescription).Create()
            if not (self.iIndexUnit in Devices):
                Domoticz.Error("Ne peut ajouter le dispositif Linky � la base de donn�es. V�rifiez dans les param�tres de Domoticz que l'ajout de nouveaux dispositifs est autoris�")
                return False
            Domoticz.Log("Devices created.")
        return True

    # Create device and insert usage in Domoticz DB
    def createAndAddToDevice(self, usage, Date):
        if not self.createDevice():
            return False
        # -1.0 for counter because Linky doesn't provide absolute counter value via Enedis website
        sValue = "-1.0;"+ str(usage) + ";"  + str(Date)
        self.myDebug("Mets dans la BDD la valeur " + sValue)
        Devices[self.iIndexUnit].Update(nValue=0, sValue=sValue, Type=self.iType, Subtype=self.iSubType, Switchtype=self.iSwitchType,)
        return True

    # Update value shown on Domoticz dashboard
    def updateDevice(self, usage):
        if not self.createDevice():
            return False
        # -1.0 for counter because Linky doesn't provide absolute counter value via Enedis website
        sValue="-1.0;"+ str(usage)
        self.myDebug("Mets sur le tableau de bord la valeur " + sValue)
        Devices[self.iIndexUnit].Update(nValue=0, sValue=sValue, Type=self.iType, Subtype=self.iSubType, Switchtype=self.iSwitchType)
        return True

    def onStart(self):
        Domoticz.Log("onStart called")
        # TODO Verification of parameters

        self.__init__()

        if self.createDevice():
            self.nextConnection = datetime.now()
        self.isStarted = True




    def onStop(self):
        Domoticz.Log("onStop called")
        self.isStarted = False

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
