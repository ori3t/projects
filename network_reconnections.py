#!/usr/bin/env python

import argparse
import os
import time
from subprocess import call, Popen, PIPE
import random
from random import choice as rchoice
import subprocess
import sys
import logging
import re


#######################
always_up_ports = 1
host_list = []
host_file = "host_list"
logname = "network.log"
host_port = ['ens1f0']
ctr_ip = ["data_0_1", "data_0_2", "data_0_3", "data_0_0"]
#host_list = ['nodea', 'nodeb', 'nodec', 'noded']

logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s  %(levelname)s   %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)


def find_hosts(host_list):
        with open( host_list, 'r') as f:
            only_hosts=[]
            lines = f.readlines()
            for line in lines:
                part = line.rsplit(',')
                only_hosts.append(part[0])
        return only_hosts

def find_host_ports(root_host):
        ports_40G = []
        ssh_ls_cmd = "ssh "+ root_host + " ls -1 /sys/class/net/"
        try:
            port_list = subprocess.check_output(ssh_ls_cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as exc:
            print("Status : FAIL", exc.returncode, exc.output)

        print("Output: \n{}\n".format(port_list))
        for port in port_list.split('\n'):
            # print port
            if port == 'lo':
                break
            port_cmd = "ethtool " + port + " |grep 'Speed:'"
            p_speed = subprocess.Popen(['sshpass', '-p', 'root', 'ssh', root_host, port_cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (speed, stderr) = p_speed.communicate()
            #speed.strip()
            print "speed of port {0} is: {1}".format(port,speed)
            speed_digit = re.search(r'\d+', speed)
            if speed_digit:
                print "speed_digit", speed_digit.group(0)
                try:
                    speed_p = int(speed_digit.group(0))
                except Exception:
                    return False
                if speed_p >= 40000:
                    print "port matched is ", port
                    ports_40G.append(port)
                    print "port matched is ", port
        return ports_40G


def turn_port_host(host_name, command, port_list):
    for changing_status_ports in port_list:
        subprocess.call(["ssh", host_name, "hostname"])
        logging.info("Port " + (changing_status_ports) + "on " + (host_name) + " is going down")
        subprocess.call(["ssh", host_name, "ifdown", changing_status_ports])
        print changing_status_ports
        time.sleep(3)
        ret = subprocess.call(["ssh", host_name, "ifup", changing_status_ports])
        logging.info("Port " + (changing_status_ports) + " on " + (host_name) + " is going up")
        if ret != 0:
            if ret < 0:
                logging.info("Port" + str(changing_status_ports) + "failed")
            else:
                logging.info("Failed to get RC of " + str(changing_status_ports))
        time.sleep(6)


def turn_ctr_port(command, port_list):
    for changing_status_ports in port_list:
        print changing_status_ports
        bash_network_cmd = command, changing_status_ports
        logging.info("Controller port" + str(changing_status_ports) + " will " + command)
        print "Controller port {0} is changeing status , cmd is {1} ".format(changing_status_ports, bash_network_cmd)
        ret = call(bash_network_cmd)
        if ret != 0:
            if ret < 0:
                logging.info(command + "on port" + str(changing_status_ports) + "failed")
            else:
                logging.info("Failed to get RC of " + str(changing_status_ports))

def host_sanity(hostname):
    response = os.system("ping -c 3 " + host)
    if response != 0:
        print hostname, "is down! Will exit! "
        sys.exit()

def randomize_port(port_list, always_up_ports):
    num_of_ports = len(port_list)
    port_manipul = rchoice(range(int(num_of_ports) - always_up_ports))
    port_manipul = port_manipul + 1
    print port_manipul
    chosen_ports = random.sample(set(ctr_ip), port_manipul)
    return(chosen_ports)

host_list = find_hosts(host_file)
sleep_timer = (random.randint(60, 300))
chosen_ports = randomize_port(ctr_ip,always_up_ports)
# num_of_ports = len(ctr_ip)
# port_manipul = rchoice(range(num_of_ports - 1))
# port_manipul = port_manipul + 1
# print port_manipul
# chosen_ports = random.sample(set(ctr_ip), port_manipul)
print time.strftime("%H:%M:%S")
print "will turn down {0} ports".format(chosen_ports)
#turn_ctr_port('ifdown', chosen_ports)
#time.sleep(sleep_timer)
#turn_ctr_port('ifup', chosen_ports)
#time.sleep(sleep_timer)
host_list.remove('\n')
for host in host_list:
    host.splitlines()
    host_sanity(host)
    root_host = "root@" + host
    data_ports = find_host_ports(root_host)
    print data_ports
    turn_port_host(root_host, 'hostname', data_ports)

