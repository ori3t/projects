#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : slot_to_numa_node.py
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
  print "Invalid Arguments - use python slot_to_numa_node.py <slot number>(1..24)|all"
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
  print "Invalid Arguments - use python slot_to_numa_node.py <slot number>(1..24)|all"
  print ""
  sys.exit(1)

#print "Slot:", StartDrive, EndDrive

for SlotNo in range (StartDrive, (EndDrive + 1)):

  # For every slot, check the PCI device info in /sys/bus/pci/slots/address

  SlotAddress = "/sys/bus/pci/slots/" + str(SlotNo) + "/address"

  if(os.path.exists(SlotAddress) != True):
    #print "No Slot: ", SlotNo
    continue

  # Valid slot number, so extract bus number to identify node.  < 128 = 0, > 128 = 1.
  # This should be true for all 2-node systems, very rare to have unequal bus allocation.
  SSDBDF = open(SlotAddress,'r').read().rstrip('\n')
  BusNo = ( (int(SSDBDF[5],base=16) << 4) + int(SSDBDF[6],base=16) )
  if(BusNo < 128):
      NUMANode = 0
  else:
      NUMANode = 1

  if (UserInput == "all"):
    print "Slot:", SlotNo, "NUMA Node:", NUMANode
  else:
    print NUMANode

