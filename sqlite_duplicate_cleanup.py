#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os
import argparse

def find_and_delete_duplicates(db_path, table_name, time_limit, dry_run=True):
    """
    Find records with duplicate updated_at values and delete those with larger play_time values.
    Also delete any records with play_time > time_limit.
    
    Args:
        db_path (str): Path to the SQLite database file
        table_name (str): Name of the table to process
        time_limit (int): Delete records with play_time greater than this value
        dry_run (bool): If True, only show what would be deleted without actually deleting
    """
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print("Error: Database file '{}' not found.".format(db_path))
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First, find records with play_time > time_limit
        high_playtime_query = """
        SELECT rowid, updated_at, play_time
        FROM {table_name}
        WHERE play_time > ?
        ORDER BY play_time DESC
        """.format(table_name=table_name)
        
        cursor.execute(high_playtime_query, (time_limit,))
        high_playtime_records = cursor.fetchall()
        
        records_to_delete = []
        
        if high_playtime_records:
            print("Found {} records with play_time > {}:".format(len(high_playtime_records), time_limit))
            for record in high_playtime_records:
                print("  rowid={}, updated_at={}, play_time={}".format(record[0], record[1], record[2]))
                records_to_delete.append(record[0])
        else:
            print("No records found with play_time > {}.".format(time_limit))
        
        # Then, find all duplicate updated_at values
        find_duplicates_query = """
        SELECT updated_at, COUNT(*) as count
        FROM {table_name}
        GROUP BY updated_at
        HAVING COUNT(*) > 1
        ORDER BY updated_at
        """.format(table_name=table_name)
        
        cursor.execute(find_duplicates_query)
        duplicates = cursor.fetchall()
        
        if not duplicates:
            print("\nNo duplicate updated_at values found.")
        else:
            print("\nFound {} updated_at values with duplicates:".format(len(duplicates)))
            for updated_at, count in duplicates:
                print("  updated_at: {} (appears {} times)".format(updated_at, count))
        
        # For each duplicate updated_at, find records to delete (keep the one with smallest play_time)
        # But skip records that are already marked for deletion due to high play_time
        
        for updated_at, _ in duplicates:
            # Get all records for this updated_at, ordered by play_time
            get_records_query = """
            SELECT rowid, updated_at, play_time
            FROM {table_name}
            WHERE updated_at = ?
            ORDER BY play_time ASC
            """.format(table_name=table_name)
            
            cursor.execute(get_records_query, (updated_at,))
            records = cursor.fetchall()
            
            # Filter out records that are already marked for deletion
            remaining_records = [r for r in records if r[0] not in records_to_delete]
            
            # Keep the first one (smallest play_time), mark the rest for deletion
            if len(remaining_records) > 1:
                records_to_keep = remaining_records[0]
                records_to_remove = remaining_records[1:]
                
                print("\nFor updated_at '{}':".format(updated_at))
                print("  Keeping: rowid={}, play_time={}".format(records_to_keep[0], records_to_keep[2]))
                print("  Deleting {} duplicate record(s):".format(len(records_to_remove)))
                
                for record in records_to_remove:
                    print("    rowid={}, play_time={}".format(record[0], record[2]))
                    records_to_delete.append(record[0])
            elif len(records) > 1 and len(remaining_records) <= 1:
                # All but one (or all) records were already marked for deletion due to high play_time
                already_deleted = len(records) - len(remaining_records)
                print("\nFor updated_at '{}':".format(updated_at))
                print("  {} record(s) already marked for deletion due to play_time > {}".format(already_deleted, time_limit))
                if remaining_records:
                    print("  Keeping: rowid={}, play_time={}".format(remaining_records[0][0], remaining_records[0][2]))
        
        if not records_to_delete:
            print("\nNo records need to be deleted.")
            return
        
        print("\nSUMMARY:")
        print("Total records to delete: {}".format(len(records_to_delete)))
        print("  - Records with play_time > {}: {}".format(time_limit, len(high_playtime_records)))
        print("  - Duplicates (keeping smallest play_time): {}".format(len(records_to_delete) - len(high_playtime_records)))
        
        if dry_run:
            print("\n*** DRY RUN MODE - No records were deleted ***")
            print("Run with --execute to perform the actual deletion.")
        else:
            # Perform the deletion
            placeholders = ','.join(['?' for _ in records_to_delete])
            delete_query = "DELETE FROM {table_name} WHERE rowid IN ({placeholders})".format(
                table_name=table_name, placeholders=placeholders)
            
            cursor.execute(delete_query, records_to_delete)
            conn.commit()
            
            print("\n*** DELETED {} records ***".format(len(records_to_delete)))
            
            # Verify the cleanup
            cursor.execute(find_duplicates_query)
            remaining_duplicates = cursor.fetchall()
            
            if remaining_duplicates:
                print("Warning: {} duplicate updated_at values still remain.".format(len(remaining_duplicates)))
            else:
                print("All duplicates have been successfully removed.")
    
    except sqlite3.Error as e:
        print("SQLite error: {}".format(e))
    except Exception as e:
        print("Error: {}".format(e))
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Find and delete duplicate records in SQLite database')
    parser.add_argument('database_path', help='Path to the SQLite database file')
    parser.add_argument('table_name', help='Name of the table to process')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually delete records (default is dry-run mode)')
    
    args = parser.parse_args()
    
    # Get time limit from environment variable, default to 10800 if not set
    time_limit = int(os.environ.get('TIMELIMIT', '10800'))
    
    print("SQLite Duplicate Record Cleanup Script")
    print("=" * 50)
    print("Database: {}".format(args.database_path))
    print("Table: {}".format(args.table_name))
    print("Time Limit: {}".format(time_limit))
    print("Mode: {}".format('EXECUTE' if args.execute else 'DRY RUN'))
    print("=" * 50)
    
    if args.execute:
        print("Running in EXECUTION mode - records will be deleted!")
        find_and_delete_duplicates(args.database_path, args.table_name, time_limit, dry_run=False)
    else:
        print("Running in DRY RUN mode - no records will be deleted")
        find_and_delete_duplicates(args.database_path, args.table_name, time_limit, dry_run=True)

if __name__ == "__main__":
    main()