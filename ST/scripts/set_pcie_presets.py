#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : set_pcie_presets.py
# Author : Stuart Campbell stuart@e8storage.com
# Date   : 2016-07-22
# Changelog:
#     0.1: Original file.
#
# Input parameters:
#		    slot no (1.24)
#           Upstream TX Preset: 0..10
#           Preset Hint to SSD: 0..10
#           Optional: auto
# 
#
#
#--------------------------------------

import sys
import subprocess
import time
import os
import datetime


Reset = True

if (len(sys.argv) < 4):
  print "Invalid Arguments - use python set_pcie_presets.py <slot number> <Upstream Preset (0..10)> <Downstream Preset Hint (0..10)> <opt:auto>"
  print ""
  sys.exit(1)

ParametersValid = True

SlotNo = sys.argv[1]

if SlotNo.isdigit():
  if ((int(SlotNo) < 1) or (int(SlotNo) > 24) ):
    ParametersValid = False
else:
    ParametersValid = False


Input = sys.argv[2]
if Input.isdigit():
  if (int(Input) > 10):
    ParametersValid = False
  else:
    UpstreamPreset = int(Input)
else:
  ParametersValid = False

Input = sys.argv[3]
if Input.isdigit():
  if (int(Input) > 10):
    ParametersValid = False
  else:
    DownstreamPreset = int(Input)
else:
  ParametersValid = False

if (ParametersValid == False):
  print "Invalid Arguments - use python set_pcie_presets.py <slot number> <Upstream Preset (0..10)> <Downstream Preset Hint (0..10)> <opt:auto>"
  print ""
  sys.exit(1)


AutoMode = False

if (len(sys.argv) > 4):
  if (sys.argv[4] == "auto"):
    AutoMode = True

print "Slot:", SlotNo, "Upstream:", UpstreamPreset, "Downstream:", DownstreamPreset, "Auto:", AutoMode


UpstreamLNKCTL="78"

# PLX Specific registers
UserLaneEqControlReg="BC8"
EqualisationControlReg="BD8"

CPU0_RC="0000:00:02.0"
CPU1_RC="0000:80:03.0"


##########################################
def ReadSecondaryBus (DeviceNo):

  LinkCommand = "setpci -s " + DeviceNo + " SECONDARY_BUS.b"
  try:
    RegValue = str(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().rstrip('\n'))
  except ValueError:
    RegValue = "ff"
  return RegValue
##########################################


# Start with each slot, which is hard-coded to specific ports.

SlotToDeviceMap0 = [ [1, CPU0_RC, "0C", "0C"],
                     [2, CPU0_RC, "0D", "0C"],
                     [3, CPU0_RC, "0E", "0C"],
                     [4, CPU0_RC, "0F", "0C"],
                     [5, CPU0_RC, "04", "04"],
                     [6, CPU0_RC, "05", "04"],
                     [7, CPU0_RC, "06", "04"],
                     [8, CPU0_RC, "07", "04"],
                     [9, CPU0_RC, "00", "00"],
                     [10, CPU0_RC, "01", "00"],
                     [11, CPU0_RC, "02", "00"],
                     [12, CPU0_RC, "03", "00"], 
                     [13, CPU1_RC, "04", "04"], 
                     [14, CPU1_RC, "05", "04"], 
                     [15, CPU1_RC, "06", "04"], 
                     [16, CPU1_RC, "07", "04"], 
                     [17, CPU1_RC, "00", "00"], 
                     [18, CPU1_RC, "01", "00"], 
                     [19, CPU1_RC, "02", "00"], 
                     [20, CPU1_RC, "03", "00"], 
                     [21, CPU1_RC, "08", "08"], 
                     [22, CPU1_RC, "09", "08"], 
                     [23, CPU1_RC, "0A", "08"], 
                     [24, CPU1_RC, "0B", "08"] ] 


Offset = int(SlotNo) - 1
PLXDownstreamDevice = SlotToDeviceMap0[Offset][2]
PLXStationDevice = SlotToDeviceMap0[Offset][3]

DeviceNo = SlotToDeviceMap0[Offset][1]
PLXBus = ReadSecondaryBus(DeviceNo)
DeviceNo = "0000:" + str(PLXBus) + ":00.0"
PLXBus = ReadSecondaryBus(DeviceNo)

DeviceNo = "0000:" + str(PLXBus) + ":" + PLXDownstreamDevice + ".0"

PortNo = (int(PLXDownstreamDevice[0],base=16) << 4) | int(PLXDownstreamDevice[1],base=16) 

PLXStationDevice = SlotToDeviceMap0[Offset][3]
PLXStationDeviceNo = "0000:" + str(PLXBus) + ":" + PLXStationDevice + ".0"

# first, read the current user lane equalisation control reg, BC8h
LinkCommand="setpci -s " + PLXStationDeviceNo + " " + UserLaneEqControlReg + ".l"
#print "Get Link Command: ", LinkCommand
UserLaneEqControl = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)

#print "Old Value:", "{0:#010x}".format(UserLaneEqControl)

# clear the value for the current port
BitMask = ~(0xff << (8*(PortNo & 0x03)) )
UserLaneEqControl = (UserLaneEqControl & BitMask)

NewPreset = (DownstreamPreset << 4) | UpstreamPreset

# set the new value for the current port
BitMask = (NewPreset << (8*(PortNo & 0x03)) )
UserLaneEqControl = (UserLaneEqControl | BitMask)

#print "New Value:", "{0:#010x}".format(UserLaneEqControl)

LinkCommand="setpci -s " + PLXStationDeviceNo + " " + UserLaneEqControlReg + ".l=" + hex(UserLaneEqControl)
#print "Set Link Command: ", LinkCommand
subprocess.call(LinkCommand, shell=True)

# set auto mode, register BD8h


LinkCommand="setpci -s " + PLXStationDeviceNo + " " + EqualisationControlReg + ".l"
EqualisationControl = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)

#print "Old Auto Value:", "{0:#010x}".format(EqualisationControl)

# clear the value for the current port
BitMask = ~(0x01 << (PortNo & 0x03) )
EqualisationControl = (EqualisationControl & BitMask)

if (AutoMode == False):
  BitMask = (0x01 << (PortNo & 0x03) )
  EqualisationControl = (EqualisationControl | BitMask)

#print "New Auto Value:", "{0:#010x}".format(EqualisationControl)

LinkCommand="setpci -s " + PLXStationDeviceNo + " " + EqualisationControlReg + ".l=" + hex(EqualisationControl)
#print "Set Link Command: ", LinkCommand
subprocess.call(LinkCommand, shell=True)

# take the link down and back up to get it to retrain.
# first disable link.
LinkCommand="setpci -s " + DeviceNo + " " + UpstreamLNKCTL + ".w=0010"
subprocess.call(LinkCommand, shell=True)

time.sleep(1)

# finally re-enable link.
LinkCommand="setpci -s " + DeviceNo + " " + UpstreamLNKCTL + ".w=0000"
subprocess.call(LinkCommand, shell=True)

