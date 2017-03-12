from fabric.api import *
import tempfile
from fabric.contrib import *
import config

@roles("hosts")
@parallel
def copy_fio():
    with settings(warn_only=True):
        run("mkdir -p {}".format(config.FIO_TEST))
        put("fio", config.FIO_TEST, mode=0755)


@roles("controllers")
def ipmi_fru():
    with hide('everything'), settings(warn_only=False):
        line=run("ipmitool  fru | grep \'Product Name\' ")
        fields = line.strip().split(":")
        system_type = fields[1].split()
        print(system_type[0])

@roles("controllers")
def ipmi_bmc():
    with hide('everything'), settings(warn_only=False):
        line=run("ipmitool bmc info | grep \'Firmware Revision'\ ")
        fields = line.strip().split(":")
        system_type = fields[1].split()
        print(system_type[0])

@roles("controllers")
def bios_ver():
    with hide('everything'), settings(warn_only=False):
        result=run("dmidecode -s bios-version")
        print result

@roles("controllers")
def ipmi_sensor():
    run("ipmitool  sdr list")

@roles("controllers")
def run_fio(ctrl_type):
    fio=config.FIO_TEST+"/E8InternalTools/fio/"
    with cd(fio):
        run("./run_fio.sh -t 10 -c crossover  -n  novalidate -e {}".format(ctrl_type))


@roles("controllers")
def validate_pci(opt=""):
    validate = config.FIO_TEST + "/E8InternalTools/scripts/"
    with cd(validate):
        run("./validate_pci.py {}".format(opt))
    # print "Running validate_pci"
    # with cd(config.FIO_TEST+"/"):
    #     with hide('output', 'running', 'warnings'), settings(warn_only=True):
    #         put("/home/ori/Panacea/ST/E8InternalTools/scripts/*", config.FIO_TEST+"/", mode=777)
    #         run("./validate_pci.py")
    #     result=run("./validate_pci.py")
    #     if not result :
    #         return(1)
    # run("{}/scripts/validate_pci.py".format(config.EXT_SCRIPTS_PATH))