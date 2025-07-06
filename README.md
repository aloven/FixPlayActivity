# FixPlayActivity
Remove extra records from play_activity on Miyoo Mini Onion OS.

## How it works
As of Onion 4.3.1-1, Activity Tracker will sometimes begin to indicate much higher playtime for games than users have actually played.  These can be fixed by removing certain records in the `play_activity_db.sqlite` file:  when these incidents occur, they happen due to sessions having erroneous records at duplicate `updated_at` timestamps.

This script performs a check for these records, returns those to the user, and then allows the user to backup the original db file, and remove the duplicate `updated_at` records.  If no duplicate records are found, the execute script will not run.

## Installation and usage

Place the entire `FixPlayActivity` folder inside the `App` folder in your SD Card.  Then, to the Apps menu on your Miyoo Mini/Plus running OnionOS, and run the FixPlayActivity app.

> [!WARNING]
> The script will backup your `play_activity_db.sqlite` file inside the same directory before making changes.  You may still want to make a backup if you're unsure; this has only been tested on 4.3.1-1

The script will run.  If problem records are found, you can press the UP key when prompted to run the removal script, or any other key to exit.  A backup `play_activity_db_bak.sqlite` will be created before making changes.
