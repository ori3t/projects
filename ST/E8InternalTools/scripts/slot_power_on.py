#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : slot_power_on.py
# Author : Stuart Campbell
# Date   : 2016-06-20
# Version: 0.2 2016-09-23
# Changelog:
#     0.2: Added for remote (over IPMI) control.
#     0.1: Original file.
# 
# Optional input parameters:
#                   node name or IP address:  use this instead of local access.
#
#--------------------------------------

import sys
import subprocess
import time
import os

# check input parameters.

if (len(sys.argv) < 2):
  print "Invalid Arguments - use python slot_power_on.py <slot number>(1..24)|all"
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
  print "Invalid Arguments - use python slot_power_on.py <slot number>(1..24)|all"
  print ""
  sys.exit(1)

# check for the optional IP address or node name
if (len(sys.argv) > 2):
  Node = sys.argv[2]
else:
  Node = ""

# now we have the slot number, set up the necessary bits in the ipmi command.
# the basic syntax is  ipmitool raw 0x3c 0xae 1 bitmap1 bitmap2 bitmap3
# where bitmap1[0..7] correspond to drive 1..8, bitmap2[0..7] correspond to drive 9..16 and
# bitmap3[0..7] correspond to drive 17..24

DriveMask1 = 0
DriveMask2 = 0
DriveMask3 = 0


for SlotNo in range (StartDrive, (EndDrive + 1)):
  dmesg="echo \"E8_slot_power_on: Enable Slot " + str(SlotNo) + " " + Node + "\"" + " > /dev/kmsg"
  subprocess.call(dmesg, shell=True)
  print "Enabling Slot:", str(SlotNo)

  if ((SlotNo >= 1) and (SlotNo <= 8) ):
    DriveMask1 = DriveMask1 | (0x01 << (SlotNo -1))

  if ((SlotNo >= 9) and (SlotNo <= 16) ):
    DriveMask2 = DriveMask2 | (0x01 << (SlotNo -9))

  if ((SlotNo >= 17) and (SlotNo <= 24) ):
    DriveMask3 = DriveMask3 | (0x01 << (SlotNo -17))

# Now issue the command.
IPMICommand = "ipmitool raw 0x3c 0xae 1 " + hex(DriveMask1) + " " + hex(DriveMask2) + " " + hex(DriveMask3)

if (Node != ""):
  IPMICommand = IPMICommand + " -U admin -P admin -H " + Node

print "IPMICommand: ", IPMICommand

subprocess.call(IPMICommand, shell=True)
