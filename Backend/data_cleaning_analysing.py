"""
Energy Analysis Module.

This module processes weather and energy data to calculate and shape
wind and solar energy predictions, exporting the results to JSON files.
"""

import json
import glob
import numpy as np
import pandas as pd
from pandas import DataFrame

# --- Constants ---
WIND_SCALER_BEST = 1
WIND_SCALER_WORST = 1
SOLAR_SCALER_BEST = 1
SOLAR_SCALER_WORST = 1

AIR_DENSITY = 1.225
TURBINE_EFF = 0.4
SOLAR_PANEL_EFF = 0.18
PERF_RATE = 0.75
GAMMA = 0.0045

WIND_CITIES = {
    "İzmir": 0.38,
    "Balıkesir": 0.285,
    "Çanakkale": 0.18,
    "Manisa": 0.155
}

SOLAR_CITIES = {
    "Konya": 0.44,
    "Ankara": 0.2,
    "Şanlıurfa": 0.19,
    "Kayseri": 0.17
}


def solar_shaper(df: DataFrame, target_col: str, reference_col: str,
                 tolerance: float = 1.05, is_best: bool = False) -> DataFrame:
    """
    Adjusts solar energy predictions based on a reference column and tolerance.
    """
    too_high = df[target_col] > (df[reference_col] * tolerance)
    df[target_col] = np.where(too_high, df[reference_col] * tolerance, df[target_col])

    if is_best:
        too_low = df[target_col] < df[reference_col]
        df[target_col] = np.where(too_low, df[reference_col], df[target_col])

    df[target_col] = df[target_col].clip(lower=0)
    return df


def energy_shaper(df: DataFrame, target_col: str, reference_col: str,
                  tolerance: float = 1.2, is_best: bool = False) -> DataFrame:
    """
    Adjusts wind energy predictions with a minimum floor based on base load.
    """
    too_high = df[target_col] > (df[reference_col] * tolerance)
    df[target_col] = np.where(too_high, df[reference_col] * tolerance, df[target_col])

    if is_best:
        too_low = df[target_col] < df[reference_col]
        df[target_col] = np.where(too_low, df[reference_col], df[target_col])

    df[target_col] = df[target_col].clip(lower=df[reference_col].min())
    return df


def wind_pivot_creator(df: DataFrame) -> DataFrame:
    """
    Creates a pivot table for wind energy and calculates total weighted energy.
    """
    df_temp = df.reset_index()
    df_filtered = df_temp[df_temp['address'].isin(WIND_CITIES.keys())]
    wind_pivot1 = df_filtered.pivot(index='Full Date', columns='address',
                                    values='RAW WIND ENERGY')

    city_wind_weights = np.array([WIND_CITIES[city] for city in wind_pivot1.columns])

    # Calculate weighted sum
    wind_pivot1["Total Hourly Energy (RAW)"] = np.dot(wind_pivot1.values, city_wind_weights)
    # Convert to appropriate unit (e.g., MW)
    wind_pivot1["Total Hourly Energy (RAW)"] = np.true_divide(
        wind_pivot1['Total Hourly Energy (RAW)'].values, 1000000
    )
    return wind_pivot1


def convert_units(df1: DataFrame) -> DataFrame:
    """
    Converts temperature to Celsius, wind speed to m/s, and merges datetime columns.
    """
    # Fahrenheit to Celsius
    df1['temp_c'] = (df1['temp'] - 32) * 5 / 9
    # MPH to M/S
    df1['windspeed_ms'] = df1['windspeed'] * 0.44704
    # Merging datetime day-hour
    df1['Full Date'] = pd.to_datetime(df1['days.datetime'] + ' ' + df1['datetime'])

    deleted_columns1 = ['days.datetime', 'datetime', 'windspeed', 'temp']
    df1.drop(deleted_columns1, inplace=True, axis=1)
    return df1


def dynamic_efficiency(vel: float) -> float:
    """
    Calculates turbine efficiency based on wind velocity.
    """
    if vel < 3:
        return 0
    if vel > 25:
        return 0
    if vel >= 12:
        return TURBINE_EFF * (12 / vel) ** 3
    return TURBINE_EFF


# Vectorize the function for performance on Pandas Series
v_eff = np.vectorize(dynamic_efficiency)


def raw_wind_energy_cal(df: DataFrame) -> None:
    """
    Calculates raw wind energy based on wind speed and efficiency.
    Modifies the DataFrame in-place.
    """
    vel = df['windspeed_ms']
    calculation_part = (vel ** 3) * AIR_DENSITY * v_eff(vel)
    df['RAW WIND ENERGY'] = np.where(((vel > 0.1) & (vel < 25)), calculation_part, 0)


def raw_solar_energy_cal(df: DataFrame) -> None:
    """
    Calculates raw solar energy based on radiation and temperature loss.
    Modifies the DataFrame in-place.
    """
    df['RAW SOLAR ENERGY'] = (
            df['solarradiation'] * SOLAR_PANEL_EFF * PERF_RATE *
            (1 - GAMMA * (df['temp_c'] - 25))
    )


def solar_pivot_creator(df: DataFrame) -> DataFrame:
    """
    Creates a pivot table for solar energy and calculates total weighted energy.
    """
    df_temp = df.reset_index()
    df_filtered = df_temp[df_temp['address'].isin(SOLAR_CITIES.keys())]
    solar_pivot1 = df_filtered.pivot(index='Full Date', columns='address',
                                     values='RAW SOLAR ENERGY')

    city_solar_weights = np.array([SOLAR_CITIES[city] for city in solar_pivot1.columns])

    # Calculate weighted sum
    solar_pivot1["Total Hourly Energy (RAW)"] = np.dot(solar_pivot1.values, city_solar_weights)
    # Convert to appropriate unit
    solar_pivot1["Total Hourly Energy (RAW)"] = np.true_divide(
        solar_pivot1['Total Hourly Energy (RAW)'].values, 1000000
    )
    return solar_pivot1


def main():
    """Main execution block."""
    # --- Data Loading (Weather) ---
    all_files = glob.glob("WEATHER_DATA/*_weather.json")
    li = []
    for filename in all_files:
        with open(filename, 'r', encoding="utf-8") as json_file:
            data = json.load(json_file)
            temp_df = pd.json_normalize(
                data,
                record_path=['days', 'hours'],
                meta=[['days', 'datetime'], ['address']]
            )
            li.append(temp_df)

    df_combined = pd.concat(li, axis=0, ignore_index=True)

    # --- Data Loading (Energy - Real) ---
    df_energy = pd.read_json("energy_data.json", convert_dates=False)
    df_energy['Date'] = pd.to_datetime(df_energy['Date'], format='%d.%m.%Y',
                                       errors='coerce', dayfirst=True)
    df_energy['DATE/HOUR'] = pd.to_datetime(
        df_energy['Date'].astype(str) + ' ' + df_energy['Hour'].astype(str) + ':00',
    )

    deleted_columns = ["Date", "Hour"]
    df_energy.drop(columns=deleted_columns, inplace=True)
    df_energy.set_index(df_energy['DATE/HOUR'], inplace=True)
    df_energy = df_energy[~df_energy.index.duplicated(keep='first')]

    # Clean Wind Energy Strings
    df_energy['Wind Energy'] = df_energy['Wind Energy'].astype(str).str.strip()
    df_energy["Wind Energy"] = df_energy["Wind Energy"].str.replace('.', '')
    df_energy["Wind Energy"] = df_energy["Wind Energy"].str.replace(',', '.')
    df_energy["Wind Energy"] = df_energy["Wind Energy"].astype(float)

    # Clean Solar Energy Strings
    df_energy['Solar Energy'] = df_energy['Solar Energy'].astype(str).str.strip()
    df_energy['Solar Energy'] = df_energy['Solar Energy'].str.replace('.', '')
    df_energy['Solar Energy'] = df_energy['Solar Energy'].str.replace(',', '.')
    df_energy['Solar Energy'] = df_energy['Solar Energy'].astype(float)
    # --- Preprocessing & Calculations ---
    target_colunms = ['days.datetime', 'datetime', 'temp', 'solarradiation',
                      'windspeed', 'address']
    df_final = df_combined[target_colunms].copy()

    df_final = convert_units(df_final)

    df_final = df_final.reset_index()
    df_final = df_final.drop_duplicates(subset=['Full Date', 'address'], keep='first')

    raw_wind_energy_cal(df_final)
    raw_solar_energy_cal(df_final)

    df_final = df_final.set_index(['Full Date', 'address'])
    wind_pivot = wind_pivot_creator(df_final)

    # --- Wind Analysis ---
    high_wind_mask = wind_pivot['Total Hourly Energy (RAW)'] > \
                     wind_pivot['Total Hourly Energy (RAW)'].quantile(0.5)

    stable_ratios = (df_energy.loc[high_wind_mask, 'Wind Energy'] /
                     wind_pivot.loc[high_wind_mask, 'Total Hourly Energy (RAW)'])

    # Calculate Scalers
    wind_scaler_best = float(stable_ratios.quantile(0.95))
    wind_scaler_worst = float(stable_ratios.quantile(0.05))

    print(f"Scalerlar: Best={wind_scaler_best:.2f}, Worst={wind_scaler_worst:.2f}")

    base_load = df_energy['Wind Energy'].min()

    # Apply Scalers
    wind_pivot["EXPECTED - BEST"] = (
            (wind_pivot['Total Hourly Energy (RAW)'] * wind_scaler_best) + base_load
    )
    wind_pivot["EXPECTED - WORST"] = (
            (wind_pivot['Total Hourly Energy (RAW)'] * wind_scaler_worst) + base_load
    )
    wind_pivot["Total Hourly Energy (REAL)"] = df_energy['Wind Energy']

    # Apply Shaper
    wind_pivot = energy_shaper(wind_pivot, 'EXPECTED - WORST',
                               'Total Hourly Energy (REAL)', tolerance=1.0)
    wind_pivot = energy_shaper(wind_pivot, 'EXPECTED - BEST',
                               'Total Hourly Energy (REAL)', tolerance=1.5, is_best=True)

    # --- Solar Analysis ---
    solar_pivot = solar_pivot_creator(df_final)
    daylight_mask = solar_pivot['Total Hourly Energy (RAW)'] > 0.0001

    solar_ratios = (df_energy.loc[daylight_mask, 'Solar Energy'] /
                    solar_pivot.loc[daylight_mask, 'Total Hourly Energy (RAW)'])

    s_solar_best = float(solar_ratios.quantile(0.99) * 1.2)
    s_solar_worst = float(solar_ratios.quantile(0.07))

    # Apply Scalers
    solar_pivot["EXPECTED - BEST"] = solar_pivot['Total Hourly Energy (RAW)'] * s_solar_best
    solar_pivot["EXPECTED - WORST"] = solar_pivot['Total Hourly Energy (RAW)'] * s_solar_worst
    solar_pivot["Total Hourly Energy (REAL)"] = df_energy['Solar Energy'].values

    # Apply Shaper
    solar_pivot = solar_shaper(solar_pivot, 'EXPECTED - BEST',
                               'Total Hourly Energy (REAL)', tolerance=1.05, is_best=True)
    solar_pivot = solar_shaper(solar_pivot, 'EXPECTED - WORST',
                               'Total Hourly Energy (REAL)', tolerance=1.0)

    # --- Export Results ---
    selected_solar_colunms = ['Full Date', 'EXPECTED - BEST',
                              'EXPECTED - WORST', 'Total Hourly Energy (REAL)']
    solar_pivot = solar_pivot.reset_index()
    solar_pivot = solar_pivot[selected_solar_colunms].copy()
    solar_pivot.to_json('complete_solar_records.json', indent=2,
                        orient='records', date_format='iso')
    print("Completed: Solar Data, stored in complete_solar_records.json")

    selected_wind_colunms = ['Full Date', 'EXPECTED - BEST',
                             'EXPECTED - WORST', 'Total Hourly Energy (REAL)']
    wind_pivot = wind_pivot.reset_index()
    wind_pivot = wind_pivot[selected_wind_colunms].copy()
    wind_pivot.to_json('complete_wind_records.json', indent=2,
                       orient='records', date_format='iso')
    print("Completed: Wind Data, stored in complete_wind_records.json")

if __name__ == "__main__":
    main()
