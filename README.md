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
- **API Key Status**: Real-time indicator of authenticated access

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

### 📄 SEC EDGAR Data Explorer (NEW)
- **Company Financials**: Access XBRL financial statement data via SEC's Company Facts API
- **SEC Filings Browser**: View and analyze recent 10-K, 10-Q, 8-K, and other filings
- **Institutional Holdings**: Track Form 13F holdings from institutional investment managers
- **Financial Statement Data Sets**: Download quarterly FSDS data for bulk analysis
- **CIK Lookup**: Search companies by ticker symbol or CIK number
- **Key Metrics Visualization**: Charts for revenue, net income, and other financial trends

**Available SEC Datasets:**
- Financial Statement Data Sets (quarterly XBRL data from all filers)
- Company Facts API (real-time standardized financial data)
- Form 13F Holdings (institutional investor positions)
- Fails-to-Deliver Data (settlement failure records)
- Company Submissions (filing history and metadata)

### 🔑 API Key Management (NEW)
- **Secure Storage**: Encrypted API key storage using industry-standard encryption
- **Multiple Services**: Support for FRED, Yahoo Finance, Alpha Vantage, Quandl, and more
- **Visual Management**: User-friendly interface for adding, updating, and removing keys
- **Status Indicators**: Real-time display of configured services
- **Higher Limits**: Automatic use of API keys for better rate limits and reliability

### 🔄 Automated Data Refresh (NEW)
- **Daily Updates**: Automatic data refresh at 6 AM UTC via GitHub Actions or Apache Airflow
- **Centralized Caching**: All economic data stored in unified cache for fast access
- **Backup System**: CSV backups created daily for inspection and recovery
- **Manual Triggers**: Run data refresh on-demand when needed
- **Quality Validation**: Automated checks ensure data freshness and completeness

For detailed setup instructions, see [docs/AUTOMATED_DATA_REFRESH.md](docs/AUTOMATED_DATA_REFRESH.md)

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

### Step 5: Set Up API Keys (Recommended)
```bash
# Quick setup with provided FRED API key
python quickstart_api_keys.py

# Or run the setup script
python setup_credentials.py
```

**Benefits of using API keys:**
- Higher rate limits for data requests
- More reliable data access
- Access to premium features
- Better performance

### Step 6: Run Tests (Optional)
```bash
# Run the local testing framework
python test_locally.py

# Or run tests manually
python -m pytest tests/ -v
```

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

## 🧪 Testing

This project includes a comprehensive testing framework to ensure reliability and facilitate future deployments.

### Local Testing
Run the local testing script to validate the entire application:

```bash
python test_locally.py
```

This script performs:
- ✅ Syntax checking for all Python files
- ✅ Unit tests for data loading functions
- ✅ Integration tests for app modules
- ✅ Offline mode validation

### Manual Testing
Run individual test components:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_data_loader.py -v

# Run with coverage (if pytest-cov installed)
python -m pytest tests/ --cov=modules --cov=pages
```

### Offline Mode
The application supports offline mode for development and testing:

```bash
# Enable offline mode
export ECONOMIC_DASHBOARD_OFFLINE=true
streamlit run app.py

# Or on Windows
set ECONOMIC_DASHBOARD_OFFLINE=true
streamlit run app.py
```

In offline mode, the app uses pre-generated sample data instead of calling external APIs.

### CI/CD
The project includes GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that:
- Runs tests on every push and pull request
- Checks code syntax
- Validates dependencies
- Ensures deployment readiness

## � Offline Mode & Caching

The dashboard includes robust offline mode and caching capabilities for reliable operation.

### Offline Mode
When internet connectivity is limited or for development/testing, enable offline mode:

```bash
# Linux/macOS
export ECONOMIC_DASHBOARD_OFFLINE=true
streamlit run app.py

# Windows PowerShell
$env:ECONOMIC_DASHBOARD_OFFLINE="true"
streamlit run app.py

# Windows Command Prompt
set ECONOMIC_DASHBOARD_OFFLINE=true
streamlit run app.py
```

### Sample Data Generation
Generate sample datasets for offline testing:

```bash
python generate_sample_data.py
```

This creates:
- `data/sample_fred_data.csv`: Economic indicators (GDP, inflation, etc.)
- `data/sample_*_data.csv`: Stock market data for major indices
- `data/sample_world_bank_gdp.csv`: Global GDP growth data

### Data Caching
The application automatically caches API responses to reduce load times and API calls:

- **Cache Location**: `data/cache/`
- **Cache Duration**: 24 hours (configurable in `config.py`)
- **Cache Types**: FRED data, Yahoo Finance data, World Bank data, calculated values

### Features in Offline Mode
- ✅ All dashboard functionality works
- ✅ Realistic sample data with proper time series
- ✅ Data visualization and analysis tools
- ✅ Sidebar shows offline mode status
- ⚠️ Data is simulated, not real-time

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
- U.S. Securities and Exchange Commission (SEC) for EDGAR API and financial datasets
- Streamlit team for the amazing framework
- Plotly for powerful visualization tools

## 📞 Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

Built with ❤️ using Streamlit, Plotly, and Python