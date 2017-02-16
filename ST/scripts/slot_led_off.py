#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : slot_led_off.py
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
  print "Invalid Arguments - use python slot_led_off.py <slot number>(1..24)|all"
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
  print "Invalid Arguments - use python slot_led_off.py <slot number>(1..24)|all"
  print ""
  sys.exit(1)

# now we have the slot number, set up the necessary bits in the ipmi command.
# the basic syntax is ipmitool raw 0x3c 0xac <slot no>

for SlotNo in range (StartDrive, (EndDrive + 1)):
  print "Disabling LED on Slot:", str(SlotNo)

  # Now issue the command.
  IPMICommand = "ipmitool raw 0x3c 0xac " + hex(SlotNo) + " 0"
#  print "IPMICommand: ", IPMICommand
#  subprocess.call(IPMICommand, shell=True)
  CmdStatus = str(subprocess.Popen(IPMICommand,shell=True,stdout=subprocess.PIPE).stdout.read())


