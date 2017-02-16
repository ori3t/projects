#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : get_power_info.py
# Author : Stuart Campbell stuart@e8storage.com
# Date   : 2016-08-30
# Version: 0.2 2016-10-04
# Changelog:
#     0.2: Removed PSU input current printout, this is invalid.
#          Decoded PSU status as on or off
# 
# Optional input parameters:
#                   node name or IP address:  use this instead of local access.
# 
#--------------------------------------

import sys
import subprocess
import time
import os


##########################################
def Convert16bitToFloat(HexValue):

# format is 16 bits, bits 0..10 are signed mantissa, 11.15 are signed exponent.

  Mantissa = HexValue & 0x3ff
  if((HexValue & 0x0400) != 0):
    Mantissa = Mantissa - 0x0400

  Exponent = (HexValue >> 11) & 0x0f
  if((HexValue & 0x8000) != 0):
    Exponent = Exponent - 0x0010

  FloatValue = Mantissa * pow(2,Exponent)

#  print "Mantissa:", Mantissa, "Exponent:", Exponent, "Value:", FloatValue

  return FloatValue
##########################################

##########################################
def Extract16bitFromRaw(Buffer, Offset):

  ReturnValue = (int(Buffer[Offset + 2],base=16) << 12) | \
                (int(Buffer[Offset + 3],base=16) << 8) | \
                (int(Buffer[Offset],base=16) << 4) | \
                 int(Buffer[Offset + 1],base=16)

  return ReturnValue
##########################################

# First create the command.
IPMICommand = "ipmitool raw 0x3c 0xbb"

if (len(sys.argv) > 1):
  IPMICommand = IPMICommand + " -U admin -P admin -H " + sys.argv[1]

RawOutput = str(subprocess.Popen(IPMICommand,shell=True,stdout=subprocess.PIPE).stdout.read().replace(" ", "").replace("\n", ""))

# The ipmi command output is a string of bytes separated by spaces, on 2 lines.  Needs some formatting to get it 
# easier to work with, so strip the spaces and newline characters.  End result is a packed set of ASCII bytes.
# Format is as follows:
# Byte No.  Value
# 0         PSU 1 status, 0x00 AC off, 0x01 AC on 
# 1         PSU 2 status, 0x00 AC off, 0x01 AC on
# 2         PSU 1 PIN low
# 3         PSU 1 PIN high
# 4         PSU 1 POUT low
# 5         PSU 1 POUT high
# 6         PSU 1 VIN low
# 7         PSU 1 VIN high
# 8         PSU 1 VOUT low
# 9         PSU 1 VOUT high
# 10        PSU 1 IIN low
# 11        PSU 1 IIN high
# 12        PSU 1 IOUT low
# 13        PSU 1 IOUT high
# 14        PSU 2 PIN low
# 15        PSU 2 PIN high
# 16        PSU 2 POUT low
# 17        PSU 2 POUT high
# 18        PSU 2 VIN low
# 19        PSU 2 VIN high
# 20        PSU 2 VOUT low
# 21        PSU 2 VOUT high
# 22        PSU 2 IIN low
# 23        PSU 2 IIN high
# 24        PSU 2 IOUT low
# 25        PSU 2 IOUT high

# Sample output:
# 01018c103d1857f3c2e0b4b429008a103d1851f3c2e074f42900
# PSU1 0x1
# PSU1 Power In   : 560 W
# PSU1 Power Out  : 488 W
# PSU1 Voltage In : 213.75 V
# PSU1 Voltage Out: 12.125 V
# PSU1 Current In : -0.82421875 A
# PSU1 Current Out: 41 A
# PSU2 0x1
# PSU2 Power In   : 552 W
# PSU2 Power Out  : 488 W
# PSU2 Voltage In : 212.25 V
# PSU2 Voltage Out: 12.125 V
# PSU2 Current In : -227.0 A
# PSU2 Current Out: 41 A
# Total Power In  : 1112 W
# Total Power Out : 976 W

print RawOutput

PSU1_Status = (int(RawOutput[0],base=16) << 4) | int(RawOutput[1],base=16)
PSU2_Status = (int(RawOutput[2],base=16) << 4) | int(RawOutput[3],base=16)


PSU1_Pin = Extract16bitFromRaw(RawOutput, 4)
PSU1_Pout = Extract16bitFromRaw(RawOutput, 8)
PSU1_Vin = Extract16bitFromRaw(RawOutput, 12)
PSU1_Vout = Extract16bitFromRaw(RawOutput, 16)
PSU1_Iin = Extract16bitFromRaw(RawOutput, 20)
PSU1_Iout = Extract16bitFromRaw(RawOutput, 24)

PSU2_Pin = Extract16bitFromRaw(RawOutput, 28)
PSU2_Pout = Extract16bitFromRaw(RawOutput, 32)
PSU2_Vin = Extract16bitFromRaw(RawOutput, 36)
PSU2_Vout = Extract16bitFromRaw(RawOutput, 40)
PSU2_Iin = Extract16bitFromRaw(RawOutput, 44)
PSU2_Iout = Extract16bitFromRaw(RawOutput, 48)


if(PSU1_Status == 0x00):
  print "PSU1 Off"
else:
  print "PSU1 On"

print "PSU1 Power In   :", Convert16bitToFloat(PSU1_Pin), "W"
print "PSU1 Power Out  :", Convert16bitToFloat(PSU1_Pout), "W"
print "PSU1 Voltage In :", Convert16bitToFloat(PSU1_Vin), "V"
print "PSU1 Voltage Out:", Convert16bitToFloat(PSU1_Vout), "V"
print "PSU1 Current Out:", Convert16bitToFloat(PSU1_Iout), "A"

if(PSU2_Status == 0x00):
  print "PSU2 Off"
else:
  print "PSU2 On"

print "PSU2 Power In   :", Convert16bitToFloat(PSU2_Pin), "W"
print "PSU2 Power Out  :", Convert16bitToFloat(PSU2_Pout), "W"
print "PSU2 Voltage In :", Convert16bitToFloat(PSU2_Vin), "V"
print "PSU2 Voltage Out:", Convert16bitToFloat(PSU2_Vout), "V"
print "PSU2 Current Out:", Convert16bitToFloat(PSU2_Iout), "A"

print "Total Power In  :", (Convert16bitToFloat(PSU1_Pin) + Convert16bitToFloat(PSU2_Pin)), "W"
print "Total Power Out :", (Convert16bitToFloat(PSU1_Pout)+ Convert16bitToFloat(PSU2_Pout)), "W"

