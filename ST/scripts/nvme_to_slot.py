#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : nvme_to_slot.py
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
  print "Invalid Arguments - use python nvme_to_slot.py <nvme device number>|all"
  print ""
  sys.exit(1)


UserInput=sys.argv[1]

StartDrive = 0xff
EndDrive = 0xff

if (UserInput == "all"):
  StartDrive = 0
  EndDrive = 23
elif UserInput.isdigit():
  if ( (int(UserInput) >= 0) and (int(UserInput) <= 23) ):
    StartDrive = int(UserInput)
    EndDrive = int(UserInput)

if( (StartDrive == 0xff) or (EndDrive == 0xff) ):
  print "Invalid Arguments - use python nvme_to_slot.py <nvme device number>|all"
  print ""
  sys.exit(1)

#print "Slot:", StartDrive, EndDrive

for NVMeDeviceNo in range (StartDrive, (EndDrive + 1)):

  # Although not optimal, best way to read info without having to do a PCI config cycle to
  # read the slot number from the bridge, is to search through the directory listings for
  # each slot, and see which one matches the required nvme device.

  SearchNVMeDevice = "nvme" + str(NVMeDeviceNo)

  #print "Searching for:", SearchNVMeDevice

  # hardcode for current 2U24 chassis.  Need to also check interposer behaviour
  for SlotNo in range (1, 25):
  
    # For every slot, check the PCI device info in /sys/bus/pci/slots/address
  
    SlotAddress = "/sys/bus/pci/slots/" + str(SlotNo) + "/address"
  
    if(os.path.exists(SlotAddress) != True):
      continue
  
    # Valid slot number, so check PCI device info
    SSDBDF = open(SlotAddress,'r').read().rstrip('\n')
  
    DevicePath = "/sys/bus/pci/devices/" + SSDBDF + ".0/nvme"
  
    if(os.path.exists(DevicePath) != True):
      continue
  
    # now we know there is an NVMe device here, so get the handle.
  
    NVMeDevice = os.listdir(DevicePath)
  
    if(NVMeDevice[0] == SearchNVMeDevice):
      if (UserInput == "all"):
          print 'NVMe Device: /dev/nvme{}'.format(NVMeDeviceNo), "Slot:", SlotNo
      else:
        print SlotNo
      break;


