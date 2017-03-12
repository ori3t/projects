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
    # c_stop_services()
    with settings(warn_only=True):
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


@roles("controllers")
@parallel
def get_logs_E8InternalTools(log_dir):
    with settings(warn_only=True):
        fio_dir = config.FIO_TEST+"/"+"E8InternalTools/fio/results/*"
        print  fio_dir
        local_dir=log_dir+"/results_"+env.host
        local("mkdir -p  %s" %local_dir)
        get(local_path=local_dir,remote_path=fio_dir)

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
        if len(config.CONTROLLERS.keys()) == 2:
            ctr_type="2U24"
        elif len(config.CONTROLLERS.keys()) == 1:
            ctr_type="1U10"
        else:
            exit(1)
    print ctr_type
    return ctr_type

@runs_once
@roles("controllers")
def _get_block_shift():
    shift_line = run("grep block_shift /opt/E8/data/conf/DONT_USE_first_boot_config.json")
    m = re.search(r"(\d\d?)", shift_line)
    if m:
        return m.group(1)
    else:
        exit(1)

@runs_once
@roles("controllers")
def c_create_volumes():
    """
    - Create and map volume
    """
    hosts = ""
    size="300"
    cmd = []
    block_shift = _get_block_shift()
    for i in config.HOSTS.keys():
         hosts += str(i)+","
    cont = prompt('In order to perform fio %sG test volume(s) need to be created for %s '
                  'Do you want to continue?'%(size,hosts),
                  '(yes/no)',default='yes', validate=r'^yes|no$')
    if cont == 'no':
        exit(1)
    for host in config.HOSTS.keys():
        vol = host
        cmd += ['e8.add_host(host_name="%s")' % host,
                'e8.add_volume(vol_name="%s", vol_capacity_gb=%s, block_shift=%s)' % (vol,size, block_shift),
                'e8.map_volume_to_host(vol_name="%s", host_name="%s")' % (vol, host),
                ]
    c_e8cli(cmd)

def c_e8cli(cmd):
    run("echo -e '%s' | /opt/E8/cli/e8cli.py" % "\\n".join(cmd))