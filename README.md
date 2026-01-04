# German Energy Data Analysis 🇩🇪

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_svg)](https://share.streamlit.io/henner247/energy_charts/master/app.py)

This project analyzes German electricity prices, residual load, and solar capture prices using data from [Energy-Charts.info](https://energy-charts.info/).

## 🚀 Live Dashboard
The interactive dashboard is available at: [your-streamlit-app-url-will-go-here]

## 🛠 Features
- **Daily Automated Data Updates**: GitHub Actions fetch the latest data every day at 14:00 CET.
- **Monthly Statistics**: Average prices, price spreads, and negative price hours.
- **Solar Capture Price Analysis**: Volume-weighted average prices for solar production and capture rates.
- **Interactive Visualizations**: Correlation between residual load and market prices.

## 📦 Deployment
This app is designed to be deployed on [Streamlit Cloud](https://streamlit.io/cloud).
1. Fork or clone this repository.
2. Sign in to Streamlit Cloud and click **"New app"**.
3. Select this repository and `app.py` as the main file.
4. Deploy!


## Overview

The toolset allows you to:
1.  **Fetch Data**: Retrieve 15-minute resolution residual load and hourly Day-Ahead electricity prices for Germany (2024-Present).
2.  **Analyze**: Calculate daily price spreads and monthly statistics.
3.  **Visualize**: Generate detailed PDF reports and scatter plots.

## Scripts

### 1. Data Fetching
- **`residual_load_with_prices.py`**: The main data fetching script.
    - Fetches 15-minute residual load (Load - Renewables).
    - Fetches Hourly Day-Ahead prices.
    - Aggregates load to hourly resolution.
    - Merges data into `hourly_german_residual_load_and_prices_2024_present.csv`.
    - Supports incremental updates (only downloads new data).

### 2. Analysis & Reporting
- **`monthly_stats.py`**: Generates a monthly comparison table (2024 vs 2025).
    - Outputs: `monthly_statistics_summary.pdf` and `.csv`.
    - Metrics: Average Price, Hourly Spread (Top 4 - Bottom 4), Negative Hours, etc.

- **`monthly_scatter_plots.py`**: Generates scatter plots of Residual Load vs Price.
    - Outputs: `monthly_scatter_plots.pdf` (12 pages, one per month).

- **`price_analysis.py`**: Calculates and plots the daily price spread trend.
    - Outputs: `price_spread_plot.png` and `daily_price_spread_analysis.csv`.

## Setup

1.  Python 3.x installed.
2.  Install dependencies:
    ```bash
    pip install pandas matplotlib
    ```

## Usage

1.  **Update Data**:
    ```bash
    python residual_load_with_prices.py
    ```
2.  **Generate Reports**:
    ```bash
    python monthly_stats.py
    python monthly_scatter_plots.py
    ```
