import os
import re
import tempfile
from fabric.api import env, run, roles, parallel, settings, put
import config
import network
from fabric.api import *
from fabric.contrib.console import confirm

@roles("controllers")
@parallel
def c_stop_services():
    """
      - stop controller services
     """
    nvme_disks = run('lspci | grep "Non-Volatile memory controller" | wc -l')
    run('systemctl stop hodor aura  chorus  necromancer corosync arbiter')
    for disk in xrange(int(nvme_disks)):
        run('systemctl stop unvmed@' + str(disk))


@roles("controllers")
@parallel
def c_start_services():
    """
      - Start controller services
     """
    nvme_disks = run('lspci | grep "Non-Volatile memory controller" | wc -l')
    for disk in xrange(int(nvme_disks)):
        run('systemctl start unvmed@' + str(disk))
    run('systemctl start hodor aura  chorus  necromancer corosync arbiter')

@roles("hosts")
def h_start_e8():
    """
      - Start host e8block service
     """
    with settings(warn_only=True):
        run("systemctl start e8block")

@roles("hosts")
def h_stop_e8():
    """
      - Stop host e8block service
     """
    with settings(warn_only=True):
        run("systemctl stop e8block")

@roles("controllers")
def c_vanilla_nvme():
    """
      - Change to vanilla linux nvme driver
     """
    c_stop_services()
    run("rmmod nvme")
    run("insmod /usr/lib/modules/`uname -r`/kernel/drivers/block/nvme.ko")

@roles("controllers")
def c_e8_nvme():
    """
      - Change to e8 nvme driver
     """
    run("rmmod nvme")
    run("insmod /usr/lib/modules/`uname -r`/extra/nvme.ko")

@roles("controllers")
@parallel
def copy_E8InternalTools():
    with settings(warn_only=True):
        fio_dir=config.FIO_TEST
        run("mkdir -p {}".format(config.FIO_TEST))
        put("E8InternalTools", fio_dir,mode=0755)
@roles("hosts")
@parallel
def copy_fio():
    with settings(warn_only=True):
        fio_dir=config.FIO_TEST
        run("mkdir -p {}".format(config.FIO_TEST))
        put("fio", fio_dir, mode=0755)

@runs_once
@roles("controllers")
def c_find_ctl_type():
    with hide('everything'):
        if len(env.hosts) == 2:
            print "2U24"
        else:
            print "1U10"
