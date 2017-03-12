#!/usr/bin/env bash


CTRL_TYPE=""

function log {
  echo "*************************************************" |tee -a $2
  echo "        $1                                       " |tee -a $2
  echo "*************************************************" |tee -a $2
}


function return_status {
  local __resultvar=$1
  local log=$2
  rc=`grep -e "^ERROR: " ${log}`
  if [  "$rc" ];then
    status="ERROR"
  else
    status="GOOD"
  fi
  eval $__resultvar="'$status'"
}

now=$(date +'%Y-%m-%d-%H-%M')
basedir="st_log"/${now}
mkdir -p $basedir
data_ips=`fab rdma_t --hide=running,status`
CTRL_TYPE=`fab c_find_ctl_type --hide=running,status`
echo $CTRL_TYPE
##-------------------- copy stuff --------------------------------
#fab copy_E8InternalTools
#fab copy_fio


#
#-------------------- FIRMWARE_VER ---------------------------
firmware_log=${basedir}/"firmware_ver.txt"
log "RUNNING FIRMWARE_VER TESTS" $firmware_log
CTRL_TYPE=`fab c_find_ctl_type --hide=running,status`
fpu_ver=`fab ipmi_fru --hide=running,status|sort|uniq`
bmc_ver=`fab ipmi_bmc --hide=running,status|sort|uniq`
bios_ver=`fab bios_ver --hide=running,status|sort|uniq`
echo "Controller type:"$CTRL_TYPE  | tee -a  $firmware_log
echo "FRU Product Name:"$fpu_ver  | tee -a  $firmware_log
echo "BMC version:"$bmc_ver       | tee -a  $firmware_log
echo "BIOS version:"$bios_ver     | tee -a  $firmware_log
firmware_ver=`fab system_ver:"$fpu_ver,$bmc_ver,$bios_ver,$CTRL_TYPE"  --hide=running,status`
#

##-------------------- HW_TEST --------------------------------
#
fab h_stop_e8
fab c_stop_services
fab c_vanilla_nvme
fab validate_pci:"silent reset"
fab run_fio:$CTRL_TYPE
hw_test=`fab validate_pci`
echo "##### RESULT #####"
echo $hw_test
echo "###################"
hw_test_status=`echo $hw_test |grep -e Bad  -e AER -e error -e ERR -e Slot`
 if [ "$hw_test_status" ];then
  status_hw_test="ERROR"
else
  status_hw_test="GOOD"
fi
fab get_logs_E8InternalTools:"$basedir"
echo $status_hw_test
fab c_e8_nvme

#
#
##-------------------- rdma_check --------------------------------
#
#echo $data_ips
#writelog=${basedir}/"rdma_check.txt"
#log "TEST OF RDMA" $writelog
#for ip in $data_ips;do
#  echo "checking ${ip}" | tee $writelog
#  run=`fab rdma_server --hide=status,status`  #--hide=running,status
#  status=`fab rdma_check:$ip --hide=status,status`
#  echo $status | tee -a $writelog
#done
####-------------------- ib_write_bw --------------------------------
##
#writelog=${basedir}/"ib_write_bw.txt"
#log "TEST OF ib_write_bw" $writelog
#for ip in $data_ips;do
#  log $ip $writelog
#  sleep 1
#  fab ctr_ib_write_bw       | tee -a $writelog
#  fab h_ib_write_bw:${ip}   | tee -a $writelog
#done
#return_status status_ib_write_bw $writelog
#echo $status_ib_write_bw
#
#####-------------------- ib_write_lat --------------------------------
##
#writelog=${basedir}/"ib_write_lat.txt"
#log "TEST OF ib_write_lat" $writelog
#for ip in $data_ips;do
#  log $ip $writelog
#  sleep 1
#  fab ctr_ib_write_lat      | tee -a $writelog
#  fab h_ib_write_lat:${ip}  | tee -a $writelog
#done
#return_status status_ib_write_lat $writelog
#echo $status_ib_write_lat
##
####-------------------- create_volumes --------------------------------
##
###fab c_create_volumes
##
####-------------------- e8lib_randread --------------------------------
##
#fab c_start_services
#fab c_e8_nvme #TODO remove
#e8lib_log=${basedir}/"e8lib_randread"
#for ip in $data_ips;do
#  echo "checking ${ip}" | tee $e8lib_log
#  fab e8fio_read:${ip}  | tee $e8lib_log
#  e8lib_rc=$(grep GOOD $e8lib_log)
#  echo $e8lib_rc
#  if [ "$e8lib_rc" ];then
#    status_e8lib_randread="GOOD"
#  else
#    status_e8lib_randread="ERROR:"
#  fi
#  echo "this is $status_e8lib_randread"
#  break
#done
##
##
####-------------------- fio_randread --------------------------------
##
#fab h_start_e8
#echo "sleep for 30sec"
#sleep 30
#fab rand_read
#perf=`fab rand_read_perf`
#echo $perf
#e8block_rc=$(echo $perf |grep GOOD)
#if [ "$e8block_rc" ];then
#  status_fio_randread="GOOD"
#else
#  status_fio_randread="ERROR"
#fi




##-------------------- STATUS --------------------------------

system_log=${basedir}/"system.txt"
echo "*************************************************" |tee -a $system_log
echo FW_VERSIONS ............. $firmware_ver          | tee -a $system_log
echo IB_WRITE_BW ............. $status_ib_write_bw    | tee -a $system_log
echo IB_WRITE_LAT ............ $status_ib_write_lat   | tee -a $system_log
echo HW TESTS ................ $status_hw_test        | tee -a $system_log
echo FIO e8lib ............... $status_e8lib_randread | tee -a $system_log
echo FIO e8block ............. $status_fio_randread   | tee -a $system_log