#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : get_slot_status.py
# Author : Stuart Campbell
# Date   : 2016-06-20
# Version: 0.1
# Version: 0.2 2016-09-25
# Changelog:
#     0.2: Added for remote (over IPMI) control.
#
# Optional input parameters:
#                   node name or IP address:  use this instead of local access.
# 
#--------------------------------------

import sys
import subprocess
import time
import os

# some definitions for the bitmaps
STATUS_ATN_LED  = 0x01  # attention LED 0 = on, 1 = off
STATUS_FAIL_LED = 0x02  # Fail LED 0 = on, 1 = off
STATUS_PWR_ENA  = 0x04  # Power Enable 0 = off, 1 = on
STATUS_PRESENT  = 0x10  # Presence 0 = present, 1 = not present
STATUS_PWR_OK   = 0x20  # Power ok 0 = no power, 1 = power ok
STATUS_INT_PRS  = 0x40  # Interposer present 0 = no interposer, 1 = interposer present

# check input parameters.

if (len(sys.argv) < 2):
  print "Invalid Arguments - use python get_slot_status.py <slot number>(1..24)|all"
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
  print "Invalid Arguments - use python get_slot_status.py <slot number>(1..24)|all"
  print ""
  sys.exit(1)

# check for the optional IP address or node name
if (len(sys.argv) > 2):
  Node = sys.argv[2]
else:
  Node = ""

#print "Slot:", StartDrive, EndDrive

# now we have the slot number, set up the necessary bits in the ipmi command.
# the basic syntax is  ipmitool raw 0x3c 0xa7 <slot no>

for SlotNo in range (StartDrive, (EndDrive + 1)):
  print "Slot", str(SlotNo), "Info:"

  # Now issue the command.
  IPMICommand = "ipmitool raw 0x3c 0xa7 " + hex(SlotNo)

  if (Node != ""):
    IPMICommand = IPMICommand + " -U admin -P admin -H " + Node

  #print "IPMICommand: ", IPMICommand

  SlotStatus = str(subprocess.Popen(IPMICommand,shell=True,stdout=subprocess.PIPE).stdout.read())
  SlotStatusHex = (int(SlotStatus[1],base=16) << 4) | int(SlotStatus[2],base=16)

  if( (SlotStatusHex & STATUS_PRESENT) == 0):

      if( (SlotStatusHex & STATUS_INT_PRS) == 0):   # only care about device type if device present
          print "SSD Present  : Direct Attach"
      else:
          print "SSD Present  : Interposer"

  else:
      print "SSD Present  : No"

  if( (SlotStatusHex & STATUS_PWR_ENA) == 0):
      print "Slot Power   : Off"
  else:
      print "Slot Power   : On"
      if( (SlotStatusHex & STATUS_PWR_OK) == 0):    # only care about power status if slot powered on
          print "Power Status : Off"
      else:
          print "Power Status : On"


  if( (SlotStatusHex & STATUS_ATN_LED) == 0):
      print "Attention LED: On"
  else:
      print "Attention LED: Off"

  if( (SlotStatusHex & STATUS_FAIL_LED) == 0):
      print "Fail LED     : On"
  else:
      print "Fail LED     : Off"

  print ""

