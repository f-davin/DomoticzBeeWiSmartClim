#!/usr/bin/env python2.7

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

from __future__ import print_function
from builtins import str
from builtins import chr
import os
import sys
from subprocess import call, check_output, STDOUT, CalledProcessError
import time

def cycleHCI(s_hci) :
   # maybe a useless time waster but it makes sure our hci is starting fresh and clean
   # nope in fact we need to call this before each time we do hci or gatt stuff or it doesn't work
   call(['hciconfig', 's_hci', 'down'])
   time.sleep(0.1)
   call(['hciconfig', 's_hci', 'up'])
   time.sleep(0.1)

def getResultStringForDeviceMacHandle(s_hci, s_mac, s_handle) :
   # Read the string from handle
   try:
      raw_input = check_output(['gatttool', '-i', s_hci, '-b', s_mac, '--char-read', '--handle='+s_handle], shell=False, stderr=STDOUT);
   except subprocess.CalledProcessError as e:
      raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
   result_string = ''
   if ':' in str(raw_input):
      raw_list=str(raw_input).split(':')
      raw_data=raw_list[1].split('\\n')[0]
      raw_data=raw_data.strip()
      octet_list=raw_data.split(' ')
      for octet in octet_list :
         j = int(octet, 16)
         if j > 31 and j < 127 : result_string += str(chr(j))
   return result_string

def getActualValues(s_hci, s_mac) :
   # read the value characteristic (read handle is 0x003f)
   # handle returns 10 byte hex block containing temperature, humidity and batery level
   # the temperature consists of 3 bytes
   # Posivive value: byte 1 & 2 present the tenfold of the temperature
   # Negative value: byte 2 - byte 3 present the tenfold of the temperature
   raw_input = check_output(['gatttool', '-i', '"' + s_hci + '"', '-b', '"' + s_mac + '"', '--char-read', '--handle=0x003f']);
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

def getDeviceInfo(s_hci, s_mac) :
   # BeeWi Smart Climate handles
   # 0x0003 :    SmartClim name : 'Smart Clim'
   # 0x001b :      model number : 'BeeWi BBW200\00'
   # 0x001d :     serial number : '\00'
   # 0x001f : firmware revision : 'V1.5 R140514\00'
   # 0x0021 : hardware revision : '1.0\00'
   # 0x0023 : software revision : '\00'
   # 0x0025 :      manufacturer : 'Voxland\00'

   Name             = getResultStringForDeviceMacHandle(s_hci, s_mac, '0x0003')
   ModelNumber      = getResultStringForDeviceMacHandle(s_hci, s_mac, '0x001b')
   SerialNumber     = getResultStringForDeviceMacHandle(s_hci, s_mac, '0x001d')
   FirmwareRevision = getResultStringForDeviceMacHandle(s_hci, s_mac, '0x001f')
   HardwareRevision = getResultStringForDeviceMacHandle(s_hci, s_mac, '0x0021')
   SoftwareRevision = getResultStringForDeviceMacHandle(s_hci, s_mac, '0x0023')
   Manufacturer     = getResultStringForDeviceMacHandle(s_hci, s_mac, '0x0025')
   return (Name, ModelNumber, SerialNumber, FirmwareRevision, HardwareRevision, SoftwareRevision, Manufacturer)

def printHelp() :
   print ('Correct usage is "[sudo] beewiclim.py <device address> <command> [argument]"')
   print ('       <device address> in the format XX:XX:XX:XX:XX:XX')
   print ('       Commands:  stat          - Get status')
   print ('       Commands:  val           - Get values (temperature, humidity, battery)')
   print ('       Commands:  raw           - Get values (temperature, humidity, battery)')
   print ('       [hci device] i.e. hci1 in case of multiple devices')
   print ('')

if __name__=='__main__' :
   if os.geteuid() != 0 :
      print ('WARNING: This script may not work correctly without sudo / root. Sorry.')
   if len(sys.argv) < 3 :
      printHelp()
   else :
      hci_device = 'hci0' # default
      device_address = sys.argv[1]
      command = sys.argv[2]
      command = command.lower()
      error = ''
      if len(sys.argv) == 4 : hci_device = sys.argv[3]
      hci_device = hci_device.lower()

      # address shortcuts
      if device_address == 'sc1' : device_address = '5C:31:3E:XX:XX:XX'
      if device_address == 'sc2' : device_address = 'D0:5F:B8:XX:XX:XX'

      if len(device_address) != 17 :
         print ('ERROR: device address must be in the format NN:NN:NN:NN:NN:NN')
         exit()
      if 'stat' in command :
         name, model, serial, frevision, hrevision, srevision, manufacturer = getDeviceInfo(hci_device, device_address)
         temperature, humidity, battery = getActualValues(hci_device, device_address)
         print ('-------------------------------------')
         print ('Device name       = ' + name)
         print ('Model number      = ' + model)
         print ('Serial number     = ' + serial)
         print ('Firmware revision = ' + frevision)
         print ('Hardware revision = ' + hrevision)
         print ('Software revision = ' + srevision)
         print ('Manufaturer       = ' + manufacturer)
         print ('-------------------------------------')
         print ('Temperature       = ' + str(temperature) + u'\u2103') # encode("utf8") needed on raspberry
         print ('Humidity          = ' + str(humidity) + '%')
         print ('Battery           = ' + str(battery) + '%')
         print ('-------------------------------------')
      if 'val' in command :
         temperature, humidity, battery = getActualValues(hci_device, device_address)
         print ('-------------------------------------')
         degree =u'\u2103'.encode("utf-8");
         print ('Temperature       = ' + str(temperature) + degree)
         print ('Humidity          = ' + str(humidity) + '%')
         print ('Battery           = ' + str(battery) + '%')
         print ('-------------------------------------')
      if 'raw' in command :
         temperature, humidity, battery = getActualValues(hci_device, device_address)
         print (str(temperature),str(humidity),str(battery))
      if error != '' :
         if error == 'off' : error = 'ERROR: SmartClim ' + device_address
         print (error)
   exit(0)
   