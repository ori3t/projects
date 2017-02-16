#!/usr/bin/python
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : get_interposer_status.py
# Author : Or Igelka or@e8storage.com
# Date   : 2016-12-22
#
# Optional input parameters:
#                   <slot number>   print selected slot number
#                   all:            print all slots
#--------------------------------------

import sys
import subprocess
import os

CPU0_PCI_ID = "0000:00:02.0"
CPU1_PCI_ID = "0000:80:03.0"

# Each slot is hard-coded to specific ports
slot_to_interposer_id = [
    "0C",
    "0D",
    "0E",
    "0F",
    "04",
    "05",
    "06",
    "07",
    "00",
    "01",
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "00",
    "01",
    "02",
    "03",
    "08",
    "09",
    "0A",
    "0B"
]

SOMETHING_IN_SLOT = 0x1000  # Presence 0 = present, 1 = not present
SOMETHING_IN_SLOT_IS_INTERPOSER  = 0x4000  # Interposer present 0 = no interposer, 1 = interposer present

LINK_STATUS_NOT_MANAGED_BY_CURRENT_NODE_1              = 0x00000000
LINK_STATUS_NOT_MANAGED_BY_CURRENT_NODE_2              = 0xFFFFFFFF
LINK_STATUS_NO_DISK_ATTACHED                           = 0x00010000
LINK_STATUS_DISK_ATTACHED_AND_SWITCHED_TO_CURRENT_NODE = 0xE0430000

def run_get_output(cmd):
    # print "Running: " + cmd
    return subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ).stdout.read()

def run_ipmitool(args):
    return int(run_get_output(
            "ipmitool raw 0x3c " + args
        ).replace(" ", "").replace("\n", ""), base=16)

def get_current_node_id():
    # Determine the ipmi node number - 0 or 1
    return run_ipmitool("0xa5")

def get_secondary_bus(pci_id):
    return run_get_output(
            "setpci -s " + pci_id + " SECONDARY_BUS.b"
        ).rstrip('\n')

def read_plx_register(plx_8713_interposer_downstream_pci_id, register_offset):
    plxreg = os.path.dirname(sys.argv[0]) + "/plxreg"
    return int(run_get_output(
        "{} {} {}".format(
            plxreg,
            plx_8713_interposer_downstream_pci_id,
            register_offset
        )).rstrip('\n'), base=16)

def get_switch_status(plx_8713_interposer_downstream_pci_id, slot_num):
    switch_status = dict()
    switch_status['node_id'] = get_current_node_id()
    switch_status['mgmt_port'] = read_plx_register(plx_8713_interposer_downstream_pci_id, "354")
    switch_status['vs0_port'] = read_plx_register(plx_8713_interposer_downstream_pci_id, "380")
    switch_status['vs1_port'] = read_plx_register(plx_8713_interposer_downstream_pci_id, "384")
    return switch_status

def print_switch_status(switch_status):
    print "Node number : " + hex(switch_status['node_id'])
    print "mgmt port   : " + hex(switch_status['mgmt_port'])
    print "VS0 port    : " + hex(switch_status['vs0_port'])
    print "VS1 port    : " + hex(switch_status['vs1_port'])

def is_switched_to_me(switch_status):
    if ((switch_status['node_id'] == 0x00) and
        (switch_status['mgmt_port'] == 0x00002120) and
        (switch_status['vs0_port'] == 0x00000005) and
        (switch_status['vs1_port'] == 0x00000002)
    ):
        return True

    if ((switch_status['node_id'] == 0x01) and
        (switch_status['mgmt_port'] == 0x00002021) and
        (switch_status['vs0_port'] == 0x00000001) and
        (switch_status['vs1_port'] == 0x00000006)
    ):
        return True

    return False

def get_interposer_pci_id(slot_num):
    cpu_pci_id = CPU0_PCI_ID if slot_num <= 12 else CPU1_PCI_ID
    plx_9765_switch_upstream_bus_id = get_secondary_bus(cpu_pci_id)
    plx_9765_switch_upstream_pci_id = compose_pci_id(
        plx_9765_switch_upstream_bus_id
    )
    plx_9765_switch_downstream_bus_id = get_secondary_bus(
        plx_9765_switch_upstream_pci_id
    )
    plx_8713_interposer_id = slot_to_interposer_id[slot_num - 1]
    plx_8713_interposer_pci_id = compose_pci_id(
        plx_9765_switch_downstream_bus_id,
        plx_8713_interposer_id
    )
    plx_8713_interposer_downstream_bus_id = get_secondary_bus(
        plx_8713_interposer_pci_id
    )
    plx_8713_interposer_downstream_pci_id = compose_pci_id(
        plx_8713_interposer_downstream_bus_id
    )
    return plx_8713_interposer_downstream_pci_id

def get_link_status(plx_8713_interposer_downstream_pci_id):
    return read_plx_register(plx_8713_interposer_downstream_pci_id, "2078")

def print_link_status(link_status, switch_status):
    if (link_status == LINK_STATUS_NOT_MANAGED_BY_CURRENT_NODE_1) or \
       (link_status == LINK_STATUS_NOT_MANAGED_BY_CURRENT_NODE_2):
        print_status("Interposer that's not managed by the current node")
        return
    elif (link_status == LINK_STATUS_NO_DISK_ATTACHED):
        print_status("Interposer without a disk")
        return
    elif (link_status == LINK_STATUS_DISK_ATTACHED_AND_SWITCHED_TO_CURRENT_NODE):
        if is_switched_to_me(switch_status):
            print_status("Interposer with disk switched to current node")
        else:
            print_status("Interposer with disk not fully switched to current node")
        return
    else:
        print_status("Interposer with disk not switched to current node")
        return

def compose_pci_id(bus_id, device_id="00"):
    return "0000:{}:{}.0".format(bus_id, device_id)

def print_status(status):
    print "Slot Status : " + status

def print_slot_status(slot_num):
    print "Slot Number : " + str(slot_num)

    slot_status = run_ipmitool("0xa7 " + hex(slot_num))
    if ((slot_status & SOMETHING_IN_SLOT) != 0):
        print_status("Nothing")
        return

    if ((slot_status & SOMETHING_IN_SLOT_IS_INTERPOSER) == 0):
        print_status("Direct disk")
        return

    plx_8713_interposer_downstream_pci_id = get_interposer_pci_id(slot_num)
    print "PCI ID      : " + plx_8713_interposer_downstream_pci_id

    device_path = "/sys/bus/pci/devices/" + plx_8713_interposer_downstream_pci_id
    if not os.path.exists(device_path):
        print "Skip Removed Device:", \
              "{0:2d}".format(slot_num), \
              plx_8713_interposer_downstream_pci_id
        return

    switch_status = get_switch_status(plx_8713_interposer_downstream_pci_id, slot_num)
    print_switch_status(switch_status)

    link_status = get_link_status(plx_8713_interposer_downstream_pci_id)
    print_link_status(link_status, switch_status)

def print_usage_and_exit():
    print "Invalid Arguments - use python get_interposer_status.py <slot number>(1..24)|all"
    print ""
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print_usage_and_exit()
    
    user_input=sys.argv[1]
    
    if user_input == "all":
        for i in xrange(1, 25):
            print
            print_slot_status(i)
    elif user_input.isdigit():
        if (1 <= int(user_input)) and (int(user_input) <= 24):
            requested_slot = int(user_input)
            print_slot_status(requested_slot)
        else:
            print_usage_and_exit()

if __name__ == '__main__':
    main()
