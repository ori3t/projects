import time
from fabric.contrib.files import *
from fabric.api import *
import tempfile
from fabric.contrib import *
import config
import network
import json
from collections import OrderedDict
import os
from fabric.contrib.files import *
from fabric.api import task, env, run, hide, execute, runs_once
from time import sleep


@parallel
@roles("controllers")
@runs_once
def background_run(command):
    command = 'nohup %s &> /dev/null &' % command
    run(command, pty=False)

@roles("controllers")
def pause():
    interfaces = network._get_data_interfaces()
    for port,ip in interfaces.items():
         run("ethtool -S %s | grep pause" % port)
         run("ethtool -a %s " % port)
         #print "%s - %s" % (port, info["state"])
         #print port, 'is' , interfaces[port]



@roles("all")
def check_pause():
    """
     - Print pause parameters and packets
    """
    l = []
    interfaces = network._get_data_interfaces()
    with hide('everything'):
        for interface, info in interfaces.iteritems():
            print "%s - %s" % (interface, info)
    #         l.append(run("ethtool -S %s | grep pause" % interface))
    #         l.append(run("ethtool -a %s " % interface))
    #     str = ''.join(l)
    # print str


# @roles("all")
# def rdma_check():
#     interfaces = network._get_data_interfaces()
#     with hide(), settings(warn_only=True):
#         for port, ip in interfaces.items():
#             if env.host in config.CONTROLLERS.keys():
#                 execute(background_run, "rdma_server")
#             elif env.host in config.HOSTS.keys():
#                 run("rdma_client -s  %s " % (ip))
#             #     if x.return_code == 0:
#             #         print "Passed  RDMA connection %s" %(env.host)
#             #     else:
#             #         print "Bad RDMA connection on  %s" %(env.host)

@roles("controllers")
def rdma_t():
    with hide('everything'):
        interfaces = network._get_data_interfaces()
        for port, ip in interfaces.items():
          print ip
         #
         # execute(rdma_server)
         # execute(rdma_check,ip)



@roles("hosts")
def rdma_check(data_ip):
    with hide(), settings(warn_only=True):
            # if env.host in config.CONTROLLERS.keys():
            #     execute(rdma_server)
            if env.host in config.HOSTS.keys():
                  run("rdma_client -s  %s " % (data_ip))
            # #     if x.return_code == 0:
            #         print "Passed  RDMA connection %s" %(env.host)
            #     else:
            #         print "Bad RDMA connection on  %s" %(env.host)


@runs_once
@roles("controllers")
def rdma_server():
    with hide(), settings(warn_only=True):
        execute(background_run, "rdma_server")
        # run("hostname")
        # # with hide('everything'):
        #
        # run("nohup rdma_server &> /dev/null & ")

@runs_once
@roles("hosts")
def rdma_client():
    with hide('running', 'stdout'), settings(warn_only=True):
        for interface, info in network.interfaces.iteritems():
            x = run("rdma_client -s  %s " % (info.get("ips", [])))
            if x.return_code == 0:
                print "Passed  RDMA connection %s" %(env.host)
            else:
                print "Bad RDMA connection on  %s" %(env.host)


@parallel
@roles("controllers")
def background_run(command):
    command = 'nohup %s &> /dev/null &' % command
    run(command, pty=False)

@roles("hosts")
def h_ib_write_bw(data_port):
    with settings(warn_only=True):
        x = run(" ib_write_bw  -d  %s  -m 4096 %s  -p 1122 -F -a  " % (config.HOSTS[env.host]["port"], data_port))
        if x.return_code == 0:
            print "Passed ib_write_bw test on %s" %(env.host)
        else:
            print "Bad ib_write_bw  test on  %s" %(env.host)

@parallel
@roles("controllers")
def ctr_ib_write_bw():
    with settings(warn_only=True):
        execute(background_run, "ib_write_bw  -m 4200 -F -p 1122  -a")

@roles("hosts")
def h_ib_write_lat(data_port):
    with settings(warn_only=True):
        x = run(" ib_write_lat  -d  %s  -m 4096 %s  -p 1122 -F -a  " % (config.HOSTS[env.host]["port"], data_port))
        if x.return_code == 0:
            print "Passed ib_write_lat test on %s" %(env.host)
        else:
            print "Bad ib_write_lat  test on  %s" %(env.host)

@parallel
@roles("controllers")
def ctr_ib_write_lat():
    with settings(warn_only=True):
        execute(background_run, "ib_write_lat  -m 4200 -F -p 1122  -a")

