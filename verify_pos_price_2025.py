
import pandas as pd
from pathlib import Path

INPUT_FILE = Path("hourly_german_residual_load_and_prices_2024_present.csv")

def main():
    print(f"Loading data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    df['datetime'] = pd.to_datetime(df['datetime_utc'])
    df['year'] = df['datetime'].dt.year
    
    # Filter for 2025
    df_2025 = df[df['year'] == 2025].copy()
    
    print(f"\n--- Analysis for 2025 ---")
    
    # Calculate Base Revenue
    df_2025['solar_revenue'] = df_2025['solar_mw_avg'] * df_2025['day_ahead_price_eur_mwh']
    
    total_gen = df_2025['solar_mw_avg'].sum()
    total_rev = df_2025['solar_revenue'].sum()
    pv_price = total_rev / total_gen
    
    print(f"Total Generation: {total_gen:,.0f} MWh")
    print(f"Total Revenue: {total_rev:,.0f} EUR")
    print(f"PV Price: {pv_price:.2f} EUR/MWh")
    
    print("-" * 30)
    
    # Analyze Negative Price Hours during Solar Production
    neg_price_solar = df_2025[(df_2025['day_ahead_price_eur_mwh'] < 0) & (df_2025['solar_mw_avg'] > 0)]
    
    neg_revenue = (neg_price_solar['solar_mw_avg'] * neg_price_solar['day_ahead_price_eur_mwh']).sum()
    neg_gen = neg_price_solar['solar_mw_avg'].sum()
    neg_hours_count = len(neg_price_solar)
    
    print(f"Negative Revenue Hours (Solar > 0): {neg_hours_count}")
    print(f"Generation during Neg Hours: {neg_gen:,.0f} MWh ({(neg_gen/total_gen)*100:.1f}%)")
    print(f"Revenue Check (Negative Part): {neg_revenue:,.0f} EUR")
    
    print("-" * 30)
    
    # Calculate Positive Only
    df_pos = df_2025[df_2025['day_ahead_price_eur_mwh'] >= 0]
    pos_gen = df_pos['solar_mw_avg'].sum()
    pos_rev = (df_pos['solar_mw_avg'] * df_pos['day_ahead_price_eur_mwh']).sum()
    
    # Note: Logic in previous script was: sum(positive_revenue) / sum(positive_generation)
    # But usually "curtailment" means you lose the generation volume too?
    # Wait, the prompt asked: "PV_Price_pos ... product of hourly solar * price ... divided by the total solar production in that month / year"
    # Wait, let me re-read the prompt:
    # "product of the hourly solar production times the price in that hour summed up over the month or year and divided by the total solar production in that month / year" -> This is standard PV Price.
    # Then for POS: "capping the price at 0 ... calculate that PV_Price_pos"
    # Actually, standard interpretation of "capture price with curtailment":
    # If price < 0, revenue = 0, generation = 0 (or generation is excluded from denominator if we are calculating avg received price for SOLD energy).
    # IF we just cap price at 0 but keep generation in denominator, the price would increase mainly because we remove negative sums.
    # IF we assume we don't sell, we remove both numerator and denominator.
    
    # My previous implementation:
    # monthly_pos['pv_price_pos'] = monthly_pos['solar_revenue'] / monthly_pos['solar_mw_avg']
    # calculated on `df_pos` which filters out negative price rows entirely.
    # So it is: Sum(Rev where P>=0) / Sum(Gen where P>=0).
    
    pv_price_pos = pos_rev / pos_gen
    
    print(f"Total Generation (Pos Hours): {pos_gen:,.0f} MWh")
    print(f"Total Revenue (Pos Hours): {pos_rev:,.0f} EUR")
    print(f"PV Price (Pos): {pv_price_pos:.2f} EUR/MWh")
    
    print("-" * 30)
    print(f"Difference: {pv_price_pos - pv_price:.2f} EUR/MWh")
    
    # Check impact
    # To get from 47.82 to ~67 (delta 20), we need to see if negative revenue was dragging it down that much.
    # Diff = Pos_Price - Base_Price
    #      = (Pos_Rev / Pos_Gen) - ((Pos_Rev + Neg_Rev) / (Pos_Gen + Neg_Gen))
    
    print("\nDrill Down:")
    print(f"Avg Negative Price during Solar: {neg_price_solar['day_ahead_price_eur_mwh'].mean():.2f} EUR/MWh")
    print(f"Min Negative Price: {neg_price_solar['day_ahead_price_eur_mwh'].min():.2f} EUR/MWh")

if __name__ == "__main__":
    main()
