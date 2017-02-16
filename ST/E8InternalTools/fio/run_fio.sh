#!/bin/bash
#--------------------------------------
# Copyright (c) 2014-2016, E8 Storage Systems Ltd. All Rights Reserved.
# Proprietary and Confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Name   : run_fio.sh
# Author : Stuart Campbell stuart@e8storage.com
# Date   : 2016-06-20
# Version: 1.1 2017-02-12
# Version: 1.0 2017-01-25
# Version: 0.9 2016-12-15
# Version: 0.8 2016-11-04
# Version: 0.7 2016-10-17
# Version: 0.6 2016-10-04
# Version: 0.5 2016-07-08
# Version: 0.4 2016-07-05
# Version: 0.3 2016-07-02
# Version: 0.2 2016-06-23
#
# Changelog:
#     1.1: Added new type of input arguments (getopts).
#          Added "novalidate" argument to avoid validate test and log
#     1.0: Added clarity to error printout for Mellanox PCIe card, replaced "AIC" with MLNX
#     0.9: Added slotcount to limit printout to valid slots.
#          Reduced SLEEPTIME to 10s, sufficient since fio waits for completion.
#          Only log node number in 2U24
#          Added Add-In-Card (AIC) PCIe error logging (card not used for tests).
#          Changed paths to relative rather than absolute.
#     0.8: Fixed dmesg logging, was not logging errors seen in dmesg output between tests.
#     0.7: Added ENCLOSURETYPE field.  Default is 2U24, change as appropriate.
#          Removed some unused tests
#          Changed PCIe error checking script to use "validate_pci.py"
#          Combined slot errors in single printout section
#          Included numjobs field in messages
#          Adjust OS parameter /proc/sys/fs/aio-max-nr to allow for > default 65536 I/Os.
#          Corrected SLEEPTIME to 60s, to exceed I/O timeout (which is default 30 in RHEL 7.2).
#     0.6: Changed default NUMJOBS script parameter to 8
#          Added Interposer errors to summary output
#     0.5: Added absolute path to nvme utility tools so can be run without installing these.
#          Added NUMJOBS script parameter to specify number of threads (default 1)
#     0.4: Added node identification.
#     0.3: Added summary of errors and verify capbility.
#     0.2: Added system identification at start of results file.
#          Added "crossover/cpu0/cpu1" option to stress QPI
#     0.1: Original file.
#
#--------------------------------------

TIMESTAMP=`date +"%Y-%m-%d-%H.%M.%S" | tr -d '\n'`
HOSTNAME=`hostname -s`
LOGFILE="results/fio-$HOSTNAME-$TIMESTAMP.log"
ELOGFILE="results/fio-$HOSTNAME-$TIMESTAMP.elog"
KLOG="/dev/kmsg"
LastKlogMessage="XXXabc123" # just initialise this to some junk value
FioJobCount=0 # count of number of tests to run.  Incremented in CreateFioJobFile()
SLEEPTIME=10s  #time to pause between tests.  Should be longer than NVMe I/O timeout
FIOPATH=../fio
NVMETOOLSPATH=../nvme
SCRIPTPATH=../scripts
ReadOnly=FALSE          # do not do write tests
CrossOver=FALSE         # run from opposite CPU than SSD attached to (max out QPI)
CPU0=FALSE              # force all I/O on CPU 0
CPU1=FALSE              # force all I/O on CPU 1
VERIFY=FALSE            # use fio verify
NUMJOBS=8
ENCLOSURETYPE=2U24	    # Set default value. Options are 1U10, 1U8, 2U24.
VALIDATE=TRUE	        	# perform validation


######################################################################################
usage()
{
cat << EOF
usage: $0 options
This script run fio and different tests on the server.

OPTIONS:
   -h       Help
   -t       <int>        - Time to run per test (Mandatory)
   -r       <readonly>   - Set read only mode
   -c       <crossover>  - Set crossover 
	    <cpu0>       - Set crossover cpu0
            <cpu1>       - Set crossover cpu1
   -v       <verify>     - Set verify
   -e       <2U24>       - Set 2u24 enclosure (default)
            <1U10>       - Set 1u10 enclosure
            <1U8>        - Set 1u8 enclosure
   -n       <novalidate> - Disable validation

example:
$0 -t 10 -c cpu0

EOF
}

TEST=
SERVER=
PASSWD=
VERBOSE=
while getopts ":h:t:r:c:v:e:n:" OPTION
do
     case $OPTION in
         h)
             usage
             exit
             ;;
         t)
             TIME=$OPTARG
               if [[ "$TIME" -ne "$TIME" ]] ; then
                 echo "time not valid"
                 exit
               fi
             ;;
         r)
             READ_OPT=$OPTARG
               if [[ "$READ_OPT" == "readonly"  ]] ; then
                 ReadOnly=TRUE
               else
                echo "ReadOnly value not valid"
                exit
              fi
             ;;
         c)
             CROSS_OPT=$OPTARG
              if [[  "$CROSS_OPT" == "cpu0"  ]] ; then
                CPU0=TRUE
              elif [[  "$CROSS_OPT" == "cpu1"  ]] ; then
                CPU1=TRUE
              elif [[  "$CROSS_OPT" == "crossover"  ]] ; then
                CrossOver=TRUE
              else
                echo "CPU value not valid"
                exit
              fi
             ;;
         v)
             VERIFY_OPT=$OPTARG
             if [[ "$VERIFY_OPT" == "verify" ]] ; then
               VERIFY=TRUE
             else
               echo "VERIFY value not valid"
               exit
             fi
             ;;
         e)
             ENCLOSURE_OPT=$OPTARG
             if [ "$ENCLOSURE_OPT" != "2U24" ] || [ "$ENCLOSURE_OPT" != "1U10" ] || [ "$ENCLOSURE_OPT" != "1U8" ] ; then
               ENCLOSURETYPE="$ENCLOSURE_OPT" 	# options are 1U10, 1U8, 2U24
             else
               echo "ENCLOSURETYPE value not valid"
               exit
             fi
             ;;
         n)
             NO_VALIDATE_OPT=$OPTARG
             if [[ "$NO_VALIDATE_OPT" == "novalidate" ]] ; then
               VALIDATE=FALSE
             else
               echo "VERIFY value not valid"
               exit
             fi
             ;;

         ?)
             usage
             exit
             ;;
     esac
done

if [[ -z $TIME ]]
then
echo "Time not set . This parameter is mandatory "
     usage
     exit 1
fi



# validate that necessary scripts and executables are present

if [ ! -x "$FIOPATH/fio" ]; then
  echo "Please install fio and/or set FIOPATH in script file"
  exit 1
fi 

if [ ! -x "$SCRIPTPATH/slot_to_nvme.py" ]; then
  echo "Please install slot_to_nvme.py script and/or set SCRIPTPATH in script file"
  exit 1
fi 

if [ ! -x "$SCRIPTPATH/slot_to_numa_node.py" ]; then
  echo "Please install slot_to_numa_node.py script and/or set SCRIPTPATH in script file"
  exit 1
fi 

if [ ! -x "$SCRIPTPATH/nvme_to_slot.py" ]; then
  echo "Please install nvme_to_slot.py script and/or set SCRIPTPATH in script file"
  exit 1
fi 

if [ ! -x "$SCRIPTPATH/validate_pci.py" ]; then
  echo "Please install validate_pci.py script and/or set SCRIPTPATH in script file"
  exit 1
fi 

# create results directory (if necessary) to keep logs clean.

if [ ! -d "results" ]; then
  mkdir "results"
fi 

# calculate slot count
if [ $ENCLOSURETYPE == "2U24" ]; then
  SLOTCOUNT=24
elif [ $ENCLOSURETYPE == "1U10" ]; then
  SLOTCOUNT=10
elif  [ $ENCLOSURETYPE == "1U8" ]; then
  SLOTCOUNT=8
else
  exit 1
fi

TimeStamp()
{
  date +"%Y-%m-%d-%H:%M.%S" | tr -d '\n'
}

LogMessage()
{
# Logs a message into the logfile AND some of it to the terminal AND kernel log

  Message="`date +"%Y-%m-%d-%H:%M.%S" | tr -d '\n'`: $@"; 
  echo >> $LOGFILE
  echo >> $LOGFILE
  echo '--------------------------------------------------------------------------------' >> $LOGFILE
  echo $Message | tee -a $LOGFILE
  echo $(basename $0): $Message >> $KLOG
  LastKlogMessage=$Message
  echo '--------------------------------------------------------------------------------' >> $LOGFILE
}

KLogMessage()
{
# Logs a message into the kernel log (dmesg)

  Message="`date +"%Y-%m-%d-%H:%M.%S" | tr -d '\n'`: $@";
  LastKlogMessage=$Message
  echo $(basename $0): $Message >> $KLOG
}

CheckKLog()
{
# Checks for any new additions to the logs AFTER the last message printed to the kernel log

  echo >> $LOGFILE
  echo >> $LOGFILE
  echo '****************************************************' >> $LOGFILE
  echo dmesg output since previous test >> $LOGFILE
  dmesg | grep -A 10000 "$LastKlogMessage" >> $LOGFILE
  echo '****************************************************' >> $LOGFILE
  echo >> $LOGFILE
  echo >> $LOGFILE
}


LogMessageFile()
{
# Logs a message into the logfile only

  Message="`date +"%Y-%m-%d-%H:%M.%S" | tr -d '\n'`: $@"; 
  echo >> $LOGFILE
  echo >> $LOGFILE
  echo '****************************************************' >> $LOGFILE
  echo $Message >> $LOGFILE
  echo '****************************************************' >> $LOGFILE
}


NVMeTemperatureLog()
{


  echo >> $LOGFILE
  echo >> $LOGFILE
  echo '****************************************************' >> $LOGFILE
  TimeStamp >> $LOGFILE
  echo "" NVMe Temperature SMART >> $LOGFILE
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
      Temperature=$($NVMETOOLSPATH/nvme smart-log $devicepath | grep temperature | cut -d':' -f 2)
      printf "Slot: %02d Device: %-10s %s\n" "$i" "$NVMeDevice" "$Temperature" >> $LOGFILE
    fi
  done

}

PCIeErrorLog()
{

  echo >> $LOGFILE
  echo >> $LOGFILE
  echo '****************************************************' >> $LOGFILE
  TimeStamp >> $LOGFILE
  echo "" PCIe Error Log >> $LOGFILE
  echo '****************************************************' >> $LOGFILE
  
  $SCRIPTPATH/validate_pci.py quiet reset $ENCLOSURETYPE >> $LOGFILE
  echo >> $LOGFILE
  echo >> $LOGFILE

}


CreateFioJobFile()
{
# arguments: $1 access type (read/write/randread/randwrite/readwrite)
# arguments: $2 access size
# arguments: $3 iodepth
# arguments: $4 runtime

#  FileName="$1$2-$3.fio"
  FileName="$1$2-$NUMJOBS-$3.fio"

# Common global header for all files

  echo "#$TIMESTAMP Autogenerated jobfile $FileName created" > $FileName
  echo "[global]" >> $FileName
  echo "ioengine=libaio" >> $FileName
  echo "direct=1" >> $FileName
  echo "directory=/dev" >> $FileName
  echo "numa_mem_policy=local" >> $FileName
  echo "numjobs=$NUMJOBS" >> $FileName
  echo "time_based=1" >> $FileName
  echo "runtime=$4" >> $FileName

  if [ $VERIFY == "TRUE" ] && [ $1 == "write" ] ; then
    echo "verify=crc32c-intel" >> $FileName
    echo "do_verify=1" >> $FileName
  fi


# File specific global-header 

  echo "readwrite=$1" >> $FileName
  echo "bs=$2" >> $FileName
  echo "iodepth=$3" >> $FileName
  echo >> $FileName
  echo >> $FileName

# Now for each slot, list the nvme target if present.
# Also set the numa node based on the CPU the SSD is connected to.

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
      echo "[Slot "$i"-"$NVMeDevice"n1]" >> $FileName
      echo "filename="$NVMeDevice"n1" >> $FileName
      NUMANode=$($SCRIPTPATH/slot_to_numa_node.py ${i})

      # for test purposes, can crossover so that the numa node is the opposite to where the SSD is located.
      # Or can select what CPU specifically to use.

      if [ $CrossOver == "TRUE" ]; then
        if [ $NUMANode == "0" ]; then
          NUMANode=1
        else
          NUMANode=0
        fi
      elif [ $CPU0 == "TRUE" ]; then
          NUMANode=0
      elif [ $CPU1 == "TRUE" ]; then
          NUMANode=1
      fi    

      echo "numa_cpu_nodes="$NUMANode >> $FileName
      echo >> $FileName
    fi
  done


# Save the jobfile name
  FIOJOBFILE[$FioJobCount]=$FileName

# Finally, increment global variable used to keep track of number of tests
  FioJobCount=$(($FioJobCount + 1))

}


# Count the number of nvme devices, for informational purposes

NVMeDeviceCount=0

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
    NVMeDeviceCount=$(($NVMeDeviceCount + 1))
  fi
done

# ensure we have at least one device to test.

if [ $NVMeDeviceCount -eq 0 ]; then
  echo "No NVMe Devices to test"
  exit 1
fi


# First create the required test files.  This is dynamic, and created for each of 6 different 
# tests in total.  These are as follows:
# Sequential Read 128KB 256 I/O
# Random Read 4KB 256 I/O
# Sequential Write 128KB 256 I/O
# Random Write 4KB 256 I/O
# Sequential Simultaneous Read/Write 128KB 256 I/O
# Random Simultaneous Read/Write 4KB 256 I/O

CreateFioJobFile read 128k 256 ${TIME}
CreateFioJobFile randread 4k 256 ${TIME}

if [ $ReadOnly == "FALSE" ]; then
  CreateFioJobFile write 128k 256 ${TIME}
  CreateFioJobFile randwrite 4k 256 ${TIME}
  CreateFioJobFile readwrite 128k 256 ${TIME}
  CreateFioJobFile randrw 4k 256 ${TIME}
fi

KLogMessage ""
LogMessage "Running $FioJobCount fio $2 $3 tests with $NUMJOBS threads on $NVMeDeviceCount SSDs for $1s per test"

LogMessageFile "BIOS Information"
dmidecode -t bios -q >> $LOGFILE

LogMessageFile "System Information"
ipmitool mc info >> $LOGFILE
ipmitool fru >> $LOGFILE

if [ $ENCLOSURETYPE == "2U24" ]; then
  LogMessageFile "Node:"
  ipmitool raw 0x3c 0xa5 >> $LOGFILE  # command to read the node, either 00 or 01.  Valid for 2U only.
fi

LogMessageFile "lspci -vvv"
lspci -vvv >> $LOGFILE

LogMessageFile "BMC sensors"
ipmitool sensor >> $LOGFILE

LogMessageFile "BMC SEL Log"
ipmitool sel list >> $LOGFILE
echo End of SEL Log >> $LOGFILE
echo >> $LOGFILE
echo >> $LOGFILE

LogMessageFile "NVMe Driver Info"
modinfo nvme >> $LOGFILE

LogMessageFile "NVMe Device List"
$NVMETOOLSPATH/nvme list >> $LOGFILE

LogMessageFile "Slot to NVMe Device Mapping"
$SCRIPTPATH/slot_to_nvme.py all >> $LOGFILE

LogMessageFile "NVMe to Slot Device Mapping"
$SCRIPTPATH/nvme_to_slot.py all >> $LOGFILE

#log temperature
NVMeTemperatureLog

# Clear PCIe errors
if [ "$VALIDATE" = TRUE ]; then  
  $SCRIPTPATH/validate_pci.py silent reset $ENCLOSURETYPE
fi
# Adjust the number of commands that can be sent
# This number allows for > 80 threads, 256 commands, 24 SSDs.  Adjust as appropriate.
echo 524288 > /proc/sys/fs/aio-max-nr


# This is where the fio testing starts.

for ((JobNo=0; JobNo<FioJobCount; JobNo++));
do

  LogMessage "Starting ${FIOJOBFILE[$JobNo]}"
  echo "*****jobfile*****" >> $LOGFILE
  cat ${FIOJOBFILE[$JobNo]} >> $LOGFILE
  echo "*****jobfile end*****" >> $LOGFILE
  echo >> $LOGFILE
  echo "*****fio output log*****" >> $LOGFILE
  $FIOPATH/fio ${FIOJOBFILE[$JobNo]} >> $LOGFILE
  echo "*****fio output end*****" >> $LOGFILE

  NVMeTemperatureLog
  LogMessageFile "BMC sensors"
  ipmitool sensor >> $LOGFILE

  sleep $SLEEPTIME
  CheckKLog
  if [ "$VALIDATE" = TRUE ]; then
    PCIeErrorLog
  fi

  LogMessage "Completed ${FIOJOBFILE[$JobNo]}"

#cleanup the job files.  The content is saved in the log for reference
  rm ${FIOJOBFILE[$JobNo]}

done


# All tests are completed.  Log the BMC SEL log, in case anything has changed.
LogMessageFile "BMC SEL Log"
ipmitool sel list >> $LOGFILE
echo "End of SEL Log" >> $LOGFILE
echo >> $LOGFILE
echo >> $LOGFILE

# Dump summary performance results to the terminal
echo '****************************************************' | tee -a $LOGFILE
echo "Performance Summary" | tee -a $LOGFILE
grep "aggrb=" $LOGFILE | tee -a $LOGFILE

# Dump summary PCIe error counter results to the terminal and error logfile
if [ "$VALIDATE" = TRUE ]; then
  echo "" | tee -a $ELOGFILE
  echo "" | tee -a $ELOGFILE
  echo '****************************************************' | tee -a $ELOGFILE
  echo "PCIe Error Summary" | tee -a $ELOGFILE
  echo "" | tee -a $ELOGFILE

  echo "Mellanox Add-In-Card 0 PCIe Error Log" | tee -a $ELOGFILE
  grep "MLNX-0" $LOGFILE | tee -a $ELOGFILE
  echo "" | tee -a $ELOGFILE

  echo "Mellanox Add-In-Card 1 PCIe Error Log" | tee -a $ELOGFILE
  grep "MLNX-1" $LOGFILE | tee -a $ELOGFILE
  echo "" | tee -a $ELOGFILE

  if [ $ENCLOSURETYPE == "2U24" ]; then
    echo "CPU0/Switch 0 PCIe Error Log" | tee -a $ELOGFILE
    grep "PCISW-0" $LOGFILE | tee -a $ELOGFILE
    echo "" | tee -a $ELOGFILE

    echo "CPU1/Switch 1 PCIe Error Log" | tee -a $ELOGFILE
    grep "PCISW-1" $LOGFILE | tee -a $ELOGFILE
    echo "" | tee -a $ELOGFILE

  fi


  for i in {1..24}
  do

    echo "Slot $i PCIe Error Log" | tee -a $ELOGFILE
    searchstring=$(printf 'grep "Slot %02d " %s | tee -a %s' "$i" "$LOGFILE" "$ELOGFILE")
    eval "$searchstring"
    echo "" | tee -a $ELOGFILE

    if [ $i == $SLOTCOUNT ];
    then
      break
    fi
  done


  echo '****************************************************' | tee -a $ELOGFILE
  #copy elog file to logfile
  cat $ELOGFILE >> $LOGFILE
fi
LogMessage "fio Testing Complete"
KLogMessage ""


