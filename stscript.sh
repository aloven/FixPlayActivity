#!/bin/sh

dbdir=/mnt/SDCARD/Saves/CurrentProfile/play_activity
appdir=/mnt/SDCARD/App/FixPlayActivity
sysdir="/mnt/SDCARD/.tmp_update/bin/parasyte"
pythonbin="/python2.7"
pythonrun=$sysdir$pythonbin
PYTHONHOME=$sysdir
APPDIR=$appdir
PYTHONPATH=/mnt/SDCARD/.tmp_update/lib/parasyte/python2.7:/mnt/SDCARD/.tmp_update/lib/parasyte/python2.7/lib-dynload
export PYTHONHOME PYTHONPATH APPDIR

# Check for LASTROW file and export as environment variable.  Run anomaly script if file exists.
if [ -f "$appdir/LASTROW.txt" ]; then
    LASTROW=$(cat $appdir/LASTROW.txt)
    export LASTROW
    # run the anomaly detection script
    echo -e "*** Running anomaly detection script (DRY RUN)...\n"
    cmd="$sysdir/python2.7 $appdir/anomaly_detection.py $dbdir/play_activity_db.sqlite play_activity"
    output=$($cmd 2>&1 | tee /dev/tty)

    case "$output" in
        *"bad record(s)"*)
            
            echo
            echo " * May remove legitimate records if you have not run"
            echo " * this script before and/or changed the Miyoo clock"
            echo
            echo " * If you are unsure, you can skip this and"
            echo " * proceed to next cycle which will attempt a fix."
            echo
            echo "-=-=- Press UP to execute, other key skips -=-=-"
            
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
                    echo -e "*** Backing up database to play_activity_db.bak.sqlite...\n"
                    cp $dbdir/play_activity_db.sqlite $dbdir/play_activity_db_bak.sqlite
                    backup=0
                    echo "*** Running anomaly detection script (EXECUTE)...\n"
                    $cmd --execute
                else
                    # Restore terminal settings
                    stty $old_stty
                    echo
                    echo "Skipping anomaly purge."
                fi
            else
                # Restore terminal settings
                stty $old_stty
                echo
                echo "Skipping anomaly purge."
            fi
            ;;
    esac
    
else
    echo "Warning: LASTROW.txt not found.  Skipping anomaly detection script."
    echo "This is normal for first-time run.  Going forward, this file will be created and used to detect anomalies in the running database."
fi


# Read TIMELIMIT from file and export as environment variable
if [ -f "$appdir/TIMELIMIT.txt" ]; then
    TIMELIMIT=$(cat $appdir/TIMELIMIT.txt)
    export TIMELIMIT
else
    echo "Warning: TIMELIMIT.txt not found.  Script will default to 10800 (3 hours)"
fi

echo -e "*** Running duplicate detection script (DRY RUN)...\n"

cmd="$pythonrun $appdir/sqlite_duplicate_cleanup.py $dbdir/play_activity_db.sqlite play_activity"

output=$($cmd 2>&1 | tee /dev/tty)

case "$output" in
    *"Total records to delete"*)
        echo
        echo "-=-=- Press UP to delete, other key exits -=-=-"
        
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
                if [ "$backup" -eq 1 ]; then
                    echo -e "*** Backing up database to play_activity_db.bak.sqlite...\n"
                    cp $dbdir/play_activity_db.sqlite $dbdir/play_activity_db_bak.sqlite
                else
                    echo -e "Backup already exists. proceeding with script..\n"
                fi
                
                echo "*** Running duplicate detection script (EXECUTE)...\n"
                $pythonrun $appdir/sqlite_duplicate_cleanup.py $dbdir/play_activity_db.sqlite play_activity --execute
            else
                # Restore terminal settings
                stty $old_stty
                echo
                echo "Exiting..."
                echo
                exit 0
            fi
        else
            # Restore terminal settings
            stty $old_stty
            echo
            echo "Exiting..."
            echo
            exit 0
        fi
        ;;
esac

read -n 1 -s -r -p "-=-=- Press any key to exit -=-=-"
echo
