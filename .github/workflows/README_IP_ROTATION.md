# IP Rotation Implementation Instructions

This directory contains optional workflow templates for implementing time-based IP rotation to avoid Yahoo Finance rate limits.

## Current Setup ✅

Your workflow already includes:
1. ✅ Proxy support (via `PROXY_URL` secret)
2. ✅ Smart 24-hour caching
3. ✅ Batch processing with delays
4. ✅ Fallback to expired cache

## Option 1: Add a Proxy Service (Recommended if rate limited)

### Step 1: Choose a Proxy Service
- **Webshare** ($2.99/month) - Best value
- **ScraperAPI** ($29/month) - Most reliable
- **Smartproxy** ($12.5/month) - Residential IPs

### Step 2: Add Proxy to GitHub
1. Go to your GitHub repository
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `PROXY_URL`
5. Value: `http://username:password@proxy.example.com:port`
   (Get this from your proxy provider)
6. Click **Add secret**

### Step 3: Test
The workflow is already configured to use the proxy automatically. Just trigger a manual run:
1. Go to **Actions** tab
2. Select **Daily Data Refresh**
3. Click **Run workflow**
4. Check logs for successful data fetching

**That's it!** No code changes needed.

---

## Option 2: Time-Spacing Workflows (Free alternative)

If you want to spread data fetching over time instead of using a proxy:

### Step 1: Activate Template Workflows

Rename the template files to activate them:

```bash
# In your repository root
mv .github/workflows/data-refresh-fred.yml.template .github/workflows/data-refresh-fred.yml
mv .github/workflows/data-refresh-stocks.yml.template .github/workflows/data-refresh-stocks.yml
mv .github/workflows/data-refresh-sectors.yml.template .github/workflows/data-refresh-sectors.yml
```

### Step 2: Update Main Workflow

Either:
- **Option A:** Delete `.github/workflows/data-refresh.yml` (use only split workflows)
- **Option B:** Keep it for manual runs, disable the schedule

To disable schedule in main workflow:
```yaml
on:
  # schedule:  # Commented out - using split workflows instead
  #   - cron: '0 6 * * *'
  
  # Keep manual trigger
  workflow_dispatch:
```

### Step 3: Update Scripts (Optional)

The template workflows pass `--source` flag to the refresh script. You'll need to update `scripts/refresh_data.py` to support this:

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--source', choices=['fred', 'stocks', 'sectors', 'all'], default='all')
args = parser.parse_args()

if args.source in ['fred', 'all']:
    # Refresh FRED data
    pass

if args.source in ['stocks', 'all']:
    # Refresh stock data
    pass

if args.source in ['sectors', 'all']:
    # Refresh sector data
    pass
```

### Schedule:
- **6:00 AM UTC** - FRED data (fastest, no rate limits)
- **6:30 AM UTC** - Stock data (30 min gap)
- **7:00 AM UTC** - Sector ETFs (1 hour gap)

This spreads requests over 1 hour, reducing rate limit risk.

---

## Recommendation

### If currently working fine:
✅ **Do nothing** - Your current caching is sufficient

### If seeing occasional rate limits:
🔄 **Implement time-spacing** (Option 2) - Free solution

### If seeing frequent rate limits:
💰 **Add proxy service** (Option 1) - Costs $3-30/month

---

## Testing Your Setup

### Test Proxy (if added):
```bash
# Set environment variable
export PROXY_URL="http://user:pass@proxy.example.com:port"

# Test with Python
python -c "import os, requests; print(requests.get('http://httpbin.org/ip', proxies={'http': os.environ['PROXY_URL']}).json())"
```

Should show your proxy's IP, not your real IP.

### Test Workflow:
1. Go to **Actions** tab in GitHub
2. Select a workflow
3. Click **Run workflow** → **Run workflow**
4. Watch the logs for:
   - ✅ `Successfully downloaded data for XLK`
   - ❌ `YFRateLimitError` (means you need stronger solution)

### Monitor Results:
Check workflow summaries for:
- Cache creation status
- Error messages
- Data completeness

---

## Troubleshooting

### Proxy not working?
1. Check format: `http://` not `https://` for HTTP proxies
2. Verify credentials in proxy dashboard
3. Test proxy locally first

### Still rate limited with proxy?
1. Increase delays in `config_settings.py`:
   ```python
   YFINANCE_RATE_LIMIT_DELAY = 1.0  # Increase to 1 second
   ```
2. Try residential proxies instead of datacenter proxies
3. Contact proxy provider about Yahoo Finance compatibility

### Time-spacing not enough?
1. Increase gaps between workflows (e.g., 2 hours apart)
2. Combine with proxy service
3. Reduce batch size to 3 tickers

---

## Cost Analysis

| Solution | Monthly Cost | Setup Time | Maintenance |
|----------|--------------|------------|-------------|
| Current (caching only) | $0 | Done ✅ | None |
| + Time-spacing | $0 | 10 min | None |
| + Webshare Proxy | $3 | 5 min | None |
| + ScraperAPI | $29 | 5 min | None |

**Most cost-effective:** Try time-spacing first (free), add proxy if needed ($3/month).

---

## Support

If you need help:
1. Check `docs/IP_ROTATION_GUIDE.md` for detailed explanations
2. Review GitHub Actions logs for error messages
3. Test proxy configuration locally before using in Actions
4. Monitor for 1 week before deciding to add paid services

**Remember:** Your current setup with 24-hour caching should handle most cases. Only add these enhancements if you're consistently hitting rate limits in the workflow logs.
