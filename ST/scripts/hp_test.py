#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : hp_test.py
# Author : Stuart Campbell
# Date   : 2016-06-20
# Version: 0.1
#
#--------------------------------------

import sys
import subprocess
import time
import os

# check input parameters.

if (len(sys.argv) < 2):
  print "Invalid Arguments - use python hp_slottest.py <slot number>"
  print ""
  sys.exit(1)


SlotNo=sys.argv[1]

SlotAddress="/sys/bus/pci/slots/" + SlotNo + "/address"

SSDBDF = open(SlotAddress,'r').read().rstrip('\n')

# SSDBDF is now in the format 0000:xx:yy Domain:bus:device
# Need to find the upstream BDF of root port, either in switch or on CPU.
# No easy way to do this, so scan all devices in /sys/bus/pci/devices/ and find the secondary bus number that
# matches the bus field from the device on the slot.

PciDeviceList=os.listdir("/sys/bus/pci/devices")

#print "No of devices",len(PciDeviceList)
#print "Device List", PciDeviceList

UpstreamBDF="FF:FF"

for DeviceNo in range (len(PciDeviceList)):
# print "checking: ",DeviceNo, PciDeviceList[DeviceNo], SSDBDF

  CheckPortCommand = "setpci -s " + PciDeviceList[DeviceNo] + " " + "SECONDARY_BUS"
  SecondaryBus = str(subprocess.Popen(CheckPortCommand,shell=True,stdout=subprocess.PIPE).stdout.read())

  if ((SecondaryBus[0] == SSDBDF[5]) and (SecondaryBus[1] == SSDBDF[6])):
    print "Found Upstream Port", PciDeviceList[DeviceNo]
    UpstreamBDF=PciDeviceList[DeviceNo]
    break

if (UpstreamBDF == "FF:FF"):
  print "Error detecting upstream BDF"
  sys.exit(1)

# Now detect the type of upstream port, either Intel or PLX
# Do this by reading the device type registers

VendorIDCommand = "setpci -s " + PciDeviceList[DeviceNo] + " " + "VENDOR_ID"
VendorID = subprocess.Popen(VendorIDCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n')

if VendorID == '8086':
  print "Intel Upstream Port"
  UpstreamLNKSTS="a2"
  UpstreamLNKCTL="a0"
else:
  print "PLX Upstream Port"
  UpstreamLNKSTS="7a"
  UpstreamLNKCTL="78"


LinkStatusCommand="setpci -s " + UpstreamBDF + " " + UpstreamLNKSTS + ".w"
LinkDownCommand="setpci -s " + UpstreamBDF + " " + UpstreamLNKCTL + ".w=0010"
LinkUpCommand="setpci -s " + UpstreamBDF + " " + UpstreamLNKCTL + ".w=0000"
CheckSSDCommand="lspci -v -s " + SSDBDF

print "LinkStatusCommand: ", LinkStatusCommand
print "LinkDownCommand  : ", LinkDownCommand
print "LinkUpCommand    : ", LinkUpCommand
print "CheckSSDCommand  : ", CheckSSDCommand

#sys.exit(1)

subprocess.call('echo "hp_test: " > /dev/kmsg', shell=True)
dmesg="echo \"hp_test: Starting Hotplug Test on Slot " + str(SlotNo) + "\"" + " > /dev/kmsg"
subprocess.call(dmesg, shell=True)

Loop = 1
LinkUpFailure = 0

while Loop >= 1:
  LinkStatus = int(subprocess.Popen(LinkStatusCommand,shell=True,stdout=subprocess.PIPE).stdout.read(),16)

  print ""
  print "Slot ", str(SlotNo), " Link Status:", hex(LinkStatus), " Iteration:", Loop, " Errors:", LinkUpFailure

  if((LinkStatus & 0x2000) != 0):
    #print "Link Up:", hex(LinkStatus)
    if((LinkStatus & 0x000f) != 0x0003):
      print "not gen3"
    print "Bringing Link Down"

    subprocess.call('echo "hp_test: " > /dev/kmsg', shell=True)
    dmesg="echo \"hp_test: Bringing Link Down on Slot " + str(SlotNo) + ", Iteration: " + str(Loop) + ", Errors: " + str(LinkUpFailure) + "\"" + " > /dev/kmsg"
    subprocess.call(dmesg, shell=True)

    subprocess.call(LinkDownCommand, shell=True)
    time.sleep(5)
    result = subprocess.Popen(CheckSSDCommand, shell=True)
    output = result.communicate()
    Loop = Loop + 1

  else:
    #print "Link Down:", hex(LinkStatus)
    print "Bringing Link Up"

    subprocess.call('echo "hp_test: " > /dev/kmsg', shell=True)
    dmesg="echo \"hp_test: Bringing Link Up on Slot " + str(SlotNo) + ", Iteration: " + str(Loop) + ", Errors: " + str(LinkUpFailure) + "\"" + " > /dev/kmsg"
    subprocess.call(dmesg, shell=True)

    subprocess.call(LinkUpCommand, shell=True)
    time.sleep(5)


    # now check result, link should be up.  so we should see device using lspci.
    #result = subprocess.Popen(CheckSSDCommand, shell=True)
    #output = result.communicate()

    result = str(subprocess.Popen(CheckSSDCommand,shell=True,stdout=subprocess.PIPE).stdout.read())
    #print "Result: ", result

    if "Slot:" in result:
      print "Link Up Success"
    else:
      print "Link Up Failure"
      LinkUpFailure = LinkUpFailure + 1

  time.sleep(10) # 10s
  