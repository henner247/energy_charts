import pandas as pd
from pathlib import Path

# Config
INPUT_FILE = Path("hourly_german_residual_load_and_prices_2024_present.csv")
OUTPUT_CSV = Path("monthly_statistics_summary.csv")

def calculate_daily_spread(group):
    # Requirement: daily price spread between the four highest prices of that day and the four minimum prices of that day
    if len(group) < 8:
        return None
    sorted_prices = group['day_ahead_price_eur_mwh'].sort_values()
    top_4_avg = sorted_prices.iloc[-4:].mean()
    bottom_4_avg = sorted_prices.iloc[:4].mean()
    return top_4_avg - bottom_4_avg

def main():
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Loading data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    df['datetime'] = pd.to_datetime(df['datetime_utc'])
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    df['date'] = df['datetime'].dt.date

    # Filter for relevant years if needed (dataset starts 2024, so likely just 2024, 2025)
    # Filter for relevant years if needed (dataset starts 2024, so likely just 2024, 2025, 2026)
    df = df[df['year'].isin([2024, 2025, 2026])]

    # 1. Calculate Daily Spreads first
    print("Calculating daily spreads...")
    # Group by date to get one spread per day
    daily_spreads = df.groupby(['year', 'month', 'date']).apply(calculate_daily_spread).reset_index(name='spread')
    
    # Aggregate spreads by Month/Year
    monthly_spread_avg = daily_spreads.groupby(['year', 'month'])['spread'].mean().reset_index(name='avg_spread')

    # 2. Calculate Hourly Metrics Aggregated by Month/Year
    print("Calculating monthly hourly metrics...")
    
    def monthly_agg(g):
        avg_price = g['day_ahead_price_eur_mwh'].mean()
        neg_hours = (g['day_ahead_price_eur_mwh'] < 0).sum()
        
        # Avg price where residual load < 0
        res_neg = g[g['residual_load_mw_avg'] < 0]
        avg_price_res_neg = res_neg['day_ahead_price_eur_mwh'].mean() if not res_neg.empty else None
        
        # Avg price where residual load > 60000
        res_high = g[g['residual_load_mw_avg'] > 60000]
        avg_price_res_high = res_high['day_ahead_price_eur_mwh'].mean() if not res_high.empty else None
        
        return pd.Series({
            'avg_price': avg_price,
            'neg_hours': neg_hours,
            'avg_price_res_neg': avg_price_res_neg,
            'avg_price_res_high': avg_price_res_high
        })

    monthly_hourly_stats = df.groupby(['year', 'month']).apply(monthly_agg).reset_index()

    # Merge Daily Spread Avgs with Hourly Stats
    merged = pd.merge(monthly_hourly_stats, monthly_spread_avg, on=['year', 'month'])

    # 3. Reshape/Pivot to desired table structure
    # We want columns for 2024 and 2025 for each metric
    # Metrics: avg_price, avg_spread, neg_hours, avg_price_res_neg, avg_price_res_high
    
    pivot_df = merged.pivot(index='month', columns='year', values=[
        'avg_price', 
        'avg_spread', 
        'neg_hours', 
        'avg_price_res_neg', 
        'avg_price_res_high'
    ])
    
    # Flatten columns
    # pivot_df.columns is MultiIndex: (metric, year)
    pivot_df.columns = [f"{metric}_{year}" for metric, year in pivot_df.columns]
    
    # Reorder columns nicely
    # Reorder columns nicely
    target_order = [
        'avg_price_2024', 'avg_price_2025', 'avg_price_2026',
        'avg_spread_2024', 'avg_spread_2025', 'avg_spread_2026',
        'neg_hours_2024', 'neg_hours_2025', 'neg_hours_2026',
        'avg_price_res_neg_2024', 'avg_price_res_neg_2025', 'avg_price_res_neg_2026',
        'avg_price_res_high_2024', 'avg_price_res_high_2025', 'avg_price_res_high_2026'
    ]
    
    # Filter to only existing columns (in case 2025 data is missing completely)
    start_cols = pivot_df.columns.tolist()
    final_cols = [c for c in target_order if c in start_cols]
    pivot_df = pivot_df[final_cols]
    
    # Reset index to make Month a column
    pivot_df = pivot_df.reset_index()

    # Create a month name column for display
    import calendar
    pivot_df['month'] = pivot_df['month'].astype(int).apply(lambda x: calendar.month_abbr[x])
    
    print("\n--- Monthly Statistics Summary ---")
    print(pivot_df.to_string(index=False, float_format="%.2f"))
    
    print(f"\nSaving to {OUTPUT_CSV}...")
    pivot_df.to_csv(OUTPUT_CSV, index=False, float_format="%.2f")

    # Generate PDF
    OUTPUT_PDF = Path("monthly_statistics_summary.pdf")
    print(f"Generating PDF report to {OUTPUT_PDF}...")
    
    import matplotlib.pyplot as plt
    
    # Create a figure for the table
    # Adjust width based on number of columns
    fig, ax = plt.subplots(figsize=(20, 8)) 
    ax.axis('off')
    ax.axis('tight')
    
    # Rename columns for better readability and split for two-row header effect
    # Map raw metric names to display names
    metric_map = {
        'avg_price': 'Avg Price',
        'avg_spread': 'Avg Hourly Spread',
        'neg_hours': 'Neg Hours',
        'avg_price_res_neg': 'Price\n(Res < 0)',
        'avg_price_res_high': 'Price\n(Res > 60G)'
    }
    
    # Prepare display dataframe
    display_df = pivot_df.copy()
    
    # Round negative hours to int (handle NaNs if necessary, though simpler to just format)
    # Use string formatting for display to avoid float decimals
    for yr in [2024, 2025, 2026]:
        col = f'neg_hours_{yr}'
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.0f}" if pd.notnull(x) else "-")
            
    # Format all other float columns to 2 decimal places
    for col in display_df.columns:
        if col == 'month' or 'neg_hours' in col:
            continue
        # Apply formatting
        display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
    
    # Format new columns dict
    new_cols = {}
    for col in display_df.columns:
        if col == 'month':
            new_cols[col] = 'Month'
            continue
            
        parts = col.rsplit('_', 1)
        if len(parts) == 2:
            metric, year = parts
            if metric in metric_map:
                new_cols[col] = f"{metric_map[metric]}\n{year}"
            else:
                new_cols[col] = col
    
    display_df = display_df.rename(columns=new_cols)

    # Create table
    table = ax.table(cellText=display_df.values,
                     colLabels=display_df.columns,
                     cellLoc='center',
                     loc='center')
    
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 2.0)  # Make rows taller to accommodate 2-row headers
    
    # Style formatting
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
            cell.set_facecolor('#e6e6e6')
            cell.set_height(0.1) # Taller header
    
    plt.title("Monthly Statistics Summary (2024 vs 2025)", fontsize=16, pad=20)
    
    plt.savefig(OUTPUT_PDF, bbox_inches='tight', pad_inches=0.5)
    plt.close()
    print(f"PDF saved to {OUTPUT_PDF.absolute()}")

if __name__ == "__main__":
    main()
