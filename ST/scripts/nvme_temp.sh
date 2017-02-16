#!/bin/bash
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : nvme_temp.sh
# Author : Stuart Campbell
# Date   : 2016-06-20
# Version: 0.1
#
#--------------------------------------

TIMESTAMP=`date +"%Y-%m-%d %H:%M.%S" | tr -d '\n'`

echo NVMe Temperature $TIMESTAMP

if [ "$1" == "all" ];
  then
    echo nvme list
    nvme list
    #echo Drive Tool Sensors
    #isdct show -sensor -intelssd
    echo
    echo BMC Sensors
    ipmitool sdr |grep SSD
    echo
  fi

for i in {1..24}
do
  NVMeDevice=$(./slot_to_nvme.py ${i})

  if [ -z $NVMeDevice ];
  then
    continue
  fi
  devicepath=/dev/$NVMeDevice
  if [ -e $devicepath ];
  then
    Temperature=$(nvme smart-log $devicepath | grep temperature)
    printf "Slot: %02d Device: %-10s %s\n" "$i" "$NVMeDevice" "$Temperature"
  fi
done


