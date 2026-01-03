import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
import calendar

# Config
INPUT_FILE = Path("hourly_german_residual_load_and_prices_2024_present.csv")
OUTPUT_PDF = Path("monthly_scatter_plots.pdf")

def main():
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Loading data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    df['datetime'] = pd.to_datetime(df['datetime_utc'])
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    
    # Filter for relevant years
    df = df[df['year'].isin([2024, 2025, 2026])]

    print(f"Generating scatter plots to {OUTPUT_PDF}...")
    
    with PdfPages(OUTPUT_PDF) as pdf:
        for month_num in range(1, 13):
            month_name = calendar.month_name[month_num]
            print(f"  Plotting {month_name}...")
            
            # Filter data for this month
            month_data = df[df['month'] == month_num]
            
            if month_data.empty:
                print(f"    No data for {month_name}, skipping.")
                continue

            plt.figure(figsize=(10, 7))
            
            # Plot 2024
            data_2024 = month_data[month_data['year'] == 2024]
            if not data_2024.empty:
                plt.scatter(data_2024['residual_load_mw_avg'], data_2024['day_ahead_price_eur_mwh'], 
                            alpha=0.5, label='2024', s=10, color='skyblue')
            
            # Plot 2025
            data_2025 = month_data[month_data['year'] == 2025]
            if not data_2025.empty:
                plt.scatter(data_2025['residual_load_mw_avg'], data_2025['day_ahead_price_eur_mwh'], 
                            alpha=0.5, label='2025', s=10, color='orange')

            # Plot 2026
            data_2026 = month_data[month_data['year'] == 2026]
            if not data_2026.empty:
                plt.scatter(data_2026['residual_load_mw_avg'], data_2026['day_ahead_price_eur_mwh'], 
                            alpha=0.5, label='2026', s=10, color='green')
            
            plt.title(f"Residual Load vs Price - {month_name}", fontsize=14)
            plt.xlabel("Residual Load (MW)", fontsize=12)
            plt.ylabel("Day-Ahead Price (EUR/MWh)", fontsize=12)
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.legend()
            
            # Add zero lines for reference
            plt.axhline(0, color='black', linewidth=0.8, linestyle='-')
            plt.axvline(0, color='black', linewidth=0.8, linestyle='-')
            
            plt.tight_layout()
            
            # Save to PDF page
            pdf.savefig()
            plt.close()

        # --- Jan 2025 vs Jan 2026 Comparison ---
        print("  Plotting Jan 2025 vs Jan 2026 Comparison...")
        plt.figure(figsize=(10, 7))
        
        jan_data = df[df['month'] == 1]
        jan_2025 = jan_data[jan_data['year'] == 2025]
        jan_2026 = jan_data[jan_data['year'] == 2026]
        
        if not jan_2025.empty:
            plt.scatter(jan_2025['residual_load_mw_avg'], jan_2025['day_ahead_price_eur_mwh'],
                        alpha=0.5, label='Jan 2025', s=15, color='orange', marker='o')
        
        if not jan_2026.empty:
            plt.scatter(jan_2026['residual_load_mw_avg'], jan_2026['day_ahead_price_eur_mwh'],
                        alpha=0.6, label='Jan 2026', s=15, color='green', marker='x')

        plt.title("Residual Load vs Price - January 2025 vs 2026", fontsize=14)
        plt.xlabel("Residual Load (MW)", fontsize=12)
        plt.ylabel("Day-Ahead Price (EUR/MWh)", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        
        plt.axhline(0, color='black', linewidth=0.8, linestyle='-')
        plt.axvline(0, color='black', linewidth=0.8, linestyle='-')
        
        plt.tight_layout()
        pdf.savefig()
        plt.close()

    print(f"Done. PDF saved to {OUTPUT_PDF.absolute()}")

if __name__ == "__main__":
    main()
