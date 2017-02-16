import time
from fabric.contrib.files import *
from fabric.api import *
import tempfile
from fabric.contrib import *
import config
import json
from collections import OrderedDict



@runs_once
def disk_tresholds(run_type):
    with open('disk_tresholds.json') as fp:
        actions_map = json.load((fp), object_pairs_hook=OrderedDict)
        fp.seek(0)
    for key, value in actions_map.iteritems():
        if key in config.DISK_TYPE:
            max_val = value['e8block'] + value['e8block']*config.DISK_IO_MARGIN
            min_val = value['e8lib'] - value['e8lib']*config.DISK_IO_MARGIN
            print(config.R + "" + str(max_val) + " " + config.W)
            return(max_val,min_val)


@roles("hosts")
@runs_once
def _mach_performance(results_file,run_type):
    import re
    with open('disk_tresholds.json') as fp:
        actions_map = json.load((fp), object_pairs_hook=OrderedDict)
        fp.seek(0)
    for key, value in actions_map.iteritems():
        if key in config.DISK_TYPE:
            max_val = value[run_type] + value[run_type]*config.DISK_IO_MARGIN
            min_val = value[run_type] - value[run_type]*config.DISK_IO_MARGIN
    with hide('everything'), settings(warn_only=True):
        line = run("grep iops {0}/{1}".format(config.FIO_TEST,results_file))
        m = re.search(r"iops=(\d+\(?)", line)
        b = re.search(r"bw=(\d+\(?)", line)
        iop=int(m.group(1))
        bw=int(b.group(1))
        if int(min_val) <= iop <= int(max_val):
            print " GOOD: HOST : {0}   IOPS: {1} {2} {3} BW: {4}".format(env.host, config.G, iop, config.W, bw)
        else:
            print " ERROR: HOST : {0}  IOPS: {1} {2} {3} BW: {4}".format(env.host, config.G, iop, config.W, bw)


#
#
# with hide('everything'), settings(warn_only=True):
#     line = run("grep iops {0}/{1}".format(config.FIO_TEST, results_file))
#     print line
#     for word in line.split(","):
#         if "iops" in word:
#             result = re.split("\D+", word)
#             for iop in result:
#                 if iop.isdigit():
#                     if int(min_val) < iop.strip < int(max_val):
#                         print " Good: HOST : {0}   IOPS :  {2} ".format(env.host, iop)
#                     else:
#                         print " ERROR: HOST : {0}   IOPS : {1} {2} {3}".format(env.host, config.R, iop, config.W)

@roles("hosts")
@parallel
def copy_fio():
    with settings(warn_only=True):
        fio_dir=config.FIO_TEST
        run("mkdir -p {}".format(config.FIO_TEST))
        put("fio", fio_dir, mode=0755)

@roles("hosts")
@parallel
def create_tempdir():
    cmd=""
    with settings(warn_only=True):
        tempdir = tempfile.mkdtemp()
        run("mkdir -p " + tempdir)
        put("fio", tempdir, mode=0755)

@roles("hosts")
def _fio_read(  iodepth=64,
                numjobs=4,
                runtime=30,
                size="30GiB",
                engine="libaio",
                rw="randrw",
                numa=0,
                filename=None
                ):
        args = ["./fio" ,
                "--name=fio",
                "--group_reporting=1",
                "--direct=1",
                "--iomem_align=4k",
                "--iodepth=%i" % iodepth,
                "--runtime=%i" % runtime,
                "--rw=%s" % rw,
                "--output=%s" %filename,
                "--bs=4k",
                "--ramp_time=1",
                "--filename=/dev/e8b0",
                "--size=%s" % size,
                "--ioengine=%s" %engine,
                "--numjobs=%i" %numjobs,
                " --numa_cpu_nodes=%i" %numa,
                ]
        with cd(config.FIO_TEST):
            run(" ".join(args))


def _e8fio(filename,
            engine,
            iodepth=64,
            numjobs=8,
            runtime=10,
            size="30GiB",
            rw="read",
            out_file=None
              ):
    args = ["./fio",
            "--name=e8fio",
            "--group_reporting=1",
            "--iodepth=%s" % iodepth,
            "--runtime=%s" % runtime,
            "--readwrite=%s" % rw,
            "--output=%s" % out_file,
            "--bs=4k",
            "--iomem_align=4k",
            "--ramp_time =1",
            "--filename=%s" %filename,
            "--size=%s" % size,
            "--ioengine=%s" % engine,
            "--numjobs=%s" % numjobs,
            "--thread",
            ]
    with cd(config.FIO_TEST):
        run(" ".join(args))

# /opt/E8/bin/fio --name=fio --group_reporting --iodepth=64 --runtime=20 --filename=rdma\://10.0.23.151\:1122,sma
# --rw=randread --bs=4k   --output=t_out.txt --iomem_align=4k --ioengine=/opt/E8/lib/e8fio_eng.so --direct=1 --numjobs=4
# --thread --size=40GiB

@parallel
@roles("hosts")
def rand_read():
    with hide(), settings(warn_only=True):
        execute(_fio_read, iodepth=64,
                  numjobs=8,
                  runtime=10,
                  size="30GiB",
                  engine="libaio",
                  rw="randrw  --rwmixread=100",
                  filename=config.RAND_READ
                )

@parallel
@roles("hosts")
def rand_read_perf():
    execute(_mach_performance,config.RAND_READ,"e8block")


@parallel
@roles("hosts")
def e8fio_read():
    with hide('running', 'stdout'), settings(warn_only=True):
        print config.HOSTS[env.host]["controller_ip"]
        execute(_e8fio,filename="rdma\\://%s\\:1122,%s" % (config.HOSTS[env.host]["controller_ip"],
                                                           config.HOSTS[env.host]["vols"]),
                engine="/opt/E8/lib/e8fio_eng.so",
                iodepth=64,
                numjobs=1,
                runtime=10,
                size="100GiB",
                rw="randrw",
                out_file=config.E8FIO_READ)

        execute(_mach_performance,config.E8FIO_READ,"e8lib")



@roles("hosts")
def rdma_client():
    with hide('running', 'stdout'), settings(warn_only=True):
        x = run("rdma_client -s  %s " % (config.HOSTS[env.host]["controller_ip"]))
        if x.return_code == 0:
            print "Passed  RDMA connection %s" %(env.host)
        else:
            print "Bad RDMA connection on  %s" %(env.host)





