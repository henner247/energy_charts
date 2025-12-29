import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Config
INPUT_FILE = Path("hourly_german_residual_load_and_prices_2024_present.csv")
OUTPUT_CSV = Path("daily_price_spread_analysis.csv")
OUTPUT_PLOT = Path("price_spread_plot.png")

def calculate_spread(group):
    """
    Calculates the spread between the average of the top 2 
    and the average of the bottom 2 prices in a daily group.
    """
    if len(group) < 4:
        # Need at least 4 hourly values to get 2 top and 2 bottom
        return pd.Series({'daily_spread': None})
    
    sorted_prices = group['day_ahead_price_eur_mwh'].sort_values()
    bottom_2_avg = sorted_prices.iloc[:2].mean()
    top_2_avg = sorted_prices.iloc[-2:].mean()
    
    return pd.Series({
        'avg_top_2': top_2_avg,
        'avg_bottom_2': bottom_2_avg,
        'daily_spread': top_2_avg - bottom_2_avg
    })

def main():
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found. Please run residual_load_with_prices.py first.")
        return

    print(f"Loading data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    
    # Convert timestamp
    df['datetime'] = pd.to_datetime(df['datetime_utc'])
    df['date'] = df['datetime'].dt.date
    
    print("Calculating daily price spreads...")
    # Group by date and calculate spread
    daily_results = df.groupby('date').apply(calculate_spread).reset_index()
    
    # Drop days with insufficient data (None)
    daily_results = daily_results.dropna()
    
    # Calculate 30-day moving average
    daily_results['spread_30d_ma'] = daily_results['daily_spread'].rolling(window=30).mean()
    
    print(f"Saving analysis to {OUTPUT_CSV}...")
    daily_results.to_csv(OUTPUT_CSV, index=False)
    
    print(f"Generating plot...")
    plt.figure(figsize=(12, 7))
    
    # Plot daily spread as scatter/thin line
    plt.plot(daily_results['date'], daily_results['daily_spread'], 
             alpha=0.3, label='Daily Spread (Top 2 - Bottom 2 Avg)', color='skyblue')
    
    # Plot 30-day moving average
    plt.plot(daily_results['date'], daily_results['spread_30d_ma'], 
             color='navy', linewidth=2.5, label='30-Day Moving Average')
    
    plt.title("German Day-Ahead Price Daily Spread (Top 2 vs Bottom 2)", fontsize=14)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Price Spread (EUR/MWh)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(OUTPUT_PLOT)
    print(f"Plot saved to {OUTPUT_PLOT.absolute()}")
    
    print("\nSummary Statistics for Price Spread (EUR/MWh):")
    print(daily_results['daily_spread'].describe())

if __name__ == "__main__":
    main()
