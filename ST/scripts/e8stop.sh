#!/bin/bash
/opt/E8/extra/stop_services.sh
rmmod nvme
insmod /usr/lib/modules/`uname -r`/kernel/drivers/block/nvme.ko
