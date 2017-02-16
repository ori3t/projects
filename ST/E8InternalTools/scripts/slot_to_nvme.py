#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : slot_to_nvme.py
# Author : Stuart Campbell
# Date   : 2016-06-20
# Version: 0.1
# Version: 0.2 2016-07-06
# Changelog:
#     0.2: Fixed issue seen with interposers, and for CentOS 7.1 where devices names are different
#     0.1: Original file.
#
#--------------------------------------

import sys
import subprocess
import time
import os

# check input parameters.

if (len(sys.argv) < 2):
  print "Invalid Arguments - use python slot_to_nvme.py <slot number>(1..24)|all"
  print ""
  sys.exit(1)


UserInput=sys.argv[1]

StartDrive = 0
EndDrive = 0

if (UserInput == "all"):
  StartDrive = 1
  EndDrive = 24
elif UserInput.isdigit():
  if ( (int(UserInput) >= 1) and (int(UserInput) <= 24) ):
    StartDrive = int(UserInput)
    EndDrive = int(UserInput)

if( (StartDrive == 0) or (EndDrive == 0) ):
  print "Invalid Arguments - use python slot_to_nvme.py <slot number>(1..24)|all"
  print ""
  sys.exit(1)

#print "Slot:", StartDrive, EndDrive

for SlotNo in range (StartDrive, (EndDrive + 1)):

  # For every slot, check the PCI device info in /sys/bus/pci/slots/address

  SlotAddress = "/sys/bus/pci/slots/" + str(SlotNo) + "/address"

  if(os.path.exists(SlotAddress) != True):
    #print "No Slot: ", SlotNo
    continue

  # Valid slot number, so check PCI device info
  SSDBDF = open(SlotAddress,'r').read().rstrip('\n')

  # CentOS 7.1, with NVMe 0.9 driver doesn't use nvme, uses misc and block instead.
  NVMePath = "/sys/bus/pci/devices/" + SSDBDF + ".0/nvme"
  MiscPath = "/sys/bus/pci/devices/" + SSDBDF + ".0/misc"

  if( (os.path.exists(NVMePath) != True) and (os.path.exists(MiscPath) != True) ):
    # See is there an interposer present, if there is, adjust the device no.
    VendorPath = "/sys/bus/pci/devices/" + SSDBDF + ".0/vendor"
    DevicePath = "/sys/bus/pci/devices/" + SSDBDF + ".0/device"
    

    if( (os.path.exists(VendorPath) != True) or (os.path.exists(DevicePath) != True) ):
      continue

    Vendor = open(VendorPath,'r').read().rstrip('\n')
    Device = open(DevicePath,'r').read().rstrip('\n')

    if( (Vendor == "0x10b5") and (Device == "0x8713") ):
      # check for a SSD present on the interposer. 
      BusNo = ( (int(SSDBDF[5],base=16) << 4) + int(SSDBDF[6],base=16) )
      BusNo = BusNo + 2  

      NVMePath = "/sys/bus/pci/devices/0000:" + format(BusNo,'02x') + ":00.0/nvme"
      MiscPath = "/sys/bus/pci/devices/0000:" + format(BusNo,'02x') + ":00.0/misc"

  if( (os.path.exists(NVMePath) != True) and (os.path.exists(MiscPath) != True) ):
    continue

  # now we know there is an NVMe device here, so get the handle.

  if(os.path.exists(NVMePath) != True):
    # CentOS 7.1 has nvme device listed in "misc" path
    NVMePath = MiscPath

  NVMeDevice = os.listdir(NVMePath)

  if (UserInput == "all"):
    print "Slot:", SlotNo, "NVMe Device:", NVMeDevice[0]
  else:
    print NVMeDevice[0]

