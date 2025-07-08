# FixPlayActivity
Remove extra records from play_activity on Miyoo Mini Onion OS.

## How it works
As of Onion 4.3.1-1, Activity Tracker will sometimes begin to indicate much higher playtime for games than users have actually played.  These can be fixed by removing certain records in the `play_activity_db.sqlite` file:  when these incidents occur, they happen due to sessions having erroneous records at duplicate `updated_at` timestamps.

This script performs a check for these records, returns those to the user, and then allows the user to backup the original db file, and remove the duplicate `updated_at` records.  If no duplicate records are found, the execute script will not run.

Version 1.1 also adds a TIMELIMIT variable, which will delete any `play_time` records above a certain TIMELIMIT.txt in seconds, or default to 3 hours if the file is missing.  If you are used to playing for longer sessions without breaking (turning off the Miyoo or using GameSwitcher) you may increase this value.

## Installation and usage

Place the entire `FixPlayActivity` folder inside the `App` folder in your SD Card.  Then, to the Apps menu on your Miyoo Mini/Plus running OnionOS, and run the FixPlayActivity app.

> [!WARNING]
> The script will backup your `play_activity_db.sqlite` file inside the same directory before making changes.  You may still want to make a backup if you're unsure; this has only been tested on 4.3.1-1

The script will run.  If problem records are found, you can press the UP key when prompted to run the removal script, or any other key to exit.  A backup `play_activity_db_bak.sqlite` will be created before making changes.

## Not a perfect solve

Unfortunately, the best way to scrub bad records would be to look at the `updated_at` times.  They should always increase and outliers shouldn't exist, where the next record has a lower value.  However, since the Miyoo uses the clock to record this value, and the clock is subject to reset if the battery is removed, or the time changes, these sessions might have irregular values and it's impossible to preserve valid playsessions if the outliers are removed.  There is a real change some bad records might still exist in smaller `play_time` units.