import urllib.request
import urllib.parse
import json
import csv
import datetime
from pathlib import Path
import time
from collections import defaultdict
import os

OUTPUT_FILE = Path("hourly_german_residual_load_and_prices_2024_present.csv")

def fetch_data(endpoint, params):
    base_url = "https://api.energy-charts.info"
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}/{endpoint}?{query_string}"
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as response:
                if response.status != 200:
                    raise Exception(f"API returned status {response.status}")
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(5)

def aggregate_to_hourly(data_dict):
    """
    Aggregates 15-minute data into hourly averages.
    Only hourly slots with exactly 4 measurements are included.
    """
    hourly_raw = defaultdict(list)
    for ts, values in data_dict.items():
        # Get the start of the hour
        hour_ts = (ts // 3600) * 3600
        hourly_raw[hour_ts].append(values)
    
    hourly_aggregated = {}
    for hour_ts, entries in hourly_raw.items():
        if len(entries) == 4:
            avg_net_load = sum(e['net_load'] for e in entries) / 4
            avg_renewables = sum(e['renewables'] for e in entries) / 4
            avg_solar = sum(e['solar'] for e in entries) / 4
            hourly_aggregated[hour_ts] = {
                'net_load': avg_net_load,
                'renewables': avg_renewables,
                'solar': avg_solar,
                'residual_load': avg_net_load - avg_renewables
            }
    return hourly_aggregated

def get_last_timestamp(file_path):
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return None
            
            last_row = None
            for row in reader:
                last_row = row
            
            if last_row:
                # Assuming timestamp_unix is the first column
                return int(last_row[0])
    except Exception as e:
        print(f"Error reading last timestamp: {e}")
        return None
    return None

def main():
    country = "de"
    
    
    # Check if header matches new schema, if not, force restart
    current_header = None
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', newline='') as f:
            current_header = next(csv.reader(f), None)
    
    expected_columns = ['timestamp_unix', 'datetime_utc', 'net_load_mw_avg', 'renewable_generation_mw_avg', 'solar_mw_avg', 'residual_load_mw_avg', 'day_ahead_price_eur_mwh']
    
    if current_header != expected_columns:
        print("Schema changed (adding Solar). Forcing full re-fetch...")
        last_ts = None
    else:
        last_ts = get_last_timestamp(OUTPUT_FILE)
    
    if last_ts:
        # Start from the next hour
        start_date = datetime.datetime.fromtimestamp(last_ts, tz=datetime.timezone.utc) + datetime.timedelta(hours=1)
        print(f"Found existing data up to {start_date - datetime.timedelta(hours=1)}.")
        is_append = True
    else:
        start_date = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        print("No existing data found. Fetching from start of 2024.")
        is_append = False
        
    end_date = datetime.datetime.now(datetime.timezone.utc)
    
    if start_date >= end_date:
        print("Data is already up to date.")
        return

    print(f"Fetching data from {start_date} to {end_date}...")

    # Selection keys based on previous inspection
    load_key = "Load (incl. self-consumption)"
    renewable_keys = {
        "Biomass", 
        "Hydro Run-of-River", 
        "Wind offshore", 
        "Wind onshore", 
        "Solar", 
        "Geothermal"
    }

    combined_hourly_load = {}
    prices_hourly = {}
    
    current_chunk_start = start_date
    
    while current_chunk_start < end_date:
        # Fetch in monthly chunks to handle years correctly, or smaller if near current time
        if current_chunk_start.month == 12:
            next_chunk_start = datetime.datetime(current_chunk_start.year + 1, 1, 1, tzinfo=datetime.timezone.utc)
        else:
            next_chunk_start = datetime.datetime(current_chunk_start.year, current_chunk_start.month + 1, 1, tzinfo=datetime.timezone.utc)
        
        chunk_end = next_chunk_start if next_chunk_start < end_date else end_date
        
        # If the chunk is very small (e.g. less than an hour), we might skip or handle carefully.
        # But for simplicity, we query.
        
        start_str = current_chunk_start.strftime("%Y-%m-%dT%H:00Z")
        # Ensure we cover the full end hour by using :59 if it's the end of fetch
        end_str = chunk_end.strftime("%Y-%m-%dT%H:59Z")
        
        print(f"Processing range: {start_str} to {end_str}")
        
        try:
            # 1. Fetch Power Data (15-min)
            power_data = fetch_data("total_power", {"country": country, "start": start_str, "end": end_str})
            ts_list = power_data.get('unix_seconds', [])
            production_types = power_data.get('production_types', [])
            series_map = {pt['name']: pt.get('data', []) for pt in production_types}
            
            if ts_list and load_key in series_map:
                load_vals = series_map[load_key]
                chunk_15min_data = {}
                
                # Extract Solar specifically
                solar_key = "Solar"
                solar_vals = [0.0] * len(ts_list)
                if solar_key in series_map:
                    solar_data_raw = series_map[solar_key]
                    for i, val in enumerate(solar_data_raw):
                        if i < len(solar_vals) and val is not None:
                            solar_vals[i] = val
                
                # Sum renewables
                r_sums = [0.0] * len(ts_list)
                for r_key in renewable_keys:
                    if r_key in series_map:
                        r_data = series_map[r_key]
                        for i, val in enumerate(r_data):
                            if i < len(r_sums) and val is not None:
                                r_sums[i] += val
                
                for i, ts in enumerate(ts_list):
                    if i < len(load_vals) and load_vals[i] is not None:
                        chunk_15min_data[ts] = {
                            'net_load': load_vals[i], 
                            'renewables': r_sums[i],
                            'solar': solar_vals[i]
                        }
                
                # Aggregate this chunk's 15min data to hourly
                chunk_hourly = aggregate_to_hourly(chunk_15min_data)
                combined_hourly_load.update(chunk_hourly)

            # 2. Fetch Price Data (Hourly)
            price_data = fetch_data("price", {"country": country, "start": start_str, "end": end_str})
            price_ts_list = price_data.get('unix_seconds', [])
            price_vals = price_data.get('price', [])
            
            for ts, p in zip(price_ts_list, price_vals):
                if p is not None:
                    prices_hourly[ts] = p
                    
        except Exception as e:
            print(f"Error processing range {start_str}: {e}")
        
        current_chunk_start = next_chunk_start
        time.sleep(1)

    # Merge results
    sorted_hours = sorted(set(combined_hourly_load.keys()) & set(prices_hourly.keys()))
    
    if not sorted_hours:
        print("No new complete data rows found.")
        return

    mode = 'a' if is_append else 'w'
    print(f"Writing {len(sorted_hours)} new hourly rows to {OUTPUT_FILE} (Mode: {mode})...")
    
    with open(OUTPUT_FILE, mode=mode, newline='') as f:
        writer = csv.writer(f)
        if not is_append:
            writer.writerow(['timestamp_unix', 'datetime_utc', 'net_load_mw_avg', 'renewable_generation_mw_avg', 'solar_mw_avg', 'residual_load_mw_avg', 'day_ahead_price_eur_mwh'])
        
        for ts in sorted_hours:
            load_data = combined_hourly_load[ts]
            price = prices_hourly[ts]
            dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat()
            writer.writerow([
                ts, dt, 
                load_data['net_load'], 
                load_data['renewables'], 
                load_data['solar'], 
                load_data['residual_load'], 
                price
            ])

    print(f"Update complete. File saved: {OUTPUT_FILE.absolute()}")

if __name__ == "__main__":
    main()
