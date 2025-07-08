#!/usr/bin/env python
"""
SQLite Bad Records Finder

This script finds and optionally removes outlier records in a SQLite database
where updated_at values are not in sequential order.

Compatible with Python 2.7+
"""

import sqlite3
import argparse
import sys
import os
from datetime import datetime


def connect_to_db(db_path):
    """Connect to SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except sqlite3.Error as e:
        print("Error connecting to database: {}".format(e))
        sys.exit(1)


def validate_table_exists(conn, table_name):
    """Check if the specified table exists."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def validate_updated_at_column(conn, table_name):
    """Check if updated_at column exists in the table."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info({})".format(table_name))
    columns = [column[1] for column in cursor.fetchall()]
    return 'updated_at' in columns


def get_primary_key_column(conn, table_name):
    """Get the primary key column name for the table."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info({})".format(table_name))
    columns = cursor.fetchall()
    
    for column in columns:
        if column[5] == 1:  # column[5] is the pk field
            return column[1]
    
    # If no primary key found, assume 'id' or 'rowid'
    column_names = [col[1] for col in columns]
    if 'id' in column_names:
        return 'id'
    else:
        return 'rowid'


def read_last_row():
    """Read the last processed row number from LASTROW environment variable or LASTROW.txt."""
    # First try to read from environment variable
    try:
        lastrow_env = os.environ.get('LASTROW')
        if lastrow_env and lastrow_env.isdigit():
            return int(lastrow_env)
    except:
        pass
    
    # Fall back to reading from LASTROW.txt
    try:
        if os.path.exists("LASTROW.txt"):
            with open("LASTROW.txt", "r") as f:
                content = f.read().strip()
                if content.isdigit():
                    return int(content)
        return 0  # Start from beginning if neither source exists or is invalid
    except:
        return 0



def get_max_row_number(conn, table_name, pk_column):
    """Get the maximum row number (primary key) from the table."""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX({}) FROM {}".format(pk_column, table_name))
    result = cursor.fetchone()
    return result[0] if result[0] is not None else 0


def find_bad_records(conn, table_name, pk_column, start_row=0):
    """
    Find records where updated_at is greater than the next record's updated_at.
    Only checks records starting from start_row.
    Returns list of tuples (primary_key, updated_at) for bad records.
    """
    cursor = conn.cursor()
    
    # Query to find records where current updated_at > next updated_at
    # Only check records starting from start_row
    query = """
        SELECT 
            current.{pk} as current_pk,
            current.updated_at as current_updated_at,
            next.{pk} as next_pk,
            next.updated_at as next_updated_at
        FROM {table} current
        LEFT JOIN {table} next ON next.{pk} = (
            SELECT MIN({pk}) 
            FROM {table} 
            WHERE {pk} > current.{pk}
        )
        WHERE current.{pk} >= ?
        AND next.{pk} IS NOT NULL 
        AND current.updated_at > next.updated_at
        ORDER BY current.{pk}
    """.format(pk=pk_column, table=table_name)
    
    try:
        cursor.execute(query, (start_row,))
        results = cursor.fetchall()
        
        bad_records = []
        for row in results:
            bad_records.append((row['current_pk'], row['current_updated_at']))
            
        return bad_records
        
    except sqlite3.Error as e:
        print("Error querying database: {}".format(e))
        sys.exit(1)


def get_record_details(conn, table_name, pk_column, pk_value):
    """Get full record details for a given primary key."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM {} WHERE {} = ?".format(table_name, pk_column), (pk_value,))
    row = cursor.fetchone()
    return dict(row) if row else {}


def remove_bad_records(conn, table_name, pk_column, bad_records):
    """Remove bad records from the database."""
    cursor = conn.cursor()
    removed_count = 0
    
    try:
        for pk_value, _ in bad_records:
            cursor.execute("DELETE FROM {} WHERE {} = ?".format(table_name, pk_column), (pk_value,))
            if cursor.rowcount > 0:
                removed_count += 1
        
        conn.commit()
        return removed_count
        
    except sqlite3.Error as e:
        print("Error removing records: {}".format(e))
        conn.rollback()
        sys.exit(1)


def format_timestamp(timestamp):
    """Format Unix timestamp for display."""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(timestamp)


def main():
    parser = argparse.ArgumentParser(
        description="Find and optionally remove bad records in SQLite database where updated_at values are not sequential"
    )
    parser.add_argument("path_to_db", help="Path to the SQLite database file")
    parser.add_argument("table_name", help="Name of the table to check")
    parser.add_argument("--execute", action="store_true", help="Execute removal of bad records (default: dry run)")
    
    args = parser.parse_args()
    
    # Connect to database
    conn = connect_to_db(args.path_to_db)
    
    try:
        # Validate table exists
        if not validate_table_exists(conn, args.table_name):
            print("Error: Table '{}' does not exist in the database.".format(args.table_name))
            sys.exit(1)
        
        # Validate updated_at column exists
        if not validate_updated_at_column(conn, args.table_name):
            print("Error: Column 'updated_at' does not exist in table '{}'.".format(args.table_name))
            sys.exit(1)
        
        # Get primary key column
        pk_column = get_primary_key_column(conn, args.table_name)
        print("Using '{}' as primary key column.".format(pk_column))
        
        # Read starting row from LASTROW.txt
        start_row = read_last_row()
        print("Starting analysis from row {} read from LASTROW.txt".format(start_row))
        
        # Find bad records
        print("\nAnalyzing table '{}' for sequential updated_at violations...".format(args.table_name))
        bad_records = find_bad_records(conn, args.table_name, pk_column, start_row)
        
        if not bad_records:
            print("✓ No bad records found. All updated_at values are in sequential order.")
        else:
            print("Found {} bad record(s):".format(len(bad_records)))
            print("-" * 80)
            
            # Display bad records
            for pk_value, updated_at in bad_records:
                record_details = get_record_details(conn, args.table_name, pk_column, pk_value)
                print("Record {}={}: updated_at={} ({})".format(
                    pk_column, pk_value, updated_at, format_timestamp(updated_at)
                ))
            
            # Execute removal if requested
            if args.execute:
                print("Removing bad records...")
                removed_count = remove_bad_records(conn, args.table_name, pk_column, bad_records)
                print("*** Successfully removed {} bad record(s). ***".format(removed_count))
            else:
                print("*** Dry run complete. No records were removed. ***")
        
            
    finally:
        conn.close()


if __name__ == "__main__":
    main()