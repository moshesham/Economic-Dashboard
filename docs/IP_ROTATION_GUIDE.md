# IP Rotation Guide for GitHub Actions

## Problem
Yahoo Finance rate limits API requests by IP address. GitHub Actions runners use Azure IPs that may get rate limited when fetching multiple tickers (e.g., 11 sector ETFs).

## Solutions

### 🎯 Option 1: Smart Caching (Already Implemented ✅)
**Cost:** Free  
**Effectiveness:** High (70-90% reduction in API calls)  
**Complexity:** Low

**Current Implementation:**
- 24-hour caching for Yahoo Finance data
- Batch processing (5 tickers at a time)
- 0.5-second delays between requests
- Fallback to 1-week-old cache on rate limit

**Configuration:**
```python
# config_settings.py
YFINANCE_RATE_LIMIT_DELAY = 0.5  # seconds
YFINANCE_BATCH_SIZE = 5          # tickers per batch
YFINANCE_CACHE_HOURS = 24        # cache duration
```

This is usually sufficient for daily workflows since data is fetched once per day.

---

### 🔄 Option 2: Rotating Proxy Service
**Cost:** $5-50/month  
**Effectiveness:** Very High (95%+ success rate)  
**Complexity:** Medium

#### Recommended Services:
1. **Bright Data (formerly Luminati)** - $500/month (enterprise)
2. **ScraperAPI** - $29/month (hobby), $99/month (startup)
3. **Smartproxy** - $12.5/month (8GB residential)
4. **Webshare** - $2.99/month (10 proxies)

#### Setup Instructions:

##### A. Add Proxy to GitHub Secrets
1. Go to GitHub Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add `PROXY_URL` with format: `http://username:password@proxy.example.com:port`

##### B. Update Workflow (Already Added)
The workflow is already configured to use `PROXY_URL` if set:
```yaml
env:
  PROXY_URL: ${{ secrets.PROXY_URL }}
```

##### C. Code Support (Already Added)
The `data_loader.py` now automatically detects and uses proxy from environment:
```python
proxy_url = os.environ.get('PROXY_URL')
if proxy_url:
    os.environ['HTTP_PROXY'] = proxy_url
    os.environ['HTTPS_PROXY'] = proxy_url
```

---

### 🏃 Option 3: Multiple Workflow Runs (Time Spacing)
**Cost:** Free  
**Effectiveness:** Medium  
**Complexity:** Low

Spread data fetching across multiple time windows to avoid burst rate limits.

#### Implementation:

**Create separate workflows for different data types:**

**`.github/workflows/data-refresh-fred.yml`** - FRED data only
```yaml
name: FRED Data Refresh
on:
  schedule:
    - cron: '0 6 * * *'  # 6 AM UTC
```

**`.github/workflows/data-refresh-stocks.yml`** - Individual stocks
```yaml
name: Stock Data Refresh
on:
  schedule:
    - cron: '30 6 * * *'  # 6:30 AM UTC (30 min later)
```

**`.github/workflows/data-refresh-sectors.yml`** - Sector ETFs
```yaml
name: Sector Data Refresh
on:
  schedule:
    - cron: '0 7 * * *'  # 7 AM UTC (1 hour later)
```

This spreads out requests over 1 hour instead of hitting all at once.

---

### 🌐 Option 4: Self-Hosted Runner with VPN
**Cost:** $5-15/month (VPS + VPN)  
**Effectiveness:** High  
**Complexity:** High

Use a self-hosted runner with VPN that can rotate IPs.

#### Setup:
1. **Get VPS** (DigitalOcean, Linode, AWS EC2)
2. **Install VPN** (NordVPN, ExpressVPN with API)
3. **Configure Self-Hosted Runner**
4. **Script to Rotate VPN Connection**

**Example rotation script:**
```bash
#!/bin/bash
# Change VPN server every hour
nordvpn connect us  # Connects to random US server
python scripts/refresh_data.py
nordvpn disconnect
```

**Not recommended for most users** - adds maintenance overhead.

---

### 🎲 Option 5: GitHub Actions Matrix Strategy
**Cost:** Free  
**Effectiveness:** Low-Medium  
**Complexity:** Medium

Run the same workflow on multiple runner types to potentially get different IPs.

**`.github/workflows/data-refresh.yml`:**
```yaml
jobs:
  refresh-data:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, ubuntu-22.04, ubuntu-20.04]
      max-parallel: 1  # Run sequentially
      fail-fast: false
    steps:
      # ... existing steps ...
```

**Limitation:** GitHub may assign same datacenter/IP pool, so effectiveness varies.

---

## Recommended Approach

### For Most Users (Free):
1. ✅ **Use smart caching** (already implemented)
2. ✅ **Keep batch processing** (already implemented)
3. ✅ **Monitor failures** and adjust delays if needed

### If Still Rate Limited:
1. 🔄 **Add time-spacing** (Option 3) - Split into 3 workflows
2. 💰 **Consider cheap proxy** (Option 2) - Webshare at $2.99/month

### For Enterprise:
1. 💼 **Professional proxy service** (ScraperAPI, Bright Data)
2. 🏢 **Self-hosted runners** with managed IPs

---

## Testing Proxy Configuration

### Local Test:
```bash
# Set proxy environment variable
$env:PROXY_URL = "http://username:password@proxy.example.com:port"

# Run data refresh
python scripts/refresh_data.py
```

### GitHub Actions Test:
1. Add `PROXY_URL` to GitHub Secrets
2. Manually trigger workflow: Actions → Daily Data Refresh → Run workflow
3. Check logs for proxy usage (look for successful downloads)

---

## Monitoring Rate Limits

### Check Workflow Logs:
Look for these patterns in GitHub Actions logs:
- ✅ `Successfully downloaded data for XLK`
- ⚠️ `Rate limit detected, using cached data`
- ❌ `YFRateLimitError: Too Many Requests`

### Cache Statistics:
The workflow summary shows cache status:
- ✅ Yahoo Finance data cache created
- 💡 Using 24-hour cached data

---

## Cost Comparison

| Solution | Monthly Cost | Setup Time | Effectiveness |
|----------|--------------|------------|---------------|
| Smart Caching (current) | $0 | 0 min | 80% |
| Time Spacing | $0 | 15 min | 85% |
| Webshare Proxy | $3 | 10 min | 95% |
| ScraperAPI | $29 | 5 min | 99% |
| Self-Hosted + VPN | $15 | 120 min | 90% |

---

## Troubleshooting

### Still Getting Rate Limited?

1. **Increase delays:**
   ```python
   # config_settings.py
   YFINANCE_RATE_LIMIT_DELAY = 1.0  # Increase to 1 second
   ```

2. **Reduce batch size:**
   ```python
   YFINANCE_BATCH_SIZE = 3  # Reduce from 5 to 3
   ```

3. **Extend cache duration:**
   ```python
   YFINANCE_CACHE_HOURS = 48  # Use 48-hour cache
   ```

4. **Check if Yahoo Finance changed policies:**
   - Visit yfinance GitHub issues
   - Look for rate limit updates

### Proxy Not Working?

1. **Verify proxy format:**
   ```
   http://user:pass@host:port  ✅
   https://host:port           ✅
   host:port                   ❌ (missing protocol)
   ```

2. **Test proxy locally:**
   ```python
   import requests
   proxies = {'http': 'http://user:pass@host:port'}
   r = requests.get('http://httpbin.org/ip', proxies=proxies)
   print(r.json())  # Should show proxy IP
   ```

3. **Check proxy service status:**
   - Login to proxy provider dashboard
   - Verify subscription is active
   - Check usage limits

---

## Additional Resources

- [yfinance Rate Limiting Discussion](https://github.com/ranaroussi/yfinance/issues)
- [GitHub Actions IP Ranges](https://api.github.com/meta) - See `actions` key
- [Yahoo Finance Terms of Service](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html)
- [Rotating Proxies Guide](https://www.scraperapi.com/blog/rotating-proxies/)

---

## Current Status

✅ **Implemented:**
- Smart 24-hour caching
- Batch processing (5 tickers)
- Rate limit delays (0.5s)
- Fallback to week-old cache
- Proxy support in code
- Proxy configuration in workflow

🔜 **Optional Enhancements:**
- Time-spacing workflows (if needed)
- Paid proxy service (if budget allows)
- Advanced monitoring/alerts

**Recommendation:** Monitor current implementation for 1 week. If rate limits persist, implement time-spacing (free) or add Webshare proxy ($3/month).
