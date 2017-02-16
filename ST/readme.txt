# Copyright (c) 2014-2017, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Version: I2017-01-26


Overview:
This document describes the E8 tools used to test and validate the AIC 2U NVMe system.  


Dependencies:
The system should have the following tools/utilities installed:
ipmitool
python
libaio (for fio)


OS Version:
The tools are built for CentOS 7.2.


Release Format:
The tools are distributed as a compressed tar archive, use tar -xzvf to decompress
It may be necessary to change permissions on these tools to allow them to be run, if so
use "chmod +x".  e.g. "chmod -R +x /tools/fio", "chmod -R +x /tools/scripts", "chmod -R +x /tools/nvme"

Tool Location:
Uncompress the tools in the /tools directory, the tools will extract to the following directory format:
/tools/fio
/tools/fio/fio
/tools/fio/run_fio.sh
/tools/Intel
/tools/Intel/issdcm-2.3.1-4.x86_64.rpm
/tools/Intel/mlc
/tools/Intel/mlc/mlc
/tools/Intel/mlc/mlc_avx512
/tools/Intel/pcm
/tools/Intel/pcm/pcm.x
/tools/Intel/pcm/pcm-core.x
/tools/Intel/pcm/pcm-memory.x
/tools/Intel/pcm/pcm-msr.x
/tools/Intel/pcm/pcm-numa.x
/tools/Intel/pcm/pcm-pcie.x
/tools/Intel/pcm/pcm-power.x
/tools/Intel/pcm/pcm-sensor.x
/tools/Intel/pcm/pcm-tsx.x
/tools/nvme
/tools/nvme/nvme
/tools/nvme/nvme-cli-master.zip
/tools/PLX
/tools/PLX/Perfmon
/tools/PLX/plx_load.sh
/tools/PLX/plx_unload.sh
/tools/PLX/PlxCm
/tools/PLX/PlxSvc.ko
/tools/scripts
/tools/scripts/disable_slot_link.py
/tools/scripts/disable_slot_link_all.py
/tools/scripts/enable_slot_link.py
/tools/scripts/enable_slot_link_all.py
/tools/scripts/get_pcie_error_counters.py
/tools/scripts/get_power_info.py
/tools/scripts/get_slot_status.py
/tools/scripts/interposer_failover.py
/tools/scripts/nvme_to_slot.py
/tools/scripts/plxreg
/tools/scripts/plxregdump
/tools/scripts/poll_pcie_error_counters.py
/tools/scripts/set_pcie_presets.py
/tools/scripts/set_slot_speed.py
/tools/scripts/set_slot_speed_all.py
/tools/scripts/slot_led_off.py
/tools/scripts/slot_led_on.py
/tools/scripts/slot_power_off.py
/tools/scripts/slot_power_on.py
/tools/scripts/slot_to_numa_node.py
/tools/scripts/slot_to_nvme.py
/tools/scripts/validate_pci.py
tools/stress
tools/stress/stress
tools/stress/stress-ng


Tool Details:
Two tools are provided in the package, both compiled for CentOS 7.2 64-bit.  THese are as follows:
fio:	fio I/O tester from https://github.com/axboe/fio
nvme:	nvme-cli from https://github.com/linux-nvme/nvme-cli  The package is also provided here for
	general use, to install type "unzip nvme-cli-master.zip", cd into the nvme-cli-master directory
	and type "make && make install".  Before building the tools ensure systemd-devel is installed, 
	"yum install systemd-devel".  For running the included run_fio.sh script, the pre-built version
	is sufficient.


Test Script Details:
Many of these scripts in the scripts/directory are used by the run_fio.sh script, so should all be present.

run_fio.sh
This is used to automatically and dynamically generate fio job files for all detected NVMe drives.  
To run, type ./run_fio.sh <time in seconds>

This runs for the specified time for EACH test.
By default, 6 tests are run, all with 256 queue depth.  These are defined towards the end of the file, 
with the "CreateFioJobFile" function.  Comment out tests not required with "#".  The "readonly" option
can also be passed to the script to skip any write tests.  
For specific tests to stress the CPUs, use random tests.
For specific tests to stress the SSD power, use sequential write tests.

Before running this test it is advised to do the following:
1. Set the system time using "date" or automatically.
2. Ensure hw clock is aligned with system time (hwclock -w)
3. Align the SEL log time with system clock (ipmitool sel time set now)
4. Clear the SEL log, (ipmitool sel clear) 
5. Edit the run_fio.sh script, and set the ENCLOSURETYPE variable for the system under test, i.e. 1U10 or 2U24

Logs are saved for the test in the /tools/fio/results directory, for any tests save the logs.


*************************************************************************************************
disable_slot_link.py
Used to disable the link on the PCIe switch to the SSD.  Specify slot number to be disabled.  
Useful for retraining link or disabling while debugging SSD.

*************************************************************************************************
disable_slot_link_all.py
Used to disable the link on the PCIe switch to all SSDs.

*************************************************************************************************
enable_slot_link.py
Used to enable the link on the PCIe switch to the SSD.  Specify slot number to be enabled.

*************************************************************************************************
enable_slot_link_all.py
Used to enable the link on the PCIe switch to all SSDs.

*************************************************************************************************
get_pcie_error_counters.py
Used to print any detected PCIe errors to the terminal.  Use "quiet" to only print out when errors are
detected.  Use "reset" to clear any errors up to this point.  Both of these options can be used 
periodically to check for errors, i.e. "./get_pcie_error_counters.py reset quiet"

*************************************************************************************************
get_power_info.py
Used to print the power information from the PSUs to the terminal.

*************************************************************************************************
get_slot_status.py
Prints status of each slot, as detected by the BMC.  Detects whether interposers are present, LED 
status, etc.  Select an individual slot number or "all".

*************************************************************************************************
interposer_failover.py
Connects an interposer to the controller this is run on.  Use slot number, or all/default/even/odd.
Requires plxreg in same directory
*************************************************************************************************
nvme_to_slot.py
Lists every nvme device, i.e. nvme0, nvme1, etc, and associates these with the physical slot number.
Select an individual slot number or "all". 

*************************************************************************************************
plxreg
Read or write memory-mapped PLX switch registers. Requires upstream domain/bus/device/function and 
register address, e.g. ./plxreg 0000:02:00.0 80

*************************************************************************************************
plxregdump
Dump uo to 256K memory-mapped PLX switch registers. Requires upstream domain/bus/device/function and 
register address, e.g. ./plxregdump 0000:02:00.0

*************************************************************************************************
poll_pcie_error_counters.py
Used to constantly read and print any detected PCIe errors to the terminal.  Specify slot number.

*************************************************************************************************
set_slot_speed.py
Sets the PCIe genX speed for listed slot. Select an individual slot number, the speed, and optionally
"retrain" to maintain the link up during the speed change.  Default is to bring the link down and up.
This works with the 1U or 2U server with either Intel or PLX upstream ports.

*************************************************************************************************
set_slot_speed_all.py
Sets the PCIe genX speed for all slots. Select the speed, and optionally "retrain" to maintain the 
link up during the speed change.  Default is to bring the link down and up.

*************************************************************************************************
slot_led_off.py
Turns off LED for the specified slot.  Select an individual slot number or "all". 

*************************************************************************************************
slot_led_on.py
Turns on LED for the specified slot.  Select an individual slot number or "all". 

*************************************************************************************************
slot_power_off.py
Turns off power for the specified slot.  Select an individual slot number or "all". 

*************************************************************************************************
slot_power_on.py
Turns on power for the specified slot.  Select an individual slot number or "all". 

*************************************************************************************************
slot_to_numa_node.py
Maps each slot to the CPU/NUMA node that it is connected to.  Returns 0 or 1.
Select an individual slot number or "all". 

*************************************************************************************************
slot_to_nvme.py
Maps each slot to the nvme device detected, i.e. nvme0, nvme1, etc.
Select an individual slot number or "all". 

*************************************************************************************************
validate_pci.py
Used to validate the PCIe configuration, including speed and link width.  Also prints any detected 
PCIe errors to the terminal.  Use "quiet" to only print out when errors are
detected.  Use "reset" to clear any errors up to this point.  Both of these options can be used 
periodically to check for errors, i.e. "./validate_pci.py reset quiet"
Auto senses system type based on ipmi fru output, but can be overridden as necessary.

*************************************************************************************************
*************************************************************************************************
stress/stress-ng
CPU stress test utilities.  Used to  stress CPU with high load.  
Recommended usage test for 2 hour test is: ./stress-ng --cpu 0 --cpu-method all -vm 128 -t 7200 
*************************************************************************************************
