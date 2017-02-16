# Registered name of driver
name=PlxSvc

# Name of module
module=$name

# Probe for a loaded conflicting driver
drv_Name=`lsmod | awk "\\$1==\"$name\" {print \\$1}"`
if [ "$drv_Name" = "" ]; then
    drv_Name=`lsmod | awk "\\$1==\"${name}_dbg\" {print \\$1}"`
fi

echo Install: $module

echo -n "  Load module......... "
# Check if conflicting driver already loaded
if [ "$drv_Name" != "" ]; then
    echo "ERROR: '$drv_Name' conflicts & already loaded"
    echo
    exit
fi

# Verify driver file exists
if [ ! -f $module.ko ]; then
    echo "ERROR: Driver not built or invalid path"
    echo "    \-- $module.ko"
    echo
    exit
fi

# Load module
if insmod $module.ko 2>/dev/null; then
    echo "Ok "
else
    echo ERROR: Load error or no supported devices found
    exit
fi

# Verify driver loaded
echo -n "  Verify load......... "
drv_Name=`lsmod | awk "\\$1==\"$module\" {print \\$1}"`
if [ "$drv_Name" = "" ]; then
    echo ERROR: \'$module\' not detected
    echo
    exit
fi
echo Ok

# Get the major number
echo -n "  Get major number.... "
major=`cat /proc/devices | awk "\\$2==\"$name\" {print \\$1}"`

# Check if valid
if [ "$major" = "" ]; then
    echo ERROR: Module major number not detected
    echo
    exit
fi

# Display Major ID
echo "Ok (MajorID = $major)"

# Create the device node path
path=/dev/plx
echo -n "  Create node path.... "
if [ -d $path ]; then
    echo "Ok ($path already exists)"
else
    mkdir $path
    chmod 0777 $path
    echo "Ok ($path)"
fi

# Create the device nodes
echo -n "  Create nodes........ "
rm -f $path/$name*
mknod $path/$name c $major 255

chmod 777 $path/*
echo "Ok ($path/$name)"
echo
