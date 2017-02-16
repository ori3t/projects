#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : set_slot_speed_all.py
# Author : Stuart Campbell
# Date   : 2016-06-20
# Version: 0.1
#
#--------------------------------------

import sys
import subprocess
import time
import os

if (len(sys.argv) < 2):
  print "Invalid Arguments - use python set_slot_speed_all.py <1|2|3> <opt:retrain>"
  print ""
  sys.exit(1)

LinkSpeed=sys.argv[1]

Retrain = False

if (len(sys.argv) > 2):
  if (sys.argv[2] == "retrain"):
    Retrain = True


# Scan all devices in /sys/bus/pci/devices/ and find the relevant PLX 9765 downstream ports.
# Only do this for PLX for now, can extend to Intel later if required.

UpstreamLNKCTL2="98"
UpstreamLNKCTL="78"

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

      print "Set Slot", str(SlotNo), "to PCIe gen",LinkSpeed, "on PLX Upstream Port", PciDeviceList[DeviceNo]

      dmesg="echo \"Set NVMe Slot " + str(SlotNo) + " to PCIe gen " + str(LinkSpeed) + " Link Upstream Port " + PciDeviceList[DeviceNo] + "\"" + " > /dev/kmsg"
      subprocess.call(dmesg, shell=True)

      if (Retrain == True):
        # change link rate.
        LinkCommand="setpci -s " + PciDeviceList[DeviceNo] + " " + UpstreamLNKCTL2 + ".w=000" + LinkSpeed
        subprocess.call(LinkCommand, shell=True)

        # Retrain link, twice (necessary when changing rate)
        LinkCommand="setpci -s " + PciDeviceList[DeviceNo] + " " + UpstreamLNKCTL + ".w=0020"
        subprocess.call(LinkCommand, shell=True)
        subprocess.call(LinkCommand, shell=True)

      else:
        # first disable link.
        LinkCommand="setpci -s " + PciDeviceList[DeviceNo] + " " + UpstreamLNKCTL + ".w=0010"
        subprocess.call(LinkCommand, shell=True)

        # next change link rate.
        LinkCommand="setpci -s " + PciDeviceList[DeviceNo] + " " + UpstreamLNKCTL2 + ".w=000" + LinkSpeed
        subprocess.call(LinkCommand, shell=True)

        # finally re-enable link.
        LinkCommand="setpci -s " + PciDeviceList[DeviceNo] + " " + UpstreamLNKCTL + ".w=0000"
        subprocess.call(LinkCommand, shell=True)


      time.sleep(1)

  #end if

#end for

#end of file
  