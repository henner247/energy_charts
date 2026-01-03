
import pandas as pd
from pathlib import Path
import calendar
import matplotlib.pyplot as plt

# Config
INPUT_FILE = Path("hourly_german_residual_load_and_prices_2024_present.csv")
OUTPUT_PDF = Path("solar_capture_prices_outlook.pdf")

def main():
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Loading data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    df['datetime'] = pd.to_datetime(df['datetime_utc'])
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    
    # Check if 'solar_mw_avg' exists
    if 'solar_mw_avg' not in df.columns:
        print("Error: 'solar_mw_avg' column missing. Please run residual_load_with_prices.py first.")
        return

    # Filter for full years or relevant data (2024, 2025, 2026)
    df = df[df['year'].isin([2024, 2025, 2026])]

    print("Calculating Solar Capture and Baseload Prices...")

    # Calculate Revenue for each hour
    df['solar_revenue'] = df['solar_mw_avg'] * df['day_ahead_price_eur_mwh']

    # --- Monthly Calculation ---
    # We need: Sum of solar revenue, Sum of solar generation, Mean of price
    monthly_grouped = df.groupby(['year', 'month']).agg({
        'solar_mw_avg': 'sum',
        'solar_revenue': 'sum',
        'day_ahead_price_eur_mwh': 'mean'
    }).reset_index()
    
    monthly_grouped['pv_price'] = monthly_grouped['solar_revenue'] / monthly_grouped['solar_mw_avg']
    monthly_grouped['baseload_price'] = monthly_grouped['day_ahead_price_eur_mwh']
    monthly_grouped['capture_rate'] = monthly_grouped['pv_price'] / monthly_grouped['baseload_price']
    
    # --- Positive Price Calculation (Curtailment) ---
    # Filter where price >= 0
    df_pos = df[df['day_ahead_price_eur_mwh'] >= 0].copy()
    monthly_pos = df_pos.groupby(['year', 'month'])[['solar_mw_avg', 'solar_revenue']].sum().reset_index()
    monthly_pos['pv_price_pos'] = monthly_pos['solar_revenue'] / monthly_pos['solar_mw_avg']
    
    # Merge
    monthly_grouped = pd.merge(monthly_grouped, monthly_pos[['year', 'month', 'pv_price_pos']], on=['year', 'month'], how='left')

    # Pivot to Monthly Table
    monthly_pivot = monthly_grouped.pivot(index='month', columns='year', values=['pv_price', 'pv_price_pos', 'baseload_price', 'capture_rate'])
    
    # Flatten columns
    def rename_col(col_tuple):
        metric, year = col_tuple
        if metric == 'pv_price':
            return f"PV Price {year}"
        elif metric == 'pv_price_pos':
            return f"PV Price (Pos) {year}"
        elif metric == 'baseload_price':
            return f"Baseload {year}"
        elif metric == 'capture_rate':
            return f"Capture Rate {year}"
        return f"{metric} {year}"

    monthly_pivot.columns = [rename_col(col) for col in monthly_pivot.columns]
    monthly_pivot = monthly_pivot.reset_index()
    
    monthly_pivot['month_name'] = monthly_pivot['month'].apply(lambda x: calendar.month_abbr[x])
    
    # Reorder columns
    sorted_years = sorted(monthly_grouped['year'].unique())
    col_order = ['month_name']
    for y in sorted_years:
        col_order.append(f"PV Price {y}")
        col_order.append(f"PV Price (Pos) {y}")
        col_order.append(f"Baseload {y}")
        col_order.append(f"Capture Rate {y}")
        
    # Filter to existing columns
    col_order = [c for c in col_order if c in monthly_pivot.columns]
    monthly_pivot = monthly_pivot[col_order]
    
    monthly_pivot.rename(columns={'month_name': 'Month'}, inplace=True)

    # --- Yearly Calculation ---
    yearly_grouped = df.groupby(['year']).agg({
        'solar_mw_avg': 'sum',
        'solar_revenue': 'sum',
        'day_ahead_price_eur_mwh': 'mean'
    }).reset_index()
    
    yearly_grouped['pv_price'] = yearly_grouped['solar_revenue'] / yearly_grouped['solar_mw_avg']
    yearly_grouped['baseload_price'] = yearly_grouped['day_ahead_price_eur_mwh']
    yearly_grouped['capture_rate'] = yearly_grouped['pv_price'] / yearly_grouped['baseload_price']
    
    # Yearly Positive Calculation
    yearly_pos = df_pos.groupby(['year'])[['solar_mw_avg', 'solar_revenue']].sum().reset_index()
    yearly_pos['pv_price_pos'] = yearly_pos['solar_revenue'] / yearly_pos['solar_mw_avg']
    
    yearly_grouped = pd.merge(yearly_grouped, yearly_pos[['year', 'pv_price_pos']], on='year', how='left')
    
    # Format Yearly Table
    yearly_display = yearly_grouped[['year', 'pv_price', 'pv_price_pos', 'baseload_price', 'capture_rate']].copy()
    yearly_display.columns = ['Year', 'Yearly PV Price', 'Yearly PV Price (Pos)', 'Yearly Baseload Price', 'Capture Rate']
    
    # --- Generate PDF ---
    print(f"Generating PDF report to {OUTPUT_PDF}...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 10), gridspec_kw={'height_ratios': [2, 1]})
    
    # Plot Monthly Table
    ax1.axis('off')
    ax1.set_title("Monthly Solar Capture vs Baseload Prices (€/MWh)", fontsize=16, pad=20)
    
    # Format data for table
    table_data_monthly = monthly_pivot.copy()
    for col in table_data_monthly.columns:
        if col != 'Month':
            if 'Capture Rate' in col:
                table_data_monthly[col] = table_data_monthly[col].fillna(0).apply(lambda x: f"{x*100:.1f}%")
            else:
                table_data_monthly[col] = table_data_monthly[col].fillna(0).apply(lambda x: f"{x:.2f}")

    table1 = ax1.table(cellText=table_data_monthly.values,
                       colLabels=table_data_monthly.columns,
                       cellLoc='center',
                       loc='center')
    
    table1.auto_set_font_size(False)
    table1.set_fontsize(8) # Smaller font for more columns
    table1.scale(1.0, 1.5)
    
    # Style header
    for (row, col), cell in table1.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
            cell.set_facecolor('#e6e6e6')
            cell.set_height(0.12) # Taller header for 3 lines of text? No, just keep standard.
    
    # Plot Yearly Table
    ax2.axis('off')
    ax2.set_title("Yearly Solar Capture vs Baseload Prices (€/MWh)", fontsize=16, pad=20)
    
    table_data_yearly = yearly_display.copy()
    table_data_yearly['Yearly PV Price'] = table_data_yearly['Yearly PV Price'].apply(lambda x: f"{x:.2f}")
    table_data_yearly['Yearly PV Price (Pos)'] = table_data_yearly['Yearly PV Price (Pos)'].apply(lambda x: f"{x:.2f}")
    table_data_yearly['Yearly Baseload Price'] = table_data_yearly['Yearly Baseload Price'].apply(lambda x: f"{x:.2f}")
    table_data_yearly['Capture Rate'] = table_data_yearly['Capture Rate'].apply(lambda x: f"{x*100:.1f}%")
    
    table2 = ax2.table(cellText=table_data_yearly.values,
                       colLabels=table_data_yearly.columns,
                       cellLoc='center',
                       loc='center',
                       colWidths=[0.1, 0.2, 0.2, 0.2, 0.2]) 
    
    table2.auto_set_font_size(False)
    table2.set_fontsize(10)
    table2.scale(1.0, 1.5)
    
    for (row, col), cell in table2.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
            cell.set_facecolor('#e6e6e6')
            cell.set_height(0.1)

    plt.tight_layout()
    plt.savefig(OUTPUT_PDF)
    plt.close()
    
    print("Done.")
    
    # Print for console verification
    print("\n--- Yearly Summary ---")
    print(yearly_display)

if __name__ == "__main__":
    main()
