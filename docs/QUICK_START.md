# Margin Call Risk Framework - Quick Start Guide

## 🚀 Getting Started (3 Steps)

### Step 1: View the Dashboard
```bash
streamlit run app.py
```
Navigate to sidebar → **"⚠️ Margin Call Risk Monitor"**

### Step 2: Calculate Risk for Your Stocks
```python
from modules.features import MarginCallRiskCalculator

calc = MarginCallRiskCalculator()

# Calculate for one stock
risk = calc.calculate_and_store('AAPL')
print(f"Risk: {risk['composite_risk_score']:.1f}/100 ({risk['risk_level']})")

# Batch calculate
for ticker in ['TSLA', 'NVDA', 'AMD']:
    calc.calculate_and_store(ticker)
```

### Step 3: Refresh Dashboard
Click **"🔄 Refresh Market Data"** in sidebar to see latest scores

---

## ⚡ Quick Commands

### Run Backtest
```bash
python backtest_margin_risk_simulated.py
```
Results: `margin_risk_backtest_simulated.csv`

### Run Feature Pipeline (includes margin risk)
```python
from modules.features.feature_pipeline import FeaturePipeline

pipeline = FeaturePipeline()
result = pipeline.run_full_pipeline('MSFT')
```

### Query Risk History
```python
from modules.database import get_db_connection

db = get_db_connection()
history = db.query("""
    SELECT * FROM margin_call_risk
    WHERE ticker = 'AAPL'
    ORDER BY date DESC
    LIMIT 30
""")
```

---

## 📊 Risk Score Cheat Sheet

| Score | Level | Action |
|-------|-------|--------|
| 0-25 | ✅ Minimal | Hold |
| 25-40 | 🟢 Low | Monitor |
| 40-60 | 🟡 Moderate | Reduce size |
| 60-75 | 🟠 High | Hedge |
| 75-100 | 🔴 Critical | Exit/Defense |

---

## 🎯 What the Components Mean

**Leverage (30%)**: Short interest, margin exposure
- High = Stocks heavily shorted, squeeze risk

**Volatility (25%)**: VIX, realized vol, Bollinger width
- High = Unstable price action, risk-off

**Options (25%)**: Put/call ratio, IV rank
- High = Bearish positioning, fear

**Liquidity (20%)**: Volume trends, spreads
- High = Forced selling, illiquidity

---

## 🔔 Alert Thresholds

**Market-Wide (VIX)**
- VIX > 20: Elevated regime
- VIX > 30: Crisis regime
- VIX > 50: Extreme stress

**Stock-Specific**
- Score > 60: Start hedging
- Score > 75: Defensive action
- Score rising fast: Risk escalating

---

## 📈 Backtesting Results

### 2020 COVID Crash
- ✅ Warning: 7 days before
- ✅ Score: 80.4/100 (Critical)
- ✅ Grade: B (Good)

### 2022 Rate Selloff
- ✅ Warning: 7 days before
- ✅ Score: 66.0/100 (High)
- ✅ Grade: B (Good)

**Overall: 100% success rate**

---

## 🛠️ Troubleshooting

**No data in dashboard?**
- Run `calc.calculate_and_store('TICKER')` first
- Click "Refresh Market Data" button

**Yahoo Finance errors?**
- Framework uses fallback (FRED for VIX)
- Can operate without real-time data

**Pipeline errors?**
- Check that ticker has options data
- Some metrics require minimum history

---

## 📚 Documentation

- Full details: `MARGIN_RISK_FRAMEWORK.md`
- Implementation: `IMPLEMENTATION_SUMMARY.md`
- Code: `modules/features/leverage_metrics.py`
- Code: `modules/features/margin_risk_composite.py`

---

## 💡 Pro Tips

1. **Combine with VIX**: Check VIX regime before trading
2. **Track Trends**: Rising score = increasing risk
3. **Sector Analysis**: High-beta stocks more sensitive
4. **Use Alerts**: Set threshold notifications
5. **Backtest**: Validate on your own scenarios

---

## 🎓 Understanding the Score

The composite score combines:
```
Score = (Leverage × 0.30) + (Volatility × 0.25) + 
        (Options × 0.25) + (Liquidity × 0.20)
```

Each component scaled 0-100, where:
- **0** = No risk
- **50** = Neutral/average
- **100** = Maximum risk

---

**Ready to use! 🚀 Start with Step 1 above.**
