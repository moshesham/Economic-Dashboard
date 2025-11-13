# 🌍 Global Economic & Financial Dashboard

A comprehensive, interactive web application for monitoring and analyzing global economic trends and financial markets. Built with Python, Streamlit, and modern data visualization libraries.

## 📊 Overview

This dashboard serves as a high-performance analytical tool for tracking real-time economic indicators, financial market performance, treasury yield curves, and market volatility. It aggregates data from multiple authoritative sources to provide actionable insights for analysts, investors, and economics enthusiasts.

## ✨ Features

### Homepage - Global Overview
- **Key Economic Indicators**: Real-time metrics for:
  - US GDP Growth (Quarterly % Change)
  - US Inflation (CPI % Change YoY)
  - US Federal Funds Rate
  - WTI Crude Oil Price
  - Gold Price
- **Interactive World GDP Map**: Visualize global GDP growth patterns
- **S&P 500 Performance Chart**: 5-year historical trend analysis

### Economic Indicators Deep Dive
- **Multi-Country Comparison**: Compare economic metrics across major economies
- **Flexible Metric Selection**: Choose from GDP Growth, Inflation (CPI), or Unemployment Rate
- **Custom Date Ranges**: Filter data for specific time periods
- **Interactive Visualizations**: Dynamic charts with hover details and tooltips
- **Summary Statistics**: View latest values and period averages

### Financial Markets Deep Dive
- **Market Indices Analysis**:
  - Track S&P 500, NASDAQ, FTSE 100, Nikkei 225, and more
  - Normalized performance comparison
  - Customizable time periods
  
- **US Treasury Yield Curve**:
  - Historical 10-Year and 2-Year Treasury yields
  - Yield curve spread analysis with inversion detection
  - Visual indicators for recession signals
  
- **Market Volatility (VIX)**:
  - 3-year VIX trend analysis
  - Real-time volatility gauge with color-coded risk levels
  - Statistical summaries (average, min, max)

## 🚀 Live Demo

*Coming soon: Streamlit Cloud deployment link*

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/moshesham/Economic-Dashboard.git
cd Economic-Dashboard
```

### Step 2: Create a Virtual Environment
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
streamlit run app.py
```

The dashboard will open automatically in your default web browser at `http://localhost:8501`

## 📦 Project Structure

```
economic-dashboard/
│
├── .github/
│   └── workflows/          # CI/CD configurations (optional)
│
├── .streamlit/
│   └── config.toml         # Streamlit app configuration and theming
│
├── modules/
│   └── data_loader.py      # Data fetching and API integration functions
│
├── pages/
│   ├── 1_Economic_Indicators_Deep_Dive.py
│   └── 2_Financial_Markets_Deep_Dive.py
│
├── .gitignore              # Python .gitignore
├── app.py                  # Main Streamlit application (Homepage)
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## 📚 Dependencies

- **streamlit** (≥1.28.0): Web application framework
- **pandas** (≥2.0.0): Data manipulation and analysis
- **plotly** (≥5.17.0): Interactive data visualizations
- **yfinance** (≥0.2.28): Yahoo Finance API for market data
- **pandas-datareader** (≥0.10.0): FRED and World Bank data access
- **numpy** (≥1.24.0): Numerical computing

## 🔗 Data Sources

This dashboard pulls data from the following authoritative sources:

- **[Federal Reserve Economic Data (FRED)](https://fred.stlouisfed.org/)**: US economic indicators, treasury yields, commodity prices
- **[Yahoo Finance](https://finance.yahoo.com/)**: Stock market indices, volatility data (VIX)
- **[World Bank](https://www.worldbank.org/)**: Global GDP growth statistics

## 🎨 Configuration

### Theme Customization
The dashboard uses a professional dark theme. You can customize colors by editing `.streamlit/config.toml`:

```toml
[theme]
primaryColor="#0068c9"
backgroundColor="#040f26"
secondaryBackgroundColor="#081943"
textColor="#ffffff"
font="sans serif"
```

## 📖 Usage Guide

### Navigation
Use the sidebar to navigate between different pages:
1. **Home**: Global overview and key metrics
2. **Economic Indicators Deep Dive**: Compare countries and indicators
3. **Financial Markets Deep Dive**: Analyze markets, yields, and volatility

### Interactivity
- **Hover** over charts to see detailed values
- **Select/Deselect** legend items to filter visualizations
- **Zoom** and **pan** on charts for detailed analysis
- **Use filters** in sidebars to customize data views

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 👨‍💻 Author

**Moshe Sham**

## 🙏 Acknowledgments

- Federal Reserve Bank of St. Louis for FRED API
- Yahoo Finance for market data API
- Streamlit team for the amazing framework
- Plotly for powerful visualization tools

## 📞 Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

Built with ❤️ using Streamlit, Plotly, and Python