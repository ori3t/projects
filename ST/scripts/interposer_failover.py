#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : interposer_failover.py
# Author : Stuart Campbell stuart@e8storage.com
# Date   : 2016-07-05
# Version: 0.2 2016-09-14
# Version: 0.3 2016-09-29
# Version: 0.4 2016-10-17
# Changelog:
#     0.4: Modified order of resetting of SSD, remove from partner VS first.
#          Now bring down upstream link on interposer on partner during failover, to
#          force partner to re-enumerate and remove device after failover.
#     0.3: Added for resetting of SSD before switching of VS, to cancel I/O in progress.
#     0.2: Added for default/even/odd selection, fixed bugs, stabilised failover.
#     0.1: Original file.
#
# Optional input parameters:
#                   <slot number>   switch selected slot number
#                   all:            switch all detected interposers.
#                   even:           switch all even number slots
#                   odd:            switch all odd number slots
#                   default:        switch the default slots for this node (even for C0, odd for C1)
#                   force:          optionally force the switchover even if already switched.
#
#--------------------------------------

import sys
import subprocess
import time
import os

if (len(sys.argv) < 2):
  print "Invalid Arguments - use python interposer_failover.py <slot number>(1..24)|all|even|odd|default opt:force"
  print ""
  sys.exit(1)

SwitchAll = False
SwitchEven = False
SwitchOdd = False
SwitchDefault = False
Force = False

UserInput=sys.argv[1]
RequestedSlot=0

if (UserInput == "all"):
  SwitchAll = True
elif (UserInput == "even"):
  SwitchEven = True
elif (UserInput == "odd"):
  SwitchOdd = True
elif (UserInput == "default"):
    SwitchDefault = True
elif UserInput.isdigit():
  if ( (int(UserInput) >= 1) and (int(UserInput) <= 24) ):
    RequestedSlot = int(UserInput)
  else:
    print "Invalid Arguments - use python interposer_failover.py <slot number>(1..24)|all|even|odd|default"
    print ""
    sys.exit(1)

if (len(sys.argv) > 2):
  if (sys.argv[2] == "force"):
    Force = True


# Detrrmine the node number, 0 or 1 using ipmi raw command.  Output of this is 00 for Node 0, 01 for Node 1.
IPMICommand = "ipmitool raw 0x3c 0xa5"
RawOutput = str(subprocess.Popen(IPMICommand,shell=True,stdout=subprocess.PIPE).stdout.read().replace(" ", "").replace("\n", ""))
NodeNumber = (int(RawOutput[0],base=16) << 4) | int(RawOutput[1],base=16)

# if switching default slots for the node, then determine what slot.
if(NodeNumber == 0x00):
  if(SwitchDefault == True):
    SwitchEven = True
else:
  if(SwitchDefault == True):
    SwitchOdd = True

PCIeLinkCapOff="0C"

CPU0_RC="0000:00:02.0"
CPU1_RC="0000:80:03.0"

PLXPortCTL=" 208"

# definitions for switching the ports, note different sequence for each node

NODE0_SWITCH_MGMT_CMD = " 354 00002120"
NODE0_REMOVE_VSx_CMD =  " 384 00000002"
NODE0_ADD_VSx_CMD =     " 380 00000005"
NODE0_PORT_BITMAP =     " 00000001"

NODE1_SWITCH_MGMT_CMD = " 354 00002021"
NODE1_REMOVE_VSx_CMD =  " 380 00000001"
NODE1_ADD_VSx_CMD =     " 384 00000006"
NODE1_PORT_BITMAP =     " 00000002"


##########################################
def ReadSecondaryBus (DeviceNo):

  LinkCommand = "setpci -s " + DeviceNo + " SECONDARY_BUS.b"
  try:
    RegValue = str(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().rstrip('\n'))
  except ValueError:
    RegValue = "ff"
  return RegValue
##########################################


# Each slot is hard-coded to specific ports.

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

  if(SwitchEven == True):
    if((SlotNo & 0x01) != 0):
      continue

  elif(SwitchOdd == True):
    if((SlotNo & 0x01) == 0):
      continue

  elif( (SwitchAll == False) and (RequestedSlot != SlotNo) ):
    continue

  DeviceNo = SlotToDeviceMap0[i][1]
  PLXBus = ReadSecondaryBus(DeviceNo)
  PLXUpstreamDeviceNo = "0000:" + str(PLXBus) + ":00.0"
  PLXBus = ReadSecondaryBus(PLXUpstreamDeviceNo)

  DeviceNo = "0000:" + str(PLXBus) + ":" + PLXDownstreamDevice + ".0"

  # check is there an attached device, if so, look at that.

  SSDBus = ReadSecondaryBus(DeviceNo)
  AttachedSSDDeviceNo = "0000:" + str(SSDBus) + ":00.0"

  DevicePath = "/sys/bus/pci/devices/" + AttachedSSDDeviceNo

  if(os.path.exists(DevicePath) != True):
    print "Skip Removed Device:", "{0:2d}".format(SlotNo), AttachedSSDDeviceNo
    continue

  VendorIDAddr = DevicePath + "/vendor"
  VendorID = open(VendorIDAddr,'r').read().rstrip('\n')

  DeviceIDAddr = DevicePath + "/device"
  DeviceID = open(DeviceIDAddr,'r').read().rstrip('\n')

  if ( (VendorID != '0x10b5') or (DeviceID != '0x8713') ):
    print "Skip Non-Interposer Device:", "{0:2d}".format(SlotNo), AttachedSSDDeviceNo
    continue

  # detect what port we are connected to, this is the port we then need to switch to.
  LinkCommand = "setpci -s " + AttachedSSDDeviceNo + " CAP_EXP+" + PCIeLinkCapOff + ".l"

  # Read current status
  try:
    LinkCommand = "./plxreg " + AttachedSSDDeviceNo + " 354"
    ManagementPortControl = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  except ValueError:
    print "ManagementPortControl ERR:", "{0:2d}".format(SlotNo), AttachedSSDDeviceNo
    continue

  try:
    LinkCommand = "./plxreg " + AttachedSSDDeviceNo + " 380"
    VS0PortVector = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  except ValueError:
    print "VS0PortVector ERR:", "{0:2d}".format(SlotNo), AttachedSSDDeviceNo
    continue

  try:
    LinkCommand = "./plxreg " + AttachedSSDDeviceNo + " 384"
    VS1PortVector = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  except ValueError:
    print "VS1PortVector ERR:", "{0:2d}".format(SlotNo), AttachedSSDDeviceNo
    continue


  #print "ManagementPortControl:", hex(ManagementPortControl), "VS0PortVector:", hex(VS0PortVector), "VS1PortVector:", hex(VS1PortVector)

  if(NodeNumber == 0x00):

    if ( (ManagementPortControl == 0x00002120) and (VS0PortVector == 0x00000005) and (VS1PortVector == 0x00000002) and (Force == False) ):
      print "Node 0 Skip Switch Interposer:", "{0:2d}".format(SlotNo), AttachedSSDDeviceNo
      continue

    print "Node 0 Switch Interposer:", "{0:2d}".format(SlotNo), AttachedSSDDeviceNo

    dmesg="echo \"Node 0 Switch Interposer Slot " + str(SlotNo) + "\"" + " > /dev/kmsg"
    subprocess.call(dmesg, shell=True)

    SwitchManagementPortCmd = NODE0_SWITCH_MGMT_CMD
    RemovePortCmd = NODE0_REMOVE_VSx_CMD
    AddPortCmd = NODE0_ADD_VSx_CMD
    ResetPartnerCmd = NODE1_PORT_BITMAP

  else:

    if ( (ManagementPortControl == 0x00002021) and (VS0PortVector == 0x00000001) and (VS1PortVector == 0x00000006) and (Force == False) ):
      print "Node 1 Skip Switch Interposer:", "{0:2d}".format(SlotNo), AttachedSSDDeviceNo
      continue

    print "Node 1 Switch Interposer:", "{0:2d}".format(SlotNo), AttachedSSDDeviceNo

    dmesg="echo \"Node 1 Switch Interposer Slot " + str(SlotNo) + "\"" + " > /dev/kmsg"
    subprocess.call(dmesg, shell=True)

    SwitchManagementPortCmd = NODE1_SWITCH_MGMT_CMD
    RemovePortCmd = NODE1_REMOVE_VSx_CMD
    AddPortCmd = NODE1_ADD_VSx_CMD
    ResetPartnerCmd = NODE0_PORT_BITMAP


  # Modify the switch management port to point to this port.
  LinkCommand = "./plxreg " + AttachedSSDDeviceNo + SwitchManagementPortCmd
  subprocess.call(LinkCommand, shell=True)


  # Remove the SSD from VS
  LinkCommand = "./plxreg " + AttachedSSDDeviceNo + RemovePortCmd
  subprocess.call(LinkCommand, shell=True)

  # bring the upstream link down on the partner.  Should cause the partner to un-enumerate it.
  # only required if it was previously switched to the partner.
  LinkCommand = "./plxreg " + AttachedSSDDeviceNo + PLXPortCTL + ResetPartnerCmd
  subprocess.call(LinkCommand, shell=True)

  # perform a secondary bus reset of the SSD.  This is register 0x3c at port 2, so port offset 0x203c

  try:
    LinkCommand = "./plxreg " + AttachedSSDDeviceNo + " 203C"
    BridgeControl = int(subprocess.Popen(LinkCommand,shell=True,stdout=subprocess.PIPE).stdout.read().rstrip('\n'),16)
  except ValueError:
    print "BridgeControl ERR:", "{0:2d}".format(SlotNo), AttachedSSDDeviceNo
    continue

  LinkCommand = "./plxreg " + AttachedSSDDeviceNo + " 203C " + hex(BridgeControl | 0x00400000)
  subprocess.call(LinkCommand, shell=True)

  LinkCommand = "./plxreg " + AttachedSSDDeviceNo + " 203C " + hex(BridgeControl & ~0x00400000)
  subprocess.call(LinkCommand, shell=True)

  # wait 1s for reset to take effect.

  time.sleep(1)

  # bring the upstream link back up on the partner.  Should cause the partner to un-enumerate it.
  # only required if it was previously switched to the partner.
  LinkCommand = "./plxreg " + AttachedSSDDeviceNo + PLXPortCTL + " 0x00000000"
  subprocess.call(LinkCommand, shell=True)

  # Add the SSD to VS
  LinkCommand = "./plxreg " + AttachedSSDDeviceNo + AddPortCmd
  subprocess.call(LinkCommand, shell=True)

  # To add a new device, we need to fully enumerate the switch.  Adding just a downstream port doesn't do this,
  # since it cannot add the required change to the subordinate bus number.  So disable/reenable the link

  dmesg="echo \"Disable Link Slot " + str(SlotNo) + "\"" + " > /dev/kmsg"
  subprocess.call(dmesg, shell=True)

  # first disable link.  Use PLX-specific register rather than port-disable, this is more effective
  # since it completely silences the link.  These are per-station registers, 4 ports in a station.

  PortNo = (int(PLXDownstreamDevice[0],base=16) << 4) | int(PLXDownstreamDevice[1],base=16) 
  PortNo = PortNo & 0x03    # 4 ports per station.
  if(PortNo == 0x00):
    PortBitmapStr = "00000001"
  elif(PortNo == 0x01):
    PortBitmapStr = "00000002"
  elif(PortNo == 0x02):
    PortBitmapStr = "00000004"
  elif(PortNo == 0x03):
    PortBitmapStr = "00000008"
  else:
    PortBitmapStr = "00000000"

  PLXStationDeviceNo = "0000:" + str(PLXBus) + ":" + PLXStationDevice + ".0"

  LinkCommand="setpci -s " + PLXStationDeviceNo + PLXPortCTL + ".l=" + PortBitmapStr
  subprocess.call(LinkCommand, shell=True)

  time.sleep(1)

  dmesg="echo \"Enable Link Slot " + str(SlotNo) + "\"" + " > /dev/kmsg"
  subprocess.call(dmesg, shell=True)

  # finally re-enable link.
  LinkCommand="setpci -s " + PLXStationDeviceNo + PLXPortCTL + ".l=00000000"
  subprocess.call(LinkCommand, shell=True)


