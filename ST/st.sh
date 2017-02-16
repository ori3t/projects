#!/usr/bin/env bash


function log {
  echo "*********************************" |tee -a $2
  echo "        $1                       " |tee -a $2
  echo "*********************************" |tee -a $2
}

now=$(date +'%Y-%m-%d-%H-%M')
basedir="st_log"/${now}
mkdir -p $basedir
data_ips=`fab rdma_t --hide=running,status`


##-------------------- fio_randrw --------------------------------
#fab rand_read
#perf=`fab rand_read_perf`
#echo $perf
#fio_randrw=$(echo $perf |grep GOOD)
#if [ "$fio_randrw" ];then
#  status_fio_randrw="GOOD"
#else
#  status_fio_randrw="ERROR"
#fi
#echo $status_fio_randrw
#
#-------------------- HW SCRIPTS --------------------------------

fab h_stop_e8
fab c_vanilla_nvme
ctr_type=`fab c_find_ctl_type --hide=running,status`
echo $ctr_type
fab validate_pci:"silent reset"
fab run_fio:$ctr_type
fab validate_pci
##-------------------- rdma_check --------------------------------
#writelog=${basedir}/"rdma_check.txt"
#log "TEST OF RDMA" $writelog
#for ip in $data_ips;do
#  echo "checking ${ip}" | tee $writelog
#  run=`fab rdma_server --hide=status,status`  #--hide=running,status
#  status=`fab rdma_check:$ip --hide=status,status`
#  echo $status | tee -a $writelog
#done
###-------------------- ib_write_bw --------------------------------
#writelog=${basedir}/"ib_write_bw.txt"
#log "TEST OF ib_write_bw" $writelog
#for ip in $data_ips;do
#  log $ip $writelog
#  fab ctr_ib_write_bw       | tee -a $writelog
#  fab h_ib_write_bw:${ip}   | tee -a $writelog
#done
#
###-------------------- ib_write_lat --------------------------------
#writelog=${basedir}/"ib_write_lat.txt"
#log "TEST OF ib_write_lat" $writelog
#for ip in $data_ips;do
#  log $ip $writelog
#  fab ctr_ib_write_lat      | tee -a $writelog
#  fab h_ib_write_lat:${ip}  | tee -a $writelog
#done
