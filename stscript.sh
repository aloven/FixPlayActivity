#!/bin/sh

dbdir=/mnt/SDCARD/Saves/CurrentProfile/play_activity
appdir=/mnt/SDCARD/App/FixPlayActivity
sysdir="/mnt/SDCARD/.tmp_update/bin/parasyte"
PYTHONHOME=$sysdir
PYTHONPATH=/mnt/SDCARD/.tmp_update/lib/parasyte/python2.7:/mnt/SDCARD/.tmp_update/lib/parasyte/python2.7/lib-dynload
export PYTHONHOME PYTHONPATH

# Read TIMELIMIT from file and export as environment variable
if [ -f "TIMELIMIT.txt" ]; then
    TIMELIMIT=$(cat TIMELIMIT.txt)
    export TIMELIMIT
else
    echo "Warning: TIMELIMIT.txt not found.  Script will default to 10800 (3 hours)"
fi

echo -e "Running dry run python script...\n"

cmd="$sysdir/python2.7 $appdir/sqlite_duplicate_cleanup.py $dbdir/play_activity_db.sqlite play_activity"

output=$($cmd 2>&1 | tee /dev/tty)

case "$output" in
    *code123*)
        echo
        echo "Press UP arrow to continue, any other key to exit..."
        
        # Save current terminal settings
        old_stty=$(stty -g)
        
        # Set terminal to raw mode for single character input
        stty raw -echo
        
        # Read first character
        key1=$(dd bs=1 count=1 2>/dev/null)
        
        # If first character is ESC, read the next two characters
        if [ "$(printf '%d' "'$key1")" = "27" ]; then
            key2=$(dd bs=1 count=1 2>/dev/null)
            key3=$(dd bs=1 count=1 2>/dev/null)
            
            # Check if it's the up arrow sequence: ESC + [ + A
            if [ "$key2" = "[" ] && [ "$key3" = "A" ]; then
                # Restore terminal settings
                stty $old_stty
                echo
                echo -e "Backing up play_activity_db...\n"
                cp $dbdir/play_activity_db.sqlite $dbdir/play_activity_db_bak.sqlite
                echo "executing python script..."
                $sysdir/python2.7 $appdir/sqlite_duplicate_cleanup.py $dbdir/play_activity_db.sqlite play_activity --execute
            else
                # Restore terminal settings
                stty $old_stty
                echo
                echo "Exiting..."
                exit 0
            fi
        else
            # Restore terminal settings
            stty $old_stty
            echo
            echo "Exiting..."
            exit 0
        fi
        ;;
esac

read -n 1 -s -r -p "Press any key to exit..."
