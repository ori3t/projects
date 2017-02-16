# Registered name of driver
name=PlxSvc

# Name of module
module=$name


echo
echo Remove: $module

# Get module load status
drv_Name=`lsmod | awk "\\$1==\"$module\" {print \\$1}"`

echo -n "  Unload module....... "
if [ "$drv_Name" = "" ]; then
    echo ERROR: \'$module\' not loaded
    echo
    exit
fi

# Generate temp file name
TmpFile=/tmp/_Plx_Rmmod_$module.tmp

# Remove module & capture output
rmmod $module 2> $TmpFile
Rm_mod=`cat $TmpFile | grep 'ERROR'`

# Check for error
if [ "$Rm_mod" != "" ]; then
    echo ERROR: Unable to remove module
    echo "      \-- Msg: `cat $TmpFile`"
    echo
    rm $TmpFile
    exit
else
    echo "Ok ($module)"
    rm $TmpFile
fi

echo -n "  Clear nodes......... "
path=/dev/plx
rm -f $path/$name*
echo "Ok ($path/$name)"

# Delete the directory only if empty
if [ -d $path ]; then
    echo -n "  Delete node path.... "
    rmdir --ignore-fail-on-non-empty ${path}
    echo "Ok ($path)"
fi
echo
