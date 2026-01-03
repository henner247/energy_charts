
import pandas as pd
from pathlib import Path

INPUT_FILE = Path("hourly_german_residual_load_and_prices_2024_present.csv")

def main():
    print(f"Loading data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    df['datetime'] = pd.to_datetime(df['datetime_utc'])
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    
    # Filter for 2024
    df_2024 = df[df['year'] == 2024].copy()
    
    print(f"\n--- Data Quality Investigation 2024 ---")
    print(f"Total Rows: {len(df_2024)}")
    print(f"Rows with NaN Solar: {df_2024['solar_mw_avg'].isna().sum()}")
    print(f"Rows with NaN Price: {df_2024['day_ahead_price_eur_mwh'].isna().sum()}")
    
    # Calculate Revenue
    df_2024['solar_revenue'] = df_2024['solar_mw_avg'] * df_2024['day_ahead_price_eur_mwh']
    
    # 1. True Capture Price (Volume Weighted)
    total_revenue = df_2024['solar_revenue'].sum()
    total_generation = df_2024['solar_mw_avg'].sum()
    vwap = total_revenue / total_generation
    print(f"\n1. True Capture Price (Sum(Rev) / Sum(Gen)): {vwap:.2f} EUR/MWh")
    
    # 2. Simple Average of Monthly PV Prices
    monthly_grouped = df_2024.groupby('month')[['solar_mw_avg', 'solar_revenue']].sum()
    monthly_grouped['pv_price'] = monthly_grouped['solar_revenue'] / monthly_grouped['solar_mw_avg']
    
    simple_avg_monthly = monthly_grouped['pv_price'].mean()
    print(f"2. Simple Average of Monthly PV Prices: {simple_avg_monthly:.2f} EUR/MWh")
    
    print("\n--- Monthly PV Prices ---")
    print(monthly_grouped['pv_price'])
    
    # 3. Simple Average of Hourly Capture Prices (Nonsensical but for check)
    # Filter out zero generation hours to avoid div/0 or just averaging price where solar > 0
    solar_hours = df_2024[df_2024['solar_mw_avg'] > 0]
    avg_price_during_solar = solar_hours['day_ahead_price_eur_mwh'].mean()
    print(f"3. Simple Average of Price during non-zero Solar Hours: {avg_price_during_solar:.2f} EUR/MWh")

if __name__ == "__main__":
    main()
