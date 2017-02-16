#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : disable_slot_link_all.py
# Author : Stuart Campbell
# Date   : 2016-06-20
# Version: 0.1
#
#--------------------------------------

import sys
import subprocess
import time
import os

# Scan all devices in /sys/bus/pci/devices/ and find the relevant PLX 9765 downstream ports.
# Only do this for PLX for now, can extend to Intel later if required.

PciDeviceList=os.listdir("/sys/bus/pci/devices")

for DeviceNo in range (len(PciDeviceList)):

    # first check does device still exist, since we are scrolling through devices that may include endpoints that disappear.

  DevicePath = "/sys/bus/pci/devices/" + PciDeviceList[DeviceNo]

  if(os.path.exists(DevicePath) != True):
    print "Skipping Device: ", PciDeviceList[DeviceNo]
    continue

  VendorIDAddr = "/sys/bus/pci/devices/" + PciDeviceList[DeviceNo] + "/vendor"
  VendorID = open(VendorIDAddr,'r').read().rstrip('\n')

  DeviceIDAddr = "/sys/bus/pci/devices/" + PciDeviceList[DeviceNo] + "/device"
  DeviceID = open(DeviceIDAddr,'r').read().rstrip('\n')

  if ( (VendorID == '0x10b5') and (DeviceID == '0x9765') ):
    CapabilitiesCommand = "setpci -s " + PciDeviceList[DeviceNo] + " " + "CAP_EXP.l"
    Capabilities = int(subprocess.Popen(CapabilitiesCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)

    # bit 24= slot implemented, bits 23:20=0x06 for downstream port

    if((Capabilities & 0x01600000) == 0x01600000):
      SlotCapCommand="setpci -s " + PciDeviceList[DeviceNo] + " 7c.l"
      SlotCap = int(subprocess.Popen(SlotCapCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)

      SlotNo = ((SlotCap >> 19) & 0x1f)

      print "Disable Slot ", str(SlotNo), "Link on PLX Upstream Port", PciDeviceList[DeviceNo]

      LinkDownCommand="setpci -s " + PciDeviceList[DeviceNo] + " 78.w=0010"
#      print "LinkdownCommand    : ", LinkDownCommand

      dmesg="echo \"Disable NVMe Slot " + str(SlotNo) + " Link Upstream Port " + PciDeviceList[DeviceNo] + "\"" + " > /dev/kmsg"
      subprocess.call(dmesg, shell=True)

      subprocess.call(LinkDownCommand, shell=True)

      time.sleep(1)

  #end if

#end for

#end of file
  