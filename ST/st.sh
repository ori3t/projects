#!/usr/bin/env bash


function log {
  echo "*********************************" |tee -a $2
  echo "        $1                       " |tee -a $2
  echo "*********************************" |tee -a $2
}


function return_status {
local __resultvar=$1
local log=$2
rc=`grep -e "^ERROR: " ${log}`
if [ ! "$ib_write_lat_rc" ];then
  status="GOOD"
else
  status="ERROR"
fi
eval $__resultvar="'$status'"
}

now=$(date +'%Y-%m-%d-%H-%M')
basedir="st_log"/${now}
mkdir -p $basedir
data_ips=`fab rdma_t --hide=running,status`

##-------------------- copy stuff --------------------------------
fab copy_E8InternalTools
fab copy_fio


#
#-------------------- HW_TEST --------------------------------

fab h_stop_e8
fab c_vanilla_nvme
ctr_type=`fab c_find_ctl_type --hide=running,status`
echo $ctr_type
fab validate_pci:"silent reset"
fab run_fio:$ctr_type
hw_test=`fab validate_pci`
if [ "$hw_test" ];then
  status_hw_test="GOOD"
else
  status_hw_test="ERROR"
fi
fab get_logs_E8InternalTools:"$basedir"
echo $status_hw_test
fab c_e8_nvme


#-------------------- rdma_check --------------------------------

writelog=${basedir}/"rdma_check.txt"
log "TEST OF RDMA" $writelog
for ip in $data_ips;do
  echo "checking ${ip}" | tee $writelog
  run=`fab rdma_server --hide=status,status`  #--hide=running,status
  status=`fab rdma_check:$ip --hide=status,status`
  echo $status | tee -a $writelog
done
###-------------------- ib_write_bw --------------------------------

writelog=${basedir}/"ib_write_bw.txt"
log "TEST OF ib_write_bw" $writelog
for ip in $data_ips;do
  log $ip $writelog
  sleep 1
  fab ctr_ib_write_bw       | tee -a $writelog
  fab h_ib_write_bw:${ip}   | tee -a $writelog
done
return_status status_ib_write_bw $writelog
echo $status_ib_write_bw
###-------------------- ib_write_lat --------------------------------

writelog=${basedir}/"ib_write_lat.txt"
log "TEST OF ib_write_lat" $writelog
for ip in $data_ips;do
  log $ip $writelog
  sleep 1
  fab ctr_ib_write_lat      | tee -a $writelog
  fab h_ib_write_lat:${ip}  | tee -a $writelog
done
return_status status_ib_write_lat $writelog
echo $status_ib_write_lat

##-------------------- create_volumes --------------------------------

#fab c_create_volumes

##-------------------- e8lib_randread --------------------------------

fab c_e8_nvme #TODO remove
e8lib_log=${basedir}/"e8lib_randread"
for ip in $data_ips;do
  echo "checking ${ip}" | tee $e8lib_log
  fab e8fio_read:${ip}  | tee $e8lib_log
  e8lib_rc=$(grep GOOD $e8lib_log)
  echo $e8lib_rc
  if [ "$e8lib_rc" ];then
    status_e8lib_randread="GOOD"
  else
    status_e8lib_randread="ERROR:"
  fi
  echo "this is $status_e8lib_randread"
  break
done


##-------------------- fio_randread --------------------------------

fab h_start_e8
echo "sleep for 30sec"
sleep 30
fab rand_read
perf=`fab rand_read_perf`
echo $perf
e8block_rc=$(echo $perf |grep GOOD)
if [ "$e8block_rc" ];then
  status_fio_randread="GOOD"
else
  status_fio_randread="ERROR"
fi


##-------------------- STATUS --------------------------------
echo IB_WRITE_BW ............. $status_ib_write_bw
echo IB_WRITE_LAT ............ $status_ib_write_lat
echo HW TESTS ................ $status_hw_test
echo FIO e8lib ............... $status_e8lib_randread
echo FIO e8block ............. $status_fio_randread