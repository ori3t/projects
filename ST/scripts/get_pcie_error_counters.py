#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : get_pcie_error_counters.py
# Author : Stuart Campbell stuart@e8storage.com
# Date   : 2016-06-20
# Version: 0.4 2016-09-13
# Version: 0.3 2016-07-05
# Version: 0.2 2016-07-02
# Changelog:
#     0.4: Fixed clearing of interposer bad DLLP/TLP counts.
#     0.3: Added slot number for devices that are un-enumerated.  Typically indicates failure.
#     0.2: Complete rewrite.  Based on 2U topology
#     0.1: Original file.

# Optional input parameters:
#                   reset:  reset any errors detected
#                   quiet:  only print when error detected
#                   silent: print nothing (used with reset to just clear errors)
#                   all:    check all devices in system, including plug-in cards
#
#--------------------------------------

import sys
import subprocess
import time
import os


Reset = False
Quiet = False
Silent = False
AllDevices = False

if (len(sys.argv) > 1):
  if (sys.argv[1] == "reset"):
    Reset = True
  if (sys.argv[1] == "quiet"):
    Quiet = True
  if (sys.argv[1] == "silent"):
    Silent = True
  if (sys.argv[1] == "all"):
    AllDevices = True

if (len(sys.argv) > 2):
  if (sys.argv[2] == "reset"):
    Reset = True
  if (sys.argv[2] == "quiet"):
    Quiet = True
  if (sys.argv[2] == "silent"):
    Silent = True
  if (sys.argv[2] == "all"):
    AllDevices = True

if (len(sys.argv) > 3):
  if (sys.argv[3] == "reset"):
    Reset = True
  if (sys.argv[3] == "quiet"):
    Quiet = True
  if (sys.argv[3] == "silent"):
    Silent = True
  if (sys.argv[3] == "all"):
    AllDevices = True

if (len(sys.argv) > 4):
  if (sys.argv[4] == "reset"):
    Reset = True
  if (sys.argv[4] == "quiet"):
    Quiet = True
  if (sys.argv[4] == "silent"):
    Silent = True
  if (sys.argv[4] == "all"):
    AllDevices = True


PCIeCapOff="00"
PCIeCapSlotOff="14"
PCIeDevStatusOff="0A"
PCIeLinkCapOff="0C"


#offsets for the AER regs.  
AERUNCStatusOff="04"
AERCORStatusOff="10"

# PLX Specific registers
BadTLPCountReg="FAC"
BadDLLPCountReg="FB0"
PortReceiverErrorCountReg="BF0"

CPU0_RC="0000:00:02.0"
CPU1_RC="0000:80:03.0"

##########################################
def ReadDeviceStatusRegister (DeviceNo):

  # Device Status register
  LinkCommand = "setpci -s " + DeviceNo + " CAP_EXP+" + PCIeDevStatusOff + ".w"
  try:
    RegValue = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  except ValueError:
    RegValue = 0xffff
  return RegValue
##########################################

##########################################
def ClearDeviceStatusRegister (DeviceNo, RegValue):

  # Device Status register
  LinkCommand = "setpci -s " + DeviceNo + " CAP_EXP+" + PCIeDevStatusOff + ".w=" + hex(RegValue)
  subprocess.call(LinkCommand, shell=True)
##########################################


##########################################
def ReadAERUNCRegister (DeviceNo):

  LinkCommand = "setpci -s " + DeviceNo + " ECAP_AER+" + AERUNCStatusOff + ".l"
  try:
    RegValue = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  except ValueError:
    RegValue = 0xffffffff
  return RegValue
##########################################

##########################################
def ClearAERUNCRegister (DeviceNo, RegValue):

  LinkCommand = "setpci -s " + DeviceNo + " ECAP_AER+" + AERUNCStatusOff + ".l=" + hex(RegValue)
  subprocess.call(LinkCommand, shell=True)
##########################################


##########################################
def ReadAERCORRegister (DeviceNo):

  LinkCommand = "setpci -s " + DeviceNo + " ECAP_AER+" + AERCORStatusOff + ".w"
  try:
    RegValue = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  except ValueError:
    RegValue = 0xffffffff
  return RegValue
##########################################

##########################################
def ClearAERCORRegister (DeviceNo, RegValue):

  LinkCommand = "setpci -s " + DeviceNo + " ECAP_AER+" + AERCORStatusOff + ".w=" + hex(RegValue)
  subprocess.call(LinkCommand, shell=True)
##########################################

##########################################
def ReadSecondaryBus (DeviceNo):

  LinkCommand = "setpci -s " + DeviceNo + " SECONDARY_BUS.b"
  try:
    RegValue = str(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().rstrip('\n'))
  except ValueError:
    RegValue = "ff"
  return RegValue
##########################################

##########################################
def ReadPLXPortReceiverErrorCount (DeviceNo, PortNo):

  #for station ports, check the 8-bit port receiver error counters.  Station ports are multiples of 4, so bits 2:1=0.

  LinkCommand="setpci -s " + DeviceNo + " " + PortReceiverErrorCountReg + ".l"
  try:
   PortReceiverErrorCount = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  except ValueError:
    ReturnValue = 0xff
  else:
   ReturnValue = ((PortReceiverErrorCount >> (8*(PortNo & 0x03))) & 0xff) 
  
#  print LinkCommand
#  print "PR Error Cnt:", hex(PortReceiverErrorCount), "Port", PortNo 

  return ReturnValue
##########################################

##########################################
def ClearPLXPortReceiverErrorCount (DeviceNo):

  LinkCommand="setpci -s " + DeviceNo + " " + PortReceiverErrorCountReg + ".l=0"
  subprocess.call(LinkCommand, shell=True)

##########################################

##########################################
def ReadPLXBadTLPCount (DeviceNo):

    # Bad TLP Count register
  LinkCommand="setpci -s " + DeviceNo + " " + BadTLPCountReg + ".l"
  ReturnValue = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  return ReturnValue
##########################################

##########################################
def ClearPLXBadTLPCount (DeviceNo):

  LinkCommand="setpci -s " + DeviceNo + " " + BadTLPCountReg + ".l=0"
  subprocess.call(LinkCommand, shell=True)

##########################################

##########################################
def ReadPLXBadDLLPCount (DeviceNo):

    # Bad DLLP Count register
  LinkCommand="setpci -s " + DeviceNo + " " + BadDLLPCountReg + ".l"
  ReturnValue = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  return ReturnValue
##########################################

##########################################
def ClearPLXBadDLLPCount (DeviceNo):

  LinkCommand="setpci -s " + DeviceNo + " " + BadDLLPCountReg + ".l=0"
  subprocess.call(LinkCommand, shell=True)

##########################################


# First, CPU 0 upstream.  

DeviceNo = CPU0_RC

PCIeDeviceStatus = ReadDeviceStatusRegister(DeviceNo)
PCIeDeviceStatus = (PCIeDeviceStatus & 0x0f)    # only care about bits 0..3
if( (Reset == True) and (PCIeDeviceStatus != 0) ):
  ClearDeviceStatusRegister(DeviceNo, PCIeDeviceStatus)

AERUNCStatus = ReadAERUNCRegister(DeviceNo)
if( (Reset == True) and (AERUNCStatus != 0) ):
  ClearAERUNCRegister(DeviceNo, AERUNCStatus)

AERCORStatus = ReadAERCORRegister(DeviceNo)
if( (Reset == True) and (AERCORStatus != 0) ):
  ClearAERCORRegister(DeviceNo, AERCORStatus)


if( (Silent == False) and ((PCIeDeviceStatus != 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (Quiet == False)) ):
  print "CPU0 RC:", "Dev Sts:", "{0:#06x}".format(PCIeDeviceStatus), \
        "AER UNC:", "{0:#010x}".format(AERUNCStatus), "AER COR:", "{0:#06x}".format(AERCORStatus)

# Next PLX 0 upstream.  
# get bus info.

DeviceNo = CPU0_RC
PLXBus = ReadSecondaryBus(DeviceNo)
DeviceNo = "0000:" + str(PLXBus) + ":00.0"


PCIeDeviceStatus = ReadDeviceStatusRegister(DeviceNo)
PCIeDeviceStatus = (PCIeDeviceStatus & 0x0f)    # only care about bits 0..3
if( (Reset == True) and (PCIeDeviceStatus != 0) ):
  ClearDeviceStatusRegister(DeviceNo, PCIeDeviceStatus)

AERUNCStatus = ReadAERUNCRegister(DeviceNo)
if( (Reset == True) and (AERUNCStatus != 0) ):
  ClearAERUNCRegister(DeviceNo, AERUNCStatus)

AERCORStatus = ReadAERCORRegister(DeviceNo)
if( (Reset == True) and (AERCORStatus != 0) ):
  ClearAERCORRegister(DeviceNo, AERCORStatus)

PortReceiverErrorCount = ReadPLXPortReceiverErrorCount(DeviceNo, 0x08)

BadTLPCount = ReadPLXBadTLPCount(DeviceNo)
if( (Reset == True) and (BadTLPCount != 0) ):
  ClearPLXBadTLPCount(DeviceNo)

BadDLLPCount = ReadPLXBadDLLPCount(DeviceNo)
if( (Reset == True) and (BadDLLPCount != 0) ):
  ClearPLXBadDLLPCount(DeviceNo)


if( (Silent == False) and ((PCIeDeviceStatus != 0) or (BadTLPCount > 0) or (BadDLLPCount > 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (PortReceiverErrorCount != 0) or (Quiet == False)) ):
  print "PLX0 UP:", "Dev Sts:", "{0:#06x}".format(PCIeDeviceStatus), \
        "AER UNC:", "{0:#010x}".format(AERUNCStatus), "AER COR:", "{0:#06x}".format(AERCORStatus), \
        "Bad TLP:", "{0:#010x}".format(BadTLPCount), "Bad DLLP:", "{0:#010x}".format(BadDLLPCount), \
        "PRT ERR:", "{0:#04x}".format(PortReceiverErrorCount)


# CPU 1 upstream.  

DeviceNo = CPU1_RC

PCIeDeviceStatus = ReadDeviceStatusRegister(DeviceNo)
PCIeDeviceStatus = (PCIeDeviceStatus & 0x0f)    # only care about bits 0..3
if( (Reset == True) and (PCIeDeviceStatus != 0) ):
  ClearDeviceStatusRegister(DeviceNo, PCIeDeviceStatus)

AERUNCStatus = ReadAERUNCRegister(DeviceNo)
if( (Reset == True) and (AERUNCStatus != 0) ):
  ClearAERUNCRegister(DeviceNo, AERUNCStatus)

AERCORStatus = ReadAERCORRegister(DeviceNo)
if( (Reset == True) and (AERCORStatus != 0) ):
  ClearAERCORRegister(DeviceNo, AERCORStatus)


if( (Silent == False) and ((PCIeDeviceStatus != 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (Quiet == False)) ):
  print "CPU1 RC:", "Dev Sts:", "{0:#06x}".format(PCIeDeviceStatus), \
        "AER UNC:", "{0:#010x}".format(AERUNCStatus), "AER COR:", "{0:#06x}".format(AERCORStatus)

# Next PLX 0 upstream.  
# get bus info.

DeviceNo = CPU1_RC
PLXBus = ReadSecondaryBus(DeviceNo)
DeviceNo = "0000:" + str(PLXBus) + ":00.0"


PCIeDeviceStatus = ReadDeviceStatusRegister(DeviceNo)
PCIeDeviceStatus = (PCIeDeviceStatus & 0x0f)    # only care about bits 0..3
if( (Reset == True) and (PCIeDeviceStatus != 0) ):
  ClearDeviceStatusRegister(DeviceNo, PCIeDeviceStatus)

AERUNCStatus = ReadAERUNCRegister(DeviceNo)
if( (Reset == True) and (AERUNCStatus != 0) ):
  ClearAERUNCRegister(DeviceNo, AERUNCStatus)

AERCORStatus = ReadAERCORRegister(DeviceNo)
if( (Reset == True) and (AERCORStatus != 0) ):
  ClearAERCORRegister(DeviceNo, AERCORStatus)

PortReceiverErrorCount = ReadPLXPortReceiverErrorCount(DeviceNo, 0x0C)

BadTLPCount = ReadPLXBadTLPCount(DeviceNo)
if( (Reset == True) and (BadTLPCount != 0) ):
  ClearPLXBadTLPCount(DeviceNo)

BadDLLPCount = ReadPLXBadDLLPCount(DeviceNo)
if( (Reset == True) and (BadDLLPCount != 0) ):
  ClearPLXBadDLLPCount(DeviceNo)

if( (Silent == False) and ((PCIeDeviceStatus != 0) or (BadTLPCount > 0) or (BadDLLPCount > 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (PortReceiverErrorCount != 0) or (Quiet == False)) ):
  print "PLX1 UP:", "Dev Sts:", "{0:#06x}".format(PCIeDeviceStatus), \
        "AER UNC:", "{0:#010x}".format(AERUNCStatus), "AER COR:", "{0:#06x}".format(AERCORStatus), \
        "Bad TLP:", "{0:#010x}".format(BadTLPCount), "Bad DLLP:", "{0:#010x}".format(BadDLLPCount), \
        "PRT ERR:", "{0:#04x}".format(PortReceiverErrorCount)


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


for i in range(len(SlotToDeviceMap0)):
  SlotNo = SlotToDeviceMap0[i][0]
  PLXDownstreamDevice = SlotToDeviceMap0[i][2]
  PLXStationDevice = SlotToDeviceMap0[i][3]


  DeviceNo = SlotToDeviceMap0[i][1]
  PLXBus = ReadSecondaryBus(DeviceNo)
  DeviceNo = "0000:" + str(PLXBus) + ":00.0"
  PLXBus = ReadSecondaryBus(DeviceNo)

  DeviceNo = "0000:" + str(PLXBus) + ":" + PLXDownstreamDevice + ".0"

  PCIeDeviceStatus = ReadDeviceStatusRegister(DeviceNo)
  PCIeDeviceStatus = (PCIeDeviceStatus & 0x0f)    # only care about bits 0..3
  if( (Reset == True) and (PCIeDeviceStatus != 0) ):
    ClearDeviceStatusRegister(DeviceNo, PCIeDeviceStatus)

  AERUNCStatus = ReadAERUNCRegister(DeviceNo)
  if( (Reset == True) and (AERUNCStatus != 0) ):
    ClearAERUNCRegister(DeviceNo, AERUNCStatus)

  AERCORStatus = ReadAERCORRegister(DeviceNo)
  if( (Reset == True) and (AERCORStatus != 0) ):
    ClearAERCORRegister(DeviceNo, AERCORStatus)

  PortNo = (int(PLXDownstreamDevice[0],base=16) << 4) | int(PLXDownstreamDevice[1],base=16) 

  PLXStationDevice = SlotToDeviceMap0[i][3]
  PLXStationDeviceNo = "0000:" + str(PLXBus) + ":" + PLXStationDevice + ".0"

  PortReceiverErrorCount = ReadPLXPortReceiverErrorCount(PLXStationDeviceNo, int(PortNo))

  BadTLPCount = ReadPLXBadTLPCount(DeviceNo)
  BadDLLPCount = ReadPLXBadDLLPCount(DeviceNo)

  if(Reset == True):
    ClearPLXBadTLPCount(DeviceNo)
    ClearPLXBadDLLPCount(DeviceNo)

  if( (Silent == False) and ((PCIeDeviceStatus != 0) or (BadTLPCount > 0) or (BadDLLPCount > 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (PortReceiverErrorCount != 0) or (Quiet == False)) ):
    print "Slot:", "{0:2d}".format(SlotNo), "Dev Sts:", "{0:#06x}".format(PCIeDeviceStatus), \
        "AER UNC:", "{0:#010x}".format(AERUNCStatus), "AER COR:", "{0:#06x}".format(AERCORStatus), \
        "Bad TLP:", "{0:#010x}".format(BadTLPCount), "Bad DLLP:", "{0:#010x}".format(BadDLLPCount), \
        "PRT ERR:", "{0:#04x}".format(PortReceiverErrorCount)

  # check is there an attached device, if so, look at that.

  SSDBus = ReadSecondaryBus(DeviceNo)
  AttachedSSDDeviceNo = "0000:" + str(SSDBus) + ":00.0"

  DevicePath = "/sys/bus/pci/devices/" + AttachedSSDDeviceNo

  if(os.path.exists(DevicePath) != True):
    print "SSD :", "{0:2d}".format(SlotNo), "Device Not Present: ", AttachedSSDDeviceNo
    continue

  VendorIDAddr = DevicePath + "/vendor"
  VendorID = open(VendorIDAddr,'r').read().rstrip('\n')

  DeviceIDAddr = DevicePath + "/device"
  DeviceID = open(DeviceIDAddr,'r').read().rstrip('\n')

  if ( (VendorID == '0x10b5') and (DeviceID == '0x8713') ):
    PlxDevice = True
#    print "PLX Interposer: ", AttachedSSDDeviceNo
    BadTLPCount = ReadPLXBadTLPCount(AttachedSSDDeviceNo)
    BadDLLPCount = ReadPLXBadDLLPCount(AttachedSSDDeviceNo)

    if(Reset == True):
      ClearPLXBadTLPCount(AttachedSSDDeviceNo)
      ClearPLXBadDLLPCount(AttachedSSDDeviceNo)

  else:
    PlxDevice = False


  PCIeDeviceStatus = ReadDeviceStatusRegister(AttachedSSDDeviceNo)
  PCIeDeviceStatus = (PCIeDeviceStatus & 0x0f)    # only care about bits 0..3
  if( (Reset == True) and (PCIeDeviceStatus != 0) ):
    ClearDeviceStatusRegister(AttachedSSDDeviceNo, PCIeDeviceStatus)

  AERUNCStatus = ReadAERUNCRegister(AttachedSSDDeviceNo)
  if( (Reset == True) and (AERUNCStatus != 0) ):
    ClearAERUNCRegister(AttachedSSDDeviceNo, AERUNCStatus)

  AERCORStatus = ReadAERCORRegister(AttachedSSDDeviceNo)
  if( (Reset == True) and (AERCORStatus != 0) ):
    ClearAERCORRegister(AttachedSSDDeviceNo, AERCORStatus)

  if (PlxDevice == True):
    if( (Silent == False) and ((PCIeDeviceStatus != 0) or (BadTLPCount > 0) or (BadDLLPCount > 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (Quiet == False)) ):
      print "Intp:", "{0:2d}".format(SlotNo), "Dev Sts:", "{0:#06x}".format(PCIeDeviceStatus), \
          "AER UNC:", "{0:#010x}".format(AERUNCStatus), "AER COR:", "{0:#06x}".format(AERCORStatus), \
          "Bad TLP:", "{0:#010x}".format(BadTLPCount), "Bad DLLP:", "{0:#010x}".format(BadDLLPCount)

  else:
    if( (Silent == False) and ((PCIeDeviceStatus != 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (Quiet == False))):
        print "SSD :", "{0:2d}".format(SlotNo), "Dev Sts:", "{0:#06x}".format(PCIeDeviceStatus), \
              "AER UNC:", "{0:#010x}".format(AERUNCStatus), "AER COR:", "{0:#06x}".format(AERCORStatus)

if(Reset == True):
  # clear all the PLX receiver counters

  DeviceNo = CPU0_RC
  PLXBus = ReadSecondaryBus(DeviceNo)

  DeviceNo = "0000:" + str(PLXBus) + ":00.0"
  ClearPLXPortReceiverErrorCount(DeviceNo)

  PLXBus = ReadSecondaryBus(DeviceNo)

  DeviceNo = "0000:" + str(PLXBus) + ":00.0"
  ClearPLXPortReceiverErrorCount(DeviceNo)

  DeviceNo = "0000:" + str(PLXBus) + ":04.0"
  ClearPLXPortReceiverErrorCount(DeviceNo)

  DeviceNo = "0000:" + str(PLXBus) + ":0C.0"
  ClearPLXPortReceiverErrorCount(DeviceNo)

  DeviceNo = CPU1_RC
  PLXBus = ReadSecondaryBus(DeviceNo)

  DeviceNo = "0000:" + str(PLXBus) + ":00.0"
  ClearPLXPortReceiverErrorCount(DeviceNo)

  PLXBus = ReadSecondaryBus(DeviceNo)

  DeviceNo = "0000:" + str(PLXBus) + ":00.0"
  ClearPLXPortReceiverErrorCount(DeviceNo)

  DeviceNo = "0000:" + str(PLXBus) + ":04.0"
  ClearPLXPortReceiverErrorCount(DeviceNo)

  DeviceNo = "0000:" + str(PLXBus) + ":08.0"
  ClearPLXPortReceiverErrorCount(DeviceNo)

