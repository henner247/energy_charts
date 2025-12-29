import urllib.request
import urllib.parse
import json
import csv
import datetime
from pathlib import Path
import time

def fetch_data(endpoint, params):
    base_url = "https://api.energy-charts.info"
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}/{endpoint}?{query_string}"
    
    # print(f"  Fetching: {url}")
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

def main():
    country = "de"
    print(f"Fetching German power data since 2024-01-01 (corrected series)...")
    
    combined_data = {}
    # Based on API inspection
    load_key = "Load (incl. self-consumption)"
    renewable_keys = {
        "Biomass", 
        "Hydro Run-of-River", 
        "Wind offshore", 
        "Wind onshore", 
        "Solar", 
        "Geothermal"
    }

    start_date = datetime.datetime(2024, 1, 1)
    # Using current date from metadata
    end_date = datetime.datetime(2025, 12, 28)
    
    current_chunk_start = start_date
    
    while current_chunk_start < end_date:
        if current_chunk_start.month == 12:
            next_chunk_start = datetime.datetime(current_chunk_start.year + 1, 1, 1)
        else:
            next_chunk_start = datetime.datetime(current_chunk_start.year, current_chunk_start.month + 1, 1)
        
        chunk_end = next_chunk_start if next_chunk_start < end_date else end_date
        
        start_str = current_chunk_start.strftime("%Y-%m-%dT00:00Z")
        end_str = chunk_end.strftime("%Y-%m-%dT23:59Z")
        
        print(f"Processing range: {start_str} to {end_str}")
        
        try:
            # Fetch Total Power (has the most complete "Load" and renewable series)
            data = fetch_data("total_power", {"country": country, "start": start_str, "end": end_str})
            
            timestamps = data.get('unix_seconds', [])
            production_types = data.get('production_types', [])
            
            # Map production types by name
            series_map = {pt['name']: pt.get('data', []) for pt in production_types}
            
            if timestamps and load_key in series_map:
                load_values = series_map[load_key]
                
                # Renewable sum for this chunk
                renewable_sums = [0.0] * len(timestamps)
                for r_key in renewable_keys:
                    if r_key in series_map:
                        r_data = series_map[r_key]
                        for i, val in enumerate(r_data):
                            if i < len(renewable_sums) and val is not None:
                                renewable_sums[i] += val
                
                for i, ts in enumerate(timestamps):
                    if i < len(load_values):
                        net_load = load_values[i]
                        if net_load is not None:
                            if ts not in combined_data:
                                combined_data[ts] = {'net_load': net_load, 'renewables': renewable_sums[i]}
        
        except Exception as e:
            print(f"Error processing range {start_str}: {e}")
        
        current_chunk_start = next_chunk_start
        time.sleep(1)

    if not combined_data:
        print("No data collected.")
        return

    sorted_ts = sorted(combined_data.keys())
    output_file = Path("german_residual_load_2024_present.csv")
    
    # Permission error fix
    if output_file.exists():
        try:
            with open(output_file, 'a'): pass
        except PermissionError:
            output_file = Path(f"german_residual_load_2024_present_{int(time.time())}.csv")

    print(f"Writing {len(sorted_ts)} rows to {output_file}...")
    with open(output_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp_unix', 'datetime_utc', 'net_load_mw', 'renewable_generation_mw', 'residual_load_mw'])
        
        for ts in sorted_ts:
            data = combined_data[ts]
            net = data['net_load']
            ren = data['renewables']
            residual = net - ren
            dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat()
            writer.writerow([ts, dt, net, ren, residual])

    print(f"Process complete. File saved: {output_file.absolute()}")

if __name__ == "__main__":
    main()
