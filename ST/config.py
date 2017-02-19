import time
from fabric.contrib.files import *
from fabric.api import *
from fabric.network import ssh
import tempfile
from fabric.contrib import *

ssh.util.log_to_file("paramiko.log", 10)
#####################################################3
DISK_TYPE = "HGST_P100"
DISK_IO_MARGIN = 0.1
EXT_SCRIPTS_PATH = "E8InternalTools"
######################################################
FIO_TEST="/tmp/fio_test"
RAND_READ="rand_read_out.txt"
E8FIO_READ="e8fio_read_out.txt"
W = '\033[0m'  # white (normal)
R = '\033[31m' # red
G = '\033[32m' # green
O = '\033[33m' # orange
P = '\033[35m' # purple


env.hosts = [
     # '#root@abba0',
    #   'root@abba1',
    'root@sm12',
    'root@cliff',
    ]
env.passwords = {
     # 'root@abba0:22': 'tctvkk12rn,di',
    #  'root@abba1:22': 'tctvkk12rn,di',
    'root@cliff:22': 'tctvkk12rn,di',
    'root@sm12:22': 'root',
}


env.user = 'root'
env.password = 'root'
#
# if you have key based authentication, uncomment and point to private key
# env.key_filename = '~/.ssh/id_rsa'
# if you have password based authentication

HOSTS = {
    "sm12": dict(port="mlx5_0"),
    # "sm16": dict(vols="sm16",
    #             controller_ip="10.0.23.169",
    #             numa_cpu_nodes="1"),
    # "sm17": dict(vols="sm17",
    #              controller_ip="10.0.21.168",
    #              numa_cpu_nodes="1"),

}

CONTROLLERS = {
    "cliff": dict(id=0,ip=" ",blk_size=4096,port=" "),    # add controller hostname
    # "abba0": dict(id=1, ip=" ", blk_size=4096, port=" "),  # add controller hostname
}

jobfile="/opt/E8/bin/jobfile"
env.roledefs = {"controllers" : [c for c in CONTROLLERS],
                "hosts" : [h for h in HOSTS],
                "all" : env.hosts}
