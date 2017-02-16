#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : validate_pci.py
# Author : Stuart Campbell stuart@e8storage.com
# Date   : 2016-09-23
# Version: 0.7 2017-01-25
# Version: 0.6 2016-12-15
# Version: 0.5 2016-11-18
# Version: 0.4 2016-11-17
# Version: 0.3 2016-10-17
# Version: 0.2 2016-09-28
# Changelog:
#     0.7: Changed default parameters to assume "quiet" and "reset".
#          Added "help" option
#          Added clarity to error printout for Mellanox PCIe card, replaced "AIC" with MLNX
#     0.6: Added support for OB122E-PH, new model name for 1U10.
#     0.5: Fixed bug in clearing framing error checking on PLX upstream ports registers
#     0.4: Added for framing error checking on PLX upstream ports 
#          Reduced printout, removed "0x" before most hex register printouts to reduce line length.
#     0.3: Added for interposer checking on downstream links and attached SSD
#          Clarified device printout
#          Added for detecting difference in upstream and downstream link parameters
#          Added to check recovery count on downstream links on switch
#     0.2: Added to monitor/clear PCIe errors too, and for 1U8
#
# Optional input parameters:
#                   all:        print all info irrespective of errors or not
#                   silent:     do not print PCIe errors
#                   noreset:    do not reset PCIe errors detected
#                   2U24:       force detection as 2U24
#                   1U10:       force detection as 1U10
#                   1U8:        force detection as 1U8 (not implemented yet!)
#
#--------------------------------------

import sys
import subprocess
import time
import os

Quiet = True
Silent = False
Reset = True
SystemType = ""
Help = False

for i in range(len(sys.argv) - 1):
  if (sys.argv[i+1] == "all"):
    Quiet = False
  if (sys.argv[i+1] == "silent"):
    Silent = True
  if (sys.argv[i+1] == "noreset"):
    Reset = False
  if (sys.argv[i+1] == "2U24"):
    SystemType = "HA202E-PH"
  if (sys.argv[i+1] == "1U10"):
    SystemType = "SB122A-PH"
  if (sys.argv[i+1] == "1U8"):
    SystemType = "SB122-PH"
  if (sys.argv[i+1] == "help"):
    Help = True


if (Help == True):
  print "validate_pci.py - Optional input parameters:"
  print "all:        print all info irrespective of errors or not"
  print "silent:     do not print PCIe errors"
  print "noreset:    do not reset PCIe errors detected"
  print "2U24:       force detection as 2U24"
  print "1U10:       force detection as 1U10"
  sys.exit(1)


# misc PCI reg offsets.
PCIeCapOff="00"
PCIeCapSlotOff="14"
PCIeDevStatusOff="0A"
PCIeLinkCapOff="0C"
PCIeLinkStaOff="12"

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


##########################################
def ReadLinkStatusRegister (DeviceNo):

  # Device Status register
  LinkCommand = "setpci -s " + DeviceNo + " CAP_EXP+" + PCIeLinkStaOff + ".w"
  try:
    RegValue = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  except ValueError:
    RegValue = 0xffff
  return RegValue
##########################################

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


# first, detect the system this is running on, use ipmitool fru.  Simplify the output a bit.  Also option to override.

if (SystemType == ""):  # no override
  IPMICommand = "ipmitool fru | grep -m 1 'Product Name'"
  SystemType = str(subprocess.Popen(IPMICommand,shell=True,stdout=subprocess.PIPE).stdout.read().replace(" Product Name          : ", "").replace("\n", ""))

# The device map lists the expected hw configuration
# type is "SSD", "MLNX" (Mellanox Add-In-Card) or "SW".  SSD will detect for interposer.
# connection is "dir" or port number in switch attached to upstream.

if (SystemType == "HA202E-PH"):
  #              Name       CPU Root  Port  Type    Conn.   Speed   Width
  DeviceMap = [ ["PCISW-0", "0000:00:02.0", "SW",   "dir",  3,      16],
                ["PCISW-1", "0000:80:03.0", "SW",   "dir",  3,      16],
                ["MLNX-0 ", "0000:00:03.0", "AIC",  "dir",  3,      16],
                ["MLNX-1 ", "0000:80:02.0", "AIC",  "dir",  3,      16],
                ["Slot 01", "0000:00:02.0", "SSD",  "0C",   3,      2],   
                ["Slot 02", "0000:00:02.0", "SSD",  "0D",   3,      2],
                ["Slot 03", "0000:00:02.0", "SSD",  "0E",   3,      2],
                ["Slot 04", "0000:00:02.0", "SSD",  "0F",   3,      2],
                ["Slot 05", "0000:00:02.0", "SSD",  "04",   3,      2],
                ["Slot 06", "0000:00:02.0", "SSD",  "05",   3,      2],
                ["Slot 07", "0000:00:02.0", "SSD",  "06",   3,      2],
                ["Slot 08", "0000:00:02.0", "SSD",  "07",   3,      2],
                ["Slot 09", "0000:00:02.0", "SSD",  "00",   3,      2],
                ["Slot 10", "0000:00:02.0", "SSD",  "01",   3,      2],
                ["Slot 11", "0000:00:02.0", "SSD",  "02",   3,      2],
                ["Slot 12", "0000:00:02.0", "SSD",  "03",   3,      2],
                ["Slot 13", "0000:80:03.0", "SSD",  "04",   3,      2],
                ["Slot 14", "0000:80:03.0", "SSD",  "05",   3,      2],
                ["Slot 15", "0000:80:03.0", "SSD",  "06",   3,      2],
                ["Slot 16", "0000:80:03.0", "SSD",  "07",   3,      2],
                ["Slot 17", "0000:80:03.0", "SSD",  "00",   3,      2],
                ["Slot 18", "0000:80:03.0", "SSD",  "01",   3,      2],
                ["Slot 19", "0000:80:03.0", "SSD",  "02",   3,      2],
                ["Slot 20", "0000:80:03.0", "SSD",  "03",   3,      2],
                ["Slot 21", "0000:80:03.0", "SSD",  "08",   3,      2],
                ["Slot 22", "0000:80:03.0", "SSD",  "09",   3,      2],
                ["Slot 23", "0000:80:03.0", "SSD",  "0A",   3,      2],
                ["Slot 24", "0000:80:03.0", "SSD",  "0B",   3,      2] ]

elif ( (SystemType == "SB122A-PH") or (SystemType == "OB122E-PH") ):
  #              Name       CPU Root  Port  Type    Conn.   Speed   Width
  DeviceMap = [ ["MLNX-0 ", "0000:00:02.2", "AIC",  "dir",  3,      8],
                ["MLNX-1 ", "0000:80:02.0", "AIC",  "dir",  3,      16],
                ["Slot 01", "0000:80:03.0", "SSD",  "dir",  3,      4],
                ["Slot 02", "0000:80:03.1", "SSD",  "dir",  3,      4],
                ["Slot 03", "0000:80:03.2", "SSD",  "dir",  3,      4],
                ["Slot 04", "0000:80:03.3", "SSD",  "dir",  3,      4],
                ["Slot 05", "0000:00:02.1", "SSD",  "dir",  3,      4],
                ["Slot 06", "0000:00:02.0", "SSD",  "dir",  3,      4],
                ["Slot 07", "0000:00:03.0", "SSD",  "dir",  3,      4],
                ["Slot 08", "0000:00:03.1", "SSD",  "dir",  3,      4],
                ["Slot 09", "0000:00:03.2", "SSD",  "dir",  3,      4],
                ["Slot 10", "0000:00:03.3", "SSD",  "dir",  3,      4] ]

elif (SystemType == "SB122-PH"):
  #              Name       CPU Root  Port  Type    Conn.   Speed   Width
  DeviceMap = [ ["MLNX-0 ", "0000:80:02.2", "AIC",  "dir",  3,      8],
                ["MLNX-1 ", "0000:80:03.0", "AIC",  "dir",  3,      8],
                ["Slot 03", "0000:00:02.0", "SSD",  "dir",  3,      4],
                ["Slot 04", "0000:00:02.1", "SSD",  "dir",  3,      4],
                ["Slot 05", "0000:00:02.2", "SSD",  "dir",  3,      4],
                ["Slot 06", "0000:00:02.3", "SSD",  "dir",  3,      4],
                ["Slot 07", "0000:00:03.0", "SSD",  "dir",  3,      4],
                ["Slot 08", "0000:00:03.1", "SSD",  "dir",  3,      4],
                ["Slot 09", "0000:00:03.2", "SSD",  "dir",  3,      4],
                ["Slot 10", "0000:00:03.3", "SSD",  "dir",  3,      4] ]


else:
  print "validate_pci.py - Unsupported System Type.  Try 2U24, 1U10, 1U8", SystemType
  print ""
  sys.exit(1)

for i in range(len(DeviceMap)):
  DeviceNo = DeviceMap[i][1]

  UpstreamSwitch = False

  if (DeviceMap[i][3] != "dir"):    # if  not direct attached, need to traverse switch attached to CPU root port.
    PLXUpstreamDevice = DeviceMap[i][3]

    PLXBus = ReadSecondaryBus(DeviceNo)
    DeviceNo = "0000:" + str(PLXBus) + ":00.0"
    PLXBus = ReadSecondaryBus(DeviceNo)

    DeviceNo = "0000:" + str(PLXBus) + ":" + PLXUpstreamDevice + ".0"

    UpstreamSwitch = True

  PCIeLinkStatus = ReadLinkStatusRegister(DeviceNo)
  PCILinkSpeed = (PCIeLinkStatus & 0x0f)
  PCILinkWidth = ((PCIeLinkStatus >> 4) & 0x3f)

  # check is there an attached device, if so, look at that.

  AttachedDeviceBus = ReadSecondaryBus(DeviceNo)
  AttachedDeviceNo = "0000:" + str(AttachedDeviceBus) + ":00.0"

  DevicePath = "/sys/bus/pci/devices/" + AttachedDeviceNo

  if(os.path.exists(DevicePath) == True):
    VendorIDAddr = DevicePath + "/vendor"
    VendorID = open(VendorIDAddr,'r').read().rstrip('\n')

    DeviceIDAddr = DevicePath + "/device"
    DeviceID = open(DeviceIDAddr,'r').read().rstrip('\n')

    AttachedDevicePCIeLinkStatus = ReadLinkStatusRegister(AttachedDeviceNo)
    AttachedDevicePCILinkSpeed = (AttachedDevicePCIeLinkStatus & 0x0f)
    AttachedDevicePCILinkWidth = ((AttachedDevicePCIeLinkStatus >> 4) & 0x3f)
    AttachedDeviceValid = True

  else:
    VendorID = "None"
    DeviceID = "None"
    AttachedDeviceValid = False

  DownstreamSwitch = False
  DownstreamInterposer = False
  ActiveInterposer = False

  if (VendorID == '0x10b5'):
    if (DeviceID == '0x8713'):  # interposer
      DownstreamInterposer = True
    elif (DeviceID == '0x9765'):
      DownstreamSwitch = True



  if( (Silent == False) and \
      ((Quiet == False) or (PCILinkSpeed != DeviceMap[i][4]) or (PCILinkWidth != DeviceMap[i][5]) or (PCIeLinkStatus == 0xffff))):
    if (PCIeLinkStatus == 0xffff):
      print DeviceMap[i][0], DeviceNo, "Error Reading"
    elif ( (PCILinkSpeed == 0) or (PCILinkWidth == 0) ):
      print DeviceMap[i][0], DeviceNo, "Link Down"
    else:
      print DeviceMap[i][0], DeviceNo, "Speed:", PCILinkSpeed, "Width:", "{0:2d}".format(PCILinkWidth), "Vendor:", VendorID, "Device:", DeviceID

  if( (PCIeLinkStatus == 0xffff) or (PCILinkSpeed == 0) or (PCILinkWidth == 0) ):
    continue

  # if an atteched device is present, it must have the same speed.  Issues have been seen with devices with different reported speed to the
  # upstream port.  This is typically due to significant number of link recoveries, and reading the device info causing more recovery issues.
  if( (Silent == False) and (AttachedDeviceValid == True) and \
      ((Quiet == False) or (AttachedDevicePCILinkSpeed != DeviceMap[i][4]) or (AttachedDevicePCILinkWidth != DeviceMap[i][5]) or (AttachedDevicePCIeLinkStatus == 0xffff)) ):
    if (AttachedDevicePCIeLinkStatus == 0xffff):
      print DeviceMap[i][0], AttachedDeviceNo, "Error Reading"
    elif ( (PCILinkSpeed == 0) or (PCILinkWidth == 0) ):    # intentionally checking the link status of upstream device here, not a mistake.
      print DeviceMap[i][0], AttachedDeviceNo, "Link Down"
    else:
      print DeviceMap[i][0], AttachedDeviceNo, "Speed:", AttachedDevicePCILinkSpeed, "Width:", "{0:2d}".format(AttachedDevicePCILinkWidth), "Vendor:", VendorID, "Device:", DeviceID


  # Look for any PCIe errors reported.  First do the upstream, then downstream port.  If interposers attached, also check them.

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

  if(UpstreamSwitch == True):

    PortNo = (int(PLXUpstreamDevice[0],base=16) << 4) | int(PLXUpstreamDevice[1],base=16)

    PLXStationPortNo = PortNo & 0x0C    # 4 ports per station, so mask out lower 2 bits.
    PLXStationDevice = "{:02x}".format(PLXStationPortNo)
    PLXStationDeviceNo = "0000:" + str(PLXBus) + ":" + PLXStationDevice + ".0"

    PortReceiverErrorCount = ReadPLXPortReceiverErrorCount(PLXStationDeviceNo, int(PortNo))
    if( (Reset == True) and (PortReceiverErrorCount != 0) ):
      ClearPLXPortReceiverErrorCount(PLXStationDeviceNo, int(PortNo))

    BadTLPCount = ReadPLXBadTLPCount(DeviceNo)
    if( (Reset == True) and (BadTLPCount != 0) ):
      ClearPLXBadTLPCount(DeviceNo)

    BadDLLPCount = ReadPLXBadDLLPCount(DeviceNo)
    if( (Reset == True) and (BadDLLPCount != 0) ):
      ClearPLXBadDLLPCount(DeviceNo)

    RecoveryCount = ReadPLXRecoveryCount(PLXStationDeviceNo, int(PortNo))
    if( (Reset == True) and (RecoveryCount != 0) ):
      ClearPLXRecoveryCount(PLXStationDeviceNo, int(PortNo))

    FramingErrorStatus = ReadPLXFramingErrorRegister(DeviceNo)
    if( (Reset == True) and (FramingErrorStatus != 0) ):
      ClearPLXFramingErrorRegister(DeviceNo, FramingErrorStatus)

    if( (Silent == False) and \
        ((PCIeDeviceStatus != 0) or (BadTLPCount > 0) or (BadDLLPCount > 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or \
         (PortReceiverErrorCount != 0) or (RecoveryCount != 0) or (Quiet == False)) ):
      print DeviceMap[i][0], "Upstream Dev Sts:", "{0:04x}".format(PCIeDeviceStatus), \
            "AER UNC:", "{0:08x}".format(AERUNCStatus), "AER COR:", "{0:04x}".format(AERCORStatus), \
            "Bad TLP:", "{0:08x}".format(BadTLPCount), "Bad DLLP:", "{0:08x}".format(BadDLLPCount), \
            "PRT ERR:", "{0:02x}".format(PortReceiverErrorCount), \
            "REC:", "{0:04x}".format(RecoveryCount), \
            "FRM:", "{0:08x}".format(FramingErrorStatus)

  else: #upstream port is directly connected to CPU
    if( (Silent == False) and ((PCIeDeviceStatus != 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (Quiet == False)) ):
        print DeviceMap[i][0], "Upstream Dev Sts:", "{0:04x}".format(PCIeDeviceStatus), \
            "AER UNC:", "{0:08x}".format(AERUNCStatus), "AER COR:", "{0:04x}".format(AERCORStatus)

  # look at the attached (downstream) device.

  PCIeDeviceStatus = ReadDeviceStatusRegister(AttachedDeviceNo)
  PCIeDeviceStatus = (PCIeDeviceStatus & 0x0f)    # only care about bits 0..3
  if( (Reset == True) and (PCIeDeviceStatus != 0) ):
    ClearDeviceStatusRegister(AttachedDeviceNo, PCIeDeviceStatus)

  AERUNCStatus = ReadAERUNCRegister(AttachedDeviceNo)
  if( (Reset == True) and (AERUNCStatus != 0) ):
    ClearAERUNCRegister(AttachedDeviceNo, AERUNCStatus)

  AERCORStatus = ReadAERCORRegister(AttachedDeviceNo)
  if( (Reset == True) and (AERCORStatus != 0) ):
    ClearAERCORRegister(AttachedDeviceNo, AERCORStatus)


  if( (DownstreamSwitch == True) or (DownstreamInterposer == True) ): # There is a switch or interposer connected, get the detailed PLX error counters.

    BadTLPCount = ReadPLXBadTLPCount(AttachedDeviceNo)
    if( (Reset == True) and (BadTLPCount != 0) ):
      ClearPLXBadTLPCount(AttachedDeviceNo)

    BadDLLPCount = ReadPLXBadDLLPCount(AttachedDeviceNo)
    if( (Reset == True) and (BadDLLPCount != 0) ):
      ClearPLXBadDLLPCount(AttachedDeviceNo)

    FramingErrorStatus = ReadPLXFramingErrorRegister(AttachedDeviceNo)
    if( (Reset == True) and (FramingErrorStatus != 0) ):
      ClearPLXFramingErrorRegister(AttachedDeviceNo, FramingErrorStatus)

    if (DownstreamSwitch == True):
      DeviceType = "Switch  "

      RecoveryCount = ReadPLXRecoveryCount(AttachedDeviceNo, 0)
      if( (Reset == True) and (RecoveryCount != 0) ):
        ClearPLXRecoveryCount(AttachedDeviceNo, 0)

    elif (DownstreamInterposer == True):
      # check whether this is an active or passive interposer path.
      PLXBus = ReadSecondaryBus(AttachedDeviceNo)
      if (PLXBus == "00"):
        DeviceType = "Inv Intp"     # something is wrong in enumeration, bus should never be 0.  So skip it.
        ActiveInterposer = False
      else:
        DeviceNo = "0000:" + str(PLXBus) + ":02.0"    # device at device 2 on secondary bus indicates it is switched.
        DevicePath = "/sys/bus/pci/devices/" + DeviceNo
        if(os.path.exists(DevicePath) == True):
          DeviceType = "Act Intp"
          ActiveInterposer = True
        else:
          DeviceType = "Pas Intp"
          ActiveInterposer = False
    else:
      DeviceType = "Unknown "

    if (DownstreamSwitch == True): 
      if( (Silent == False) and ((PCIeDeviceStatus != 0) or (BadTLPCount > 0) or (BadDLLPCount > 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (Quiet == False) or (RecoveryCount != 0)) ):
        print DeviceMap[i][0], DeviceType, "Dev Sts:", "{0:04x}".format(PCIeDeviceStatus), \
              "AER UNC:", "{0:08x}".format(AERUNCStatus), "AER COR:", "{0:04x}".format(AERCORStatus), \
              "Bad TLP:", "{0:08x}".format(BadTLPCount), "Bad DLLP:", "{0:08x}".format(BadDLLPCount), \
              "REC:", "{0:04x}".format(RecoveryCount), \
              "FRM:", "{0:08x}".format(FramingErrorStatus)

    else:
      if( (Silent == False) and ((PCIeDeviceStatus != 0) or (BadTLPCount > 0) or (BadDLLPCount > 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (Quiet == False)) ):
        print DeviceMap[i][0], DeviceType, "Dev Sts:", "{0:04x}".format(PCIeDeviceStatus), \
              "AER UNC:", "{0:08x}".format(AERUNCStatus), "AER COR:", "{0:04x}".format(AERCORStatus), \
              "Bad TLP:", "{0:08x}".format(BadTLPCount), "Bad DLLP:", "{0:08x}".format(BadDLLPCount), \
              "FRM:", "{0:08x}".format(FramingErrorStatus)

    # See if the interposer is switched, and if there is a device connected to it.
    if( (DownstreamInterposer == True) and (ActiveInterposer == True) ):

      AttachedDeviceBus = ReadSecondaryBus(DeviceNo)
      AttachedDeviceNo = "0000:" + str(AttachedDeviceBus) + ":00.0"

      DevicePath = "/sys/bus/pci/devices/" + AttachedDeviceNo

      if(os.path.exists(DevicePath) == True):
        VendorIDAddr = DevicePath + "/vendor"
        VendorID = open(VendorIDAddr,'r').read().rstrip('\n')

        DeviceIDAddr = DevicePath + "/device"
        DeviceID = open(DeviceIDAddr,'r').read().rstrip('\n')
      else:
        VendorID = "None"
        DeviceID = "None"

      PCIeLinkStatus = ReadLinkStatusRegister(DeviceNo)
      PCILinkSpeed = (PCIeLinkStatus & 0x0f)
      PCILinkWidth = ((PCIeLinkStatus >> 4) & 0x3f)

      # Interposer connection to SSD should be x4, gen3.  Hard-coded here.
      if( (Quiet == False) or (PCILinkSpeed != 3) or (PCILinkWidth != 4) or (PCIeLinkStatus == 0xffff) ):
        if (PCIeLinkStatus == 0xffff):
          print DeviceMap[i][0], DeviceNo, "Error Reading Interposer Downstream"
          continue
        elif ( (PCILinkSpeed == 0) or (PCILinkWidth == 0) ):
          print DeviceMap[i][0], DeviceNo, "Link Down Interposer Downstream"
          continue
        else:
          print DeviceMap[i][0], DeviceNo, "Interposer Downstream Speed:", PCILinkSpeed, "Width:", "{0:2d}".format(PCILinkWidth), "Vendor:", VendorID, "Device:", DeviceID


      # Look for any errors on interposer downstream port
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

      BadTLPCount = ReadPLXBadTLPCount(DeviceNo)
      if( (Reset == True) and (BadTLPCount != 0) ):
        ClearPLXBadTLPCount(DeviceNo)

      BadDLLPCount = ReadPLXBadDLLPCount(DeviceNo)
      if( (Reset == True) and (BadDLLPCount != 0) ):
        ClearPLXBadDLLPCount(DeviceNo)

      FramingErrorStatus = ReadPLXFramingErrorRegister(DeviceNo)
      if( (Reset == True) and (FramingErrorStatus != 0) ):
        ClearPLXFramingErrorRegister(DeviceNo, FramingErrorStatus)

      if( (Silent == False) and ((PCIeDeviceStatus != 0) or (BadTLPCount > 0) or (BadDLLPCount > 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (Quiet == False)) ):
        print DeviceMap[i][0], "Intp Dwn Dev Sts:", "{0:04x}".format(PCIeDeviceStatus), \
              "AER UNC:", "{0:08x}".format(AERUNCStatus), "AER COR:", "{0:04x}".format(AERCORStatus), \
              "Bad TLP:", "{0:08x}".format(BadTLPCount), "Bad DLLP:", "{0:08x}".format(BadDLLPCount), \
              "FRM:", "{0:08x}".format(FramingErrorStatus)

      # Finally, look at the attached (downstream) device.

      PCIeDeviceStatus = ReadDeviceStatusRegister(AttachedDeviceNo)
      PCIeDeviceStatus = (PCIeDeviceStatus & 0x0f)    # only care about bits 0..3
      if( (Reset == True) and (PCIeDeviceStatus != 0) ):
        ClearDeviceStatusRegister(AttachedDeviceNo, PCIeDeviceStatus)

      AERUNCStatus = ReadAERUNCRegister(AttachedDeviceNo)
      if( (Reset == True) and (AERUNCStatus != 0) ):
        ClearAERUNCRegister(AttachedDeviceNo, AERUNCStatus)

      AERCORStatus = ReadAERCORRegister(AttachedDeviceNo)
      if( (Reset == True) and (AERCORStatus != 0) ):
        ClearAERCORRegister(AttachedDeviceNo, AERCORStatus)

      if( (Silent == False) and ((PCIeDeviceStatus != 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (Quiet == False)) ):
          print DeviceMap[i][0],"Intp SSD Dev Sts:", "{0:04x}".format(PCIeDeviceStatus), \
              "AER UNC:", "{0:08x}".format(AERUNCStatus), "AER COR:", "{0:04x}".format(AERCORStatus)

  else: #downstream port is regular endpoint
    if( (Silent == False) and ((PCIeDeviceStatus != 0) or (AERUNCStatus != 0) or (AERCORStatus != 0) or (Quiet == False)) ):

      if (DeviceMap[i][2] == "SSD"):
          DeviceType = "SSD     "
      elif (DeviceMap[i][2] == "AIC"):
          DeviceType = "PCI Card"
      else:
        DeviceType = "Unknown "


      print DeviceMap[i][0],DeviceType, "Dev Sts:", "{0:04x}".format(PCIeDeviceStatus), \
            "AER UNC:", "{0:08x}".format(AERUNCStatus), "AER COR:", "{0:04x}".format(AERCORStatus)






