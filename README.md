# FixPlayActivity
Remove extra records from play_activity on Miyoo Mini Onion OS.

## How it works
As of Onion 4.3.1-1, Activity Tracker will sometimes begin to indicate much higher playtime for games than users have actually played.  These can be fixed by removing certain records in the `play_activity_db.sqlite` file: when these incidents occur, they happen due to sessions having erroneous records at duplicate `updated_at` timestamps.

This script performs a check for these records, returns those to the user, and then allows the user to backup the original db file and remove the duplicate `updated_at` records.  If no duplicate records are found, the execute script will not run.

Version 1.1 also adds a TIMELIMIT variable, which will delete any `play_time` records above a certain TIMELIMIT.txt in seconds, or default to 3 hours if the file is missing.  If you are used to playing for longer sessions without breaking (turning off the Miyoo or using GameSwitcher) you may increase this value.

Version 1.2 will track your database between each run and begin performing anomaly checks first:  specifically, if any `updated_at` values end up higher than a following record.  This shouldn't happen unless the Miyoo RTC falls back, or the battery is pulled and clock reset.  The last `rowid` is writted in a LASTROW.txt file in the app folder.

## Installation and usage

Place the entire `FixPlayActivity` folder inside the `App` folder in your SD Card.  Then, to the Apps menu on your Miyoo Mini/Plus running OnionOS, and run the FixPlayActivity app.

> [!WARNING]
> Do not rename the folder.  It should be `FixPlayActivity` inside the `App` folder.  Any other folder/filename path will not work.

> [!TIP]
> The script will backup your `play_activity_db.sqlite` file inside the same directory before making changes.  You may still want to make a backup if you're unsure; this has only been tested on 4.3.1-1

The script will run.  If problem records are found, you can press the UP key when prompted to run the removal script, or any other key to exit.  A backup `play_activity_db_bak.sqlite` will be created before making changes.

## Not a perfect solve

Unfortunately, the best way to scrub bad records would be to look at the `updated_at` times.  They should always increase and outliers shouldn't exist, where the next record has a lower value.  However, since the Miyoo uses the clock to record this value, and the clock is subject to reset if the battery is removed, or the time changes, these sessions might have irregular values and it's impossible to preserve valid playsessions if the outliers are removed.  There is a real chance some bad records might still exist in smaller `play_time` units.

This script addresses this issue by only checking against these anomalies after it's first run, since we assume that there may be lots of out-of-order records prior to establishing the RTC or clock setup.

> [!TIP]
> If you're confident your clock has always been set correctly since day 1, you can set the value in the LASTROW.txt file to '1' and it will run a check against all your history; you can still skip the removal when prompted.

### Script info

OnionOS uses a non-standard installation of Python, specifically 2.7, as of `4.3.1-1`.
The script launches from the OS, feeds a stepper script into the OnionOS terminal emulator `st` which then runs the `py` scripts with user input in the terminal.
I used Claude AI to generate most of the Python and `sh` shell scripts here, and modified accordingly, but there may be some extra operations or unnecessary bulk that could be removed.
