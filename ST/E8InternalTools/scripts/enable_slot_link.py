#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : enable_slot_link.py
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
  print "Invalid Arguments - use python enable_slot_link.py <slot number>"
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

  CheckPortCommand = "setpci -s " + PciDeviceList[DeviceNo] + " " + "SECONDARY_BUS"
  SecondaryBus = str(subprocess.Popen(CheckPortCommand,shell=True,stdout=subprocess.PIPE).stdout.read())

  if ((SecondaryBus[0] == SSDBDF[5]) and (SecondaryBus[1] == SSDBDF[6])):
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
  print "Enable Slot ", str(SlotNo), "Link on Intel Upstream Port", UpstreamBDF
  UpstreamLNKSTS="a2"
  UpstreamLNKCTL="a0"
else:
  print "Enable Slot ", str(SlotNo), "Link on PLX Upstream Port", UpstreamBDF
  UpstreamLNKSTS="7a"
  UpstreamLNKCTL="78"

LinkUpCommand="setpci -s " + UpstreamBDF + " " + UpstreamLNKCTL + ".w=0000"

dmesg="echo \"Enable NVMe Slot " + str(SlotNo) + " Link Upstream Port " + str(UpstreamBDF) + "\"" + " > /dev/kmsg"
subprocess.call(dmesg, shell=True)

subprocess.call(LinkUpCommand, shell=True)
  