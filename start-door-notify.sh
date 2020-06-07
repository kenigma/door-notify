#!/bin/sh

check_process() {
    # check the args
    if [ "$1" = "" ];
    then
        return 0
    fi

    PROCESS_NUM=$(ps -ef | grep "$1" | grep -v "grep" | wc -l)
    if [ $PROCESS_NUM -eq 1 ];
    then
        return 1
    else
        return 0
    fi
}

check_process "door-notify.py"

if [ $? -eq 1 ];
then
    echo "`date +%F.%T` Process already running, quitting now."
else
    echo "`date +%F.%T` Process not running, starting it now..."
    /home/pi/projects/door-notify/door-notify.py > /dev/null 2>&1 &
    echo "`date +%F.%T` Started"
fi
