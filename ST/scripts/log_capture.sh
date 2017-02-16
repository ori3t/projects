#!/bin/bash
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : log_capture.sh
# Author : Stuart Campbell
# Date   : 2016-06-20
# Version: 0.2 2016-06-21
#
# Changelog:
#     0.2: Added more system information.
#     0.1: Original file.
#
#--------------------------------------

TIMESTAMP=`date +"%Y%m%d-%H%M%S" | tr -d '\n'`
LOGFILE="logfile.$TIMESTAMP.log"
SCRIPTPATH=/tools/scripts

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo lspci info >> $LOGFILE
echo '****************************************************' >> $LOGFILE
lspci -vvv >> $LOGFILE

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo PCIe error info >> $LOGFILE
echo '****************************************************' >> $LOGFILE
$SCRIPTPATH/get_pcie_error_counters.py >> $LOGFILE

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo BMC sensors >> $LOGFILE
echo '****************************************************' >> $LOGFILE
ipmitool sensor >> $LOGFILE

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo BMC SEL Log >> $LOGFILE
echo '****************************************************' >> $LOGFILE
ipmitool sel list >> $LOGFILE

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo System Information >> $LOGFILE
echo '****************************************************' >> $LOGFILE
ipmitool mc info >> $LOGFILE
ipmitool fru >> $LOGFILE

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo BIOS Information >> $LOGFILE
echo '****************************************************' >> $LOGFILE
dmidecode -t bios -q >> $LOGFILE

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo CPU Information >> $LOGFILE
echo '****************************************************' >> $LOGFILE
dmidecode -t processor >> $LOGFILE

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo NVMe Driver Info >> $LOGFILE
echo '****************************************************' >> $LOGFILE
modinfo nvme >> $LOGFILE

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo NVMe Device List >> $LOGFILE
echo '****************************************************' >> $LOGFILE
nvme list >> $LOGFILE

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo Slot to NVMe Device Mapping >> $LOGFILE
echo '****************************************************' >> $LOGFILE
$SCRIPTPATH/slot_to_nvme.py all >> $LOGFILE

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo NVMe to Slot Device Mapping >> $LOGFILE
echo '****************************************************' >> $LOGFILE
$SCRIPTPATH/nvme_to_slot.py all >> $LOGFILE

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo NVMe SMART Logs >> $LOGFILE
echo '****************************************************' >> $LOGFILE
for i in {1..24}
do
  NVMeDevice=$($SCRIPTPATH/slot_to_nvme.py ${i})

  if [ -z $NVMeDevice ];
  then
    continue
  fi
  devicepath=/dev/$NVMeDevice
  if [ -e $devicepath ];
  then
    echo Slot No:$i NVMe Device:$NVMeDevice >> $LOGFILE
    nvme smart-log $devicepath >> $LOGFILE
    echo >> $LOGFILE
  fi
done

echo >> $LOGFILE
echo >> $LOGFILE
echo '****************************************************' >> $LOGFILE
echo NVMe Temperature SMART >> $LOGFILE
echo '****************************************************' >> $LOGFILE
for i in {1..24}
do
  NVMeDevice=$($SCRIPTPATH/slot_to_nvme.py ${i})

  if [ -z $NVMeDevice ];
  then
    continue
  fi
  devicepath=/dev/$NVMeDevice
  if [ -e $devicepath ];
  then
    echo Slot No:$i NVMe Device:$NVMeDevice >> $LOGFILE
    nvme smart-log $devicepath | grep temperature >> $LOGFILE
    echo >> $LOGFILE
  fi
done


