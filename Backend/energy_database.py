"""
Energy Database Module
This module handles SQLite operations for wind and solar energy statistics.
"""
import json
import os
import sqlite3
import pandas as pd


class EnergyDatabase:
    """
    EnergyDatabase is responsible for storing wind and solar energy data
    into an SQLite database with specific tables for each energy source.
    """

    def __init__(self, db_name="energy_data_v2 [2].db"):
        """
        Initializes the database name and prepares the database schema.
        :param db_name: Name of the SQLite database file.
        """
        self.db_name = db_name
        self.setup_db()

    def setup_db(self):
        """
        Prepares the SQLite database by creating required tables if they don't exist.
        Initializes 'wind_energy_stats' and 'solar_energy_stats' with a common schema.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Define common table schema for both energy types
        table_schema = '''
                       (
                           id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                           full_date               TEXT UNIQE,
                           expected_best           REAL,
                           expected_worst          REAL,
                           total_hourly_real       REAL
                       )
                       '''

        # Create Wind Energy Table
        cursor.execute(f'CREATE TABLE IF NOT EXISTS wind_energy_stats {table_schema}')

        # Create Solar Energy Table
        cursor.execute(f'CREATE TABLE IF NOT EXISTS solar_energy_stats {table_schema}')

        # Create indexes for optimized time-based queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wind_time ON '
                       'wind_energy_stats (full_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_solar_time ON '
                       'solar_energy_stats (full_date)')

        conn.commit()
        conn.close()
        print(f"Database setup successful: Tables are ready in {self.db_name}")

    def store_json_to_sql(self, json_file_path, table_name):
        """
        Reads energy data from a JSON file and appends it to the specified SQL table.
        :param json_file_path: Path to the source JSON file.
        :param table_name: Target database table name.
        """
        if not os.path.exists(json_file_path):
            print(f"Error: {json_file_path} not found!")
            return

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                print(f"Error: JSON root in {json_file_path} must be a list.")
                return

            df = pd.DataFrame(data)

            # Mapping JSON keys to Database column names
            name_mapping = {
                "Full Date": "full_date",
                "EXPECTED - BEST": "expected_best",
                "EXPECTED - WORST": "expected_worst",
                "Total Hourly Energy (REAL)": "total_hourly_real"
            }
            df = df.rename(columns=name_mapping)

            # Selecting only the required columns defined in the schema
            final_columns = ['full_date', 'expected_best', 'expected_worst', 'total_hourly_real']

            # Filter and reorder columns to match DB schema
            df = df[final_columns]

            conn = sqlite3.connect(self.db_name)
            # Append data to the specific table
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            conn.commit()
            conn.close()
            print(f"Success: {len(df)} rows from '{json_file_path}' inserted into '{table_name}'.")

        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Data storage error for table '{table_name}': {e}")


if __name__ == "__main__":
    # Create the database instance
    db = EnergyDatabase()

    # 1. Store wind data in wind_energy_stats table
    db.store_json_to_sql('complete_wind_records.json', 'wind_energy_stats')

    # 2. Store solar data in solar_energy_stats table
    db.store_json_to_sql('complete_solar_records.json', 'solar_energy_stats')
