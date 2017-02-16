import time
from fabric.contrib.files import *
from fabric.api import *
import tempfile
from fabric.contrib import *
import config
import json
from collections import OrderedDict

@roles("controllers")
def _get_data_interfaces():
    interfaces = dict()
    data ={}
    with hide('everything'):
        ibdev = run("ibdev2netdev")
        for line in ibdev.splitlines():
            m = re.search(r"==> (\w+) \((\w+)\)", line)
            if m:
                interfaces.setdefault(m.group(1), {})["state"] = m.group(2).lower()
        for interface in interfaces:
            ips = run("ip addr show dev %s" % interface)
            for line in ips.splitlines():
                m = re.search(r"inet (\d+\.\d+\.\d+\.\d+\(?)", line)
                if m:
                    interfaces[interface].setdefault("ips", []).append(m.group(1))
                    data[interface]=m.group(1)

    return data
    #return interfaces


@roles("all")
def print_data_ports():
    """
     - Print data ports and their IPs
    """
    interfaces = _get_data_interfaces()

    print"\n"
    print "##############  {0}  ##############".format(env.host)
    for interface, info in interfaces.iteritems():
        print interface
        print info.get("ips", [])