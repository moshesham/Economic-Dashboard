<div align="center">

# 📊 Economic Dashboard

### Professional-Grade Financial Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![FRED API](https://img.shields.io/badge/FRED-API-00529B?style=for-the-badge)](https://fred.stlouisfed.org/)

**A comprehensive, real-time economic intelligence platform for tracking US macroeconomic indicators, market performance, and financial trends.**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

---

</div>

## 🎯 Overview

The **Economic Dashboard** is an enterprise-grade analytical platform designed for financial professionals, economists, and data enthusiasts. It provides real-time access to over **60+ economic indicators** sourced from the Federal Reserve Economic Data (FRED) and Yahoo Finance, presented through an intuitive, modern interface.

### Why Economic Dashboard?

| Feature | Benefit |
|---------|---------|
| 📈 **Real-Time Data** | Live economic indicators updated automatically |
| 🎨 **Modern UI/UX** | Professional dark theme with responsive design |
| 🔒 **Secure** | Encrypted API key storage with industry standards |
| ⚡ **High Performance** | Intelligent caching for lightning-fast load times |
| 📱 **Responsive** | Works seamlessly across desktop and tablet |

---

## ✨ Features

### 📊 Core Analytics Modules

<table>
<tr>
<td width="50%">

#### 🏛️ Macroeconomic Dashboard
- **GDP & Growth Metrics** — Real GDP, GDP components, productivity indices
- **Inflation Tracking** — CPI, Core CPI, PCE, PPI with YoY comparisons
- **Employment Analytics** — Unemployment, payrolls, labor force participation
- **Consumer Insights** — Personal consumption, savings rates, retail sales

</td>
<td width="50%">

#### 📈 Market Intelligence
- **Global Indices** — S&P 500, NASDAQ, Dow Jones, FTSE, Nikkei, DAX
- **Sector Heatmaps** — Visual sector performance analysis
- **Technical Analysis** — Advanced charting with indicators
- **Correlation Matrix** — Cross-market relationship analysis

</td>
</tr>
<tr>
<td width="50%">

#### 🏠 Housing & Consumer
- **Housing Starts** — New construction activity tracking
- **Mortgage Rates** — 30-year fixed rate trends
- **Consumer Confidence** — Sentiment indicators
- **Personal Savings** — Savings rate monitoring

</td>
<td width="50%">

#### 💹 Interest Rates & Treasury
- **Federal Funds Rate** — Fed policy tracking
- **Treasury Yields** — 2Y, 5Y, 10Y, 30Y curves
- **Yield Curve Analysis** — Inversion detection
- **Breakeven Inflation** — Market expectations

</td>
</tr>
</table>

### 🛠️ Platform Capabilities

- **🔑 Secure API Management** — Encrypted storage for FRED, Yahoo Finance, and more
- **🔄 Automated Data Refresh** — Daily updates via GitHub Actions or Apache Airflow
- **📊 Interactive Visualizations** — Powered by Plotly with zoom, pan, and hover details
- **💾 Smart Caching** — 24-hour intelligent cache for optimal performance
- **🌐 Offline Mode** — Full functionality with sample data for development

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** — [Download Python](https://python.org)
- **pip** — Python package manager (included with Python)
- **Git** — [Download Git](https://git-scm.com)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/moshesham/Economic-Dashboard.git
cd Economic-Dashboard

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the dashboard
streamlit run app.py
```

The dashboard will automatically open at **http://localhost:8501**

### 🔐 API Configuration (Recommended)

For enhanced rate limits and reliability, configure your API keys:

```bash
# Quick setup with guided prompts
python quickstart_api_keys.py

# Or use the setup script
python setup_credentials.py
```

> **💡 Pro Tip:** API keys are encrypted using industry-standard encryption and stored securely.

---

## 📖 Documentation

### 📂 Project Architecture

```
Economic-Dashboard/
├── 📱 app.py                    # Main application entry point
├── 📁 pages/                    # Dashboard pages
│   ├── 1_GDP_and_Growth.py
│   ├── 2_Inflation_and_Prices.py
│   ├── 3_Employment_and_Wages.py
│   ├── 4_Consumer_and_Housing.py
│   ├── 5_Markets_and_Rates.py
│   ├── 6_API_Key_Management.py
│   ├── 7_Market_Indices.py
│   ├── 8_Stock_Technical_Analysis.py
│   └── 9_News_Sentiment.py
├── 📁 modules/                  # Core functionality
│   ├── data_loader.py           # Data fetching & caching
│   ├── technical_analysis.py    # TA indicators
│   ├── sentiment_analysis.py    # News sentiment
│   └── auth/                    # Authentication
├── 📁 .streamlit/               # Streamlit configuration
│   └── config.toml              # Theme & settings
├── 📁 docs/                     # Documentation
├── 📁 tests/                    # Test suite
└── 📁 data/                     # Cache & sample data
```

### 🎨 Theme Configuration

Customize the dashboard appearance in `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#0068c9"
backgroundColor = "#040f26"
secondaryBackgroundColor = "#081943"
textColor = "#ffffff"
font = "sans serif"
```

### 🧪 Testing

```bash
# Run full test suite
python test_locally.py

# Run pytest with verbose output
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=modules --cov=pages
```

### 🔌 Offline Mode

Enable offline mode for development or limited connectivity:

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

---

## 📊 Data Sources

| Source | Data Types | Update Frequency |
|--------|------------|------------------|
| **FRED** | GDP, CPI, Employment, Interest Rates | Daily |
| **Yahoo Finance** | Stock prices, Market indices | Real-time |
| **World Bank** | International GDP comparisons | Quarterly |

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please read our contributing guidelines and ensure tests pass before submitting.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

<div align="center">

**Moshe Sham**

[![GitHub](https://img.shields.io/badge/GitHub-moshesham-181717?style=flat-square&logo=github)](https://github.com/moshesham)

</div>

---

## 🙏 Acknowledgments

<div align="center">

**Powered by industry-leading technologies**

[![FRED](https://img.shields.io/badge/Federal_Reserve-FRED_API-00529B?style=flat-square)](https://fred.stlouisfed.org/)
[![Yahoo Finance](https://img.shields.io/badge/Yahoo-Finance_API-6001D2?style=flat-square)](https://finance.yahoo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Framework-FF4B4B?style=flat-square&logo=streamlit)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-Visualizations-3F4F75?style=flat-square&logo=plotly)](https://plotly.com/)

</div>

---

<div align="center">

**Built with ❤️ for the financial community**

*Track • Analyze • Decide*

</div>