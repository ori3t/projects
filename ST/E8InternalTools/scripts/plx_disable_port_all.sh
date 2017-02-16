#!/bin/bash
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : plx_disable_port_all.sh
# Author : Stuart Campbell
# Date   : 2016-06-20
# Version: 0.1
#--------------------------------------

# Disables all ports by writing to the station port control registers.
# 4 ports per station.  Note different stations for different PLX chips.
# PLX EEPROM needs to have entry to enable PCI config access to extended address space.
setpci -s 03:00 208.l=0000000f
setpci -s 03:04 208.l=0000000f
setpci -s 03:0c 208.l=0000000f
setpci -s 87:00 208.l=0000000f
setpci -s 87:04 208.l=0000000f
setpci -s 87:08 208.l=0000000f

