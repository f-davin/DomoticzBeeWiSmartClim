# Domoticz plugin for BeeeWi SmartClim

This plugin permit to get periodically the information about the temperature and humidity from the device SmartClim (BBW200 rev A1). All datas are stored in the log of temperature device.


## Prerequisites

This plugin was tested in release 4.9701 (ou beta more recent).
This plugin can be used only on linux OS (tested on Debian) and the following tools must be installed:
* gatttool
* hcitool
* Bluetooth LE device compatible (Bluetooth 4.0 minimum)

## Installation

Place you in the subfolder *plugins* of domoticz folder and launch the following command:
```
git clone https://github.com/Flo1987/DomoticzBeeWiSmartClim.git BeeWiSmartClim
```

Enter in the folder:
```
cd BeeWiSmartClim
```

Update the repository :
```
git pull
```

Put the execution permission on the plugin file :
```
chmod ugo+x plugin.py
```

Restart Domoticz.

## Licence

This project is under the licence LGPLv3 - cf. fichier [LICENSE](LICENSE) pour plus de détails.

