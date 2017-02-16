#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : poll_pcie_error_counters.py
# Author : Stuart Campbell stuart@e8storage.com
# Date   : 2016-07-21
# Version: 0.5 2016-11-19
# Version: 0.4 2016-11-18
# Version: 0.3 2016-10-17
# Version: 0.2 2016-10-04
# Changelog:
#     0.5: Fixed bug in clearing port error counts.
#     0.4: Added for framing error checking on PLX upstream ports 
#          Reduced printout, removed "0x" before most hex register printouts to reduce line length.
#          Only clear port receiver errors for port being monitored not complete station.
#     0.3: Added to check recovery count on downstream links on switch
#     0.2: Fixed clearing of interposer bad DLLP/TLP counts.
#     0.1: Original file.
#
# Input parameters:
#		    slot no (1.24)
#
#
#--------------------------------------

import sys
import subprocess
import time
import os
import datetime


Reset = True


if (len(sys.argv) < 2):
  print "Invalid Arguments - use python poll_pcie_error_counters.py <slot number>"
  print ""
  sys.exit(1)


SlotNo= int(sys.argv[1])


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
Port0ReceiverErrorCountReg="BF0"
Port1ReceiverErrorCountReg="BF1"
Port2ReceiverErrorCountReg="BF2"
Port3ReceiverErrorCountReg="BF3"
RecoveryCounterReg="BC4"
FramingErrorStatusReg="724"

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

  if( (PortNo & 0x03) == 0):
    PortReceiverErrorCountReg = Port0ReceiverErrorCountReg
  elif( (PortNo & 0x03) == 1):
    PortReceiverErrorCountReg = Port1ReceiverErrorCountReg
  elif( (PortNo & 0x03) == 2):
    PortReceiverErrorCountReg = Port2ReceiverErrorCountReg
  else:
    PortReceiverErrorCountReg = Port3ReceiverErrorCountReg

  LinkCommand="setpci -s " + DeviceNo + " " + PortReceiverErrorCountReg + ".b"

  try:
   PortReceiverErrorCount = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  except ValueError:
    ReturnValue = 0xff
  else:
   ReturnValue = PortReceiverErrorCount 
  
#  print "Read Port Receiver:", LinkCommand
#  print "PR Error Cnt:", hex(PortReceiverErrorCount), "Port", PortNo 

  return ReturnValue
##########################################


##########################################
def ClearPLXPortReceiverErrorCount (DeviceNo, PortNo):

  #for station ports, check the 8-bit port receiver error counters.  Station ports are multiples of 4, so bits 2:1=0.

  if( (PortNo & 0x03) == 0):
    PortReceiverErrorCountReg = Port0ReceiverErrorCountReg
  elif( (PortNo & 0x03) == 1):
    PortReceiverErrorCountReg = Port1ReceiverErrorCountReg
  elif( (PortNo & 0x03) == 2):
    PortReceiverErrorCountReg = Port2ReceiverErrorCountReg
  else:
    PortReceiverErrorCountReg = Port3ReceiverErrorCountReg

  LinkCommand="setpci -s " + DeviceNo + " " + PortReceiverErrorCountReg + ".b=0"
  subprocess.call(LinkCommand, shell=True)

##########################################


##########################################
def ReadPLXRecoveryCount (DeviceNo, PortNo):

  #On station ports, check the 16-bit recovery counter in the recovery diagnostics register.  Station ports are multiples of 4, so bits 2:1=0.

  # first, set the port number in the appropriate field, bits 26:24
  RecoveryCount = ((PortNo & 0x03) << 24)

  # set the port number by writing to the register
  LinkCommand="setpci -s " + DeviceNo + " " + RecoveryCounterReg + ".l=" + hex(RecoveryCount)
  subprocess.call(LinkCommand, shell=True)

  # now, read the value.
  LinkCommand="setpci -s " + DeviceNo + " " + RecoveryCounterReg + ".l"

  try:
   RecoveryCount = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  except ValueError:
    ReturnValue = 0xffff
  else:
   ReturnValue = (RecoveryCount & 0xffff)   # 16-bit value only.
  
  return ReturnValue
##########################################

##########################################
def ClearPLXRecoveryCount (DeviceNo, PortNo):

  #On station ports, check the 16-bit recovery counter in the recovery diagnostics register.  Station ports are multiples of 4, so bits 2:1=0.

  # first, set the port number in the appropriate field, bits 26:24
  RecoveryCount = ((PortNo & 0x03) << 24)
  RecoveryCount = RecoveryCount | 0x80000000    # bit 31 to reset.

  LinkCommand="setpci -s " + DeviceNo + " " + RecoveryCounterReg + ".l=" + hex(RecoveryCount)
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

##########################################
def ReadPLXFramingErrorRegister (DeviceNo):

    # Bad DLLP Count register
  LinkCommand="setpci -s " + DeviceNo + " " + FramingErrorStatusReg + ".l"
  ReturnValue = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  return ReturnValue
##########################################

##########################################
def ClearPLXFramingErrorRegister (DeviceNo, RegValue):

  LinkCommand="setpci -s " + DeviceNo + " " + FramingErrorStatusReg + ".l=" + hex(RegValue)
  subprocess.call(LinkCommand, shell=True)

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

Loop = 1
UpstreamErrors = 0
DownstreamErrors = 0

print datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3], "Starting Error Monitoring"

while Loop >= 1:

  Offset = int(SlotNo) - 1
  PLXDownstreamDevice = SlotToDeviceMap0[Offset][2]
  PLXStationDevice = SlotToDeviceMap0[Offset][3]

  Error = False

  DeviceNo = SlotToDeviceMap0[Offset][1]
  PLXBus = ReadSecondaryBus(DeviceNo)
  DeviceNo = "0000:" + str(PLXBus) + ":00.0"
  PLXBus = ReadSecondaryBus(DeviceNo)

  DeviceNo = "0000:" + str(PLXBus) + ":" + PLXDownstreamDevice + ".0"

  PCIeDeviceStatus = ReadDeviceStatusRegister(DeviceNo)
  PCIeDeviceStatus = (PCIeDeviceStatus & 0x0f)    # only care about bits 0..3

  # can skip reading any other registers if the device status is zero.
  if ((PCIeDeviceStatus != 0)):

    if( (Reset == True) and (PCIeDeviceStatus != 0) ):
      ClearDeviceStatusRegister(DeviceNo, PCIeDeviceStatus)

    AERUNCStatus = ReadAERUNCRegister(DeviceNo)
    if( (Reset == True) and (AERUNCStatus != 0) ):
      ClearAERUNCRegister(DeviceNo, AERUNCStatus)

    AERCORStatus = ReadAERCORRegister(DeviceNo)
    if( (Reset == True) and (AERCORStatus != 0) ):
      ClearAERCORRegister(DeviceNo, AERCORStatus)

    PortNo = (int(PLXDownstreamDevice[0],base=16) << 4) | int(PLXDownstreamDevice[1],base=16) 

    PLXStationDevice = SlotToDeviceMap0[Offset][3]
    PLXStationDeviceNo = "0000:" + str(PLXBus) + ":" + PLXStationDevice + ".0"

    PortReceiverErrorCount = ReadPLXPortReceiverErrorCount(PLXStationDeviceNo, int(PortNo))

    RecoveryCount = ReadPLXRecoveryCount(PLXStationDeviceNo, int(PortNo))

    BadTLPCount = ReadPLXBadTLPCount(DeviceNo)
    BadDLLPCount = ReadPLXBadDLLPCount(DeviceNo)

    FramingErrorStatus = ReadPLXFramingErrorRegister(DeviceNo)

    if(Reset == True):
      if (BadTLPCount > 0):
        ClearPLXBadTLPCount(DeviceNo)
      if (BadDLLPCount > 0):
        ClearPLXBadDLLPCount(DeviceNo)
      if (PortReceiverErrorCount > 0):
        ClearPLXPortReceiverErrorCount(PLXStationDeviceNo, int(PortNo))
      if (RecoveryCount > 0):
        ClearPLXRecoveryCount(PLXStationDeviceNo, int(PortNo))
      if (FramingErrorStatus != 0):
        ClearPLXFramingErrorRegister(DeviceNo, FramingErrorStatus)

    if( (Loop > 1) and \
        ((PCIeDeviceStatus != 0) or (BadTLPCount > 0) or (BadDLLPCount > 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or \
         (PortReceiverErrorCount != 0) or (RecoveryCount != 0)) ):
      UpstreamErrors = UpstreamErrors + 1
      Error = True
      print "Slot:", "{0:2d}".format(SlotNo), "Dev Sts:", "{0:04x}".format(PCIeDeviceStatus), \
          "AER UNC:", "{0:08x}".format(AERUNCStatus), "AER COR:", "{0:04x}".format(AERCORStatus), \
          "Bad TLP:", "{0:08x}".format(BadTLPCount), "Bad DLLP:", "{0:08x}".format(BadDLLPCount), \
          "PRT ERR:", "{0:02x}".format(PortReceiverErrorCount), \
          "REC:", "{0:04x}".format(RecoveryCount), \
          "FRM:", "{0:08x}".format(FramingErrorStatus)



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

  PCIeDeviceStatus = ReadDeviceStatusRegister(AttachedSSDDeviceNo)

  PCIeDeviceStatus = (PCIeDeviceStatus & 0x0f)    # only care about bits 0..3

  # can skip reading any other registers if the device status is zero.
  if ((PCIeDeviceStatus != 0)):

    if( (Reset == True) and (PCIeDeviceStatus != 0) ):
      ClearDeviceStatusRegister(AttachedSSDDeviceNo, PCIeDeviceStatus)

    AERUNCStatus = ReadAERUNCRegister(AttachedSSDDeviceNo)
    if( (Reset == True) and (AERUNCStatus != 0) ):
      ClearAERUNCRegister(AttachedSSDDeviceNo, AERUNCStatus)

    AERCORStatus = ReadAERCORRegister(AttachedSSDDeviceNo)
    if( (Reset == True) and (AERCORStatus != 0) ):
      ClearAERCORRegister(AttachedSSDDeviceNo, AERCORStatus)

    if ( (VendorID == '0x10b5') and (DeviceID == '0x8713') ):

      BadTLPCount = ReadPLXBadTLPCount(AttachedSSDDeviceNo)
      BadDLLPCount = ReadPLXBadDLLPCount(AttachedSSDDeviceNo)
      FramingErrorStatus = ReadPLXFramingErrorRegister(AttachedSSDDeviceNo)

      if(Reset == True):
        if (BadTLPCount > 0):
          ClearPLXBadTLPCount(AttachedSSDDeviceNo)
        if (BadDLLPCount > 0):
          ClearPLXBadDLLPCount(AttachedSSDDeviceNo)
        if (FramingErrorStatus != 0):
          ClearPLXFramingErrorRegister(AttachedSSDDeviceNo, FramingErrorStatus)

      if( (Loop > 1) and ((PCIeDeviceStatus != 0) or (BadTLPCount > 0) or (BadDLLPCount > 0) or (AERUNCStatus != 0) or (AERCORStatus != 0)) ):
        DownstreamErrors = DownstreamErrors + 1
        Error = True
        print "Intp:", "{0:2d}".format(SlotNo), "Dev Sts:", "{0:04x}".format(PCIeDeviceStatus), \
            "AER UNC:", "{0:08x}".format(AERUNCStatus), "AER COR:", "{0:04x}".format(AERCORStatus), \
            "Bad TLP:", "{0:08x}".format(BadTLPCount), "Bad DLLP:", "{0:08x}".format(BadDLLPCount), \
            "FRM:", "{0:08x}".format(FramingErrorStatus)

    else:
      if( (Loop > 1) and ((PCIeDeviceStatus != 0) or (AERUNCStatus != 0) or (AERCORStatus != 0)) ):
        DownstreamErrors = DownstreamErrors + 1
        Error = True
        print "SSD :", "{0:2d}".format(SlotNo), "Dev Sts:", "{0:04x}".format(PCIeDeviceStatus), \
              "AER UNC:", "{0:08x}".format(AERUNCStatus), "AER COR:", "{0:04x}".format(AERCORStatus)
  
  if(Error == True):
    print datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3], "Iteration:", "{0:06d}".format(Loop), "Upstream Errors:",UpstreamErrors, "Downstream Errors:", DownstreamErrors

  Loop = Loop + 1


