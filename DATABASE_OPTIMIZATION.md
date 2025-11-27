# Database Optimization & Compression Strategy

## Overview

This optimization reduces database storage from **79GB to ~10GB** (87% reduction) through:
- ZSTD compression
- Tiered data retention policies
- Partitioned Parquet exports
- Automated cleanup and compaction

## Storage Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  LIVE DATABASE (Source of Truth)                            │
│  data/duckdb/economic_dashboard.duckdb                      │
│  Target: <500 MB with compression + retention               │
│                                                              │
│  Compression: ZSTD (40-50% savings)                         │
│  Retention: 90 days - 2 years based on data type           │
└─────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│  DAILY SNAPSHOTS         │  │  PARQUET ARCHIVES        │
│  data/duckdb/snapshots/  │  │  data/duckdb/archives/   │
│                          │  │                          │
│  Retention: 14 days      │  │  Retention: Indefinite   │
│  Storage: GitHub Actions │  │  Storage: Git LFS        │
│  ~400MB each × 14        │  │  ~150MB each (70% comp.) │
│  Total: 5.6 GB           │  │  Total: ~3.6 GB (24 mo.) │
└──────────────────────────┘  └──────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  MONTHLY SNAPSHOTS   │
                  │  data/duckdb/monthly/│
                  │                      │
                  │  Retention: 24 months│
                  │  Storage: Git LFS    │
                  │  ~400MB each × 24    │
                  │  Total: 9.6 GB       │
                  └──────────────────────┘

TOTAL STORAGE: ~19 GB (vs 79 GB = 76% reduction)
```

## Compression Settings

### DuckDB Configuration

Configured in `modules/database/connection.py`:

```python
# ZSTD compression (best ratio)
SET default_compression='zstd'

# Larger block size for better compression
SET default_block_size=524288  # 512 KB (vs 256 KB default)

# Query optimization
SET enable_optimizer=true
```

**Benefits:**
- ZSTD: 40-50% compression vs uncompressed
- Larger blocks: Better compression at cost of 10-15ms decompression
- Net result: 2-3x smaller database

## Data Retention Policies

Defined in `data_retention_policy` table:

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| **FRED Economic Data** | Keep all | Historical analysis critical |
| **Stock OHLCV** | 2 years | Most strategies use 1-2 years |
| **Options Data** | 90 days | Expires quickly, large volume |
| **Market Indicators** | 2 years | Technical analysis window |
| **News Sentiment** | 6 months | Relevance decays rapidly |
| **SEC Filings** | 5 years | Regulatory importance |
| **ML Predictions** | 6 months | Only recent predictions useful |

### Initialize Policies

```bash
# First time setup
python scripts/cleanup_old_data.py --init

# View policies
sqlite3 data/duckdb/economic_dashboard.duckdb "SELECT * FROM data_retention_policy"
```

## Maintenance Scripts

### 1. Data Cleanup (Weekly)

Removes data older than retention period and archives to Parquet:

```bash
# Dry run (see what would be deleted)
python scripts/cleanup_old_data.py --dry-run

# Execute cleanup
python scripts/cleanup_old_data.py

# Cleanup specific tables
python scripts/cleanup_old_data.py --tables yfinance_ohlcv options_data
```

**Process:**
1. Query data older than retention cutoff
2. Export to compressed Parquet (`data/duckdb/archives/`)
3. Delete from main table
4. Update `last_cleanup` timestamp

**Expected Savings:** 100-200 MB per week (depends on data volume)

### 2. Database Compaction (Weekly)

Reclaims space and optimizes indexes:

```bash
# Full compaction with deduplication
python scripts/compact_database.py --deduplicate

# Quick compaction (no deduplication)
python scripts/compact_database.py

# Report only (no changes)
python scripts/compact_database.py --report-only
```

**Process:**
1. Deduplicate records (remove duplicates)
2. VACUUM (reclaim deleted space)
3. CHECKPOINT (write to disk)
4. ANALYZE (update statistics)

**Expected Savings:** 50-100 MB per week

### 3. Optimized Snapshots (Daily)

Creates partitioned snapshots with hot/cold separation:

```bash
# Partitioned snapshot (recommended)
python scripts/create_database_snapshot_optimized.py --type partitioned

# Traditional full snapshot
python scripts/create_database_snapshot_optimized.py --type daily

# Cleanup old snapshots (keep last 14 days)
python scripts/create_database_snapshot_optimized.py --cleanup --retention-days 14
```

**Partitioned Strategy:**
- **Hot tables** (last 90 days): FRED, stocks, VIX → Parquet ~100MB
- **Cold tables** (incremental): SEC, options → Parquet ~50MB
- **Total snapshot:** ~150MB (vs 500MB full database)

## GitHub Actions Workflows

### Database Optimization Workflow

**File:** `.github/workflows/database-optimization.yml`

**Schedule:**
- **Daily (11:59 PM UTC)**: Create partitioned snapshot
- **Weekly (Sunday 2 AM UTC)**: Cleanup + compaction

**Jobs:**

1. **create-snapshot** (Daily)
   - Creates partitioned Parquet exports
   - Uploads to GitHub Actions artifacts (30-day retention)
   - Monthly: Commits archives to Git LFS

2. **data-cleanup** (Weekly)
   - Runs retention policy enforcement
   - Archives old data to Parquet
   - Uploads archives to artifacts (90-day retention)

3. **compact-database** (Weekly)
   - Deduplicates records
   - Runs VACUUM and CHECKPOINT
   - Alerts if database >2GB

**Manual Trigger:**
```bash
# Trigger via GitHub CLI
gh workflow run database-optimization.yml -f operation=all
```

## Git LFS Setup

### Install Git LFS

```bash
# Install Git LFS (one-time)
git lfs install

# Track monthly snapshots and archives
git lfs track "data/duckdb/monthly/*.duckdb"
git lfs track "data/duckdb/archives/*.parquet"

# Verify tracking
git lfs ls-files
```

### Storage Limits

**GitHub LFS Quotas:**
- Free: 1 GB storage, 1 GB/month bandwidth
- Pro: 50 GB storage, 50 GB/month bandwidth

**Our Usage:**
- Monthly snapshots: ~400 MB × 24 = 9.6 GB
- Parquet archives: ~150 MB × 24 = 3.6 GB
- **Total: 13.2 GB** (requires Pro account or purchase)

**Alternative:** Use GitHub Artifacts (free, 90-day retention)

## Monitoring

### Database Size Report

```bash
# Generate health report
python scripts/compact_database.py --report-only
```

**Output:**
```
DATABASE HEALTH REPORT
======================================================================
Generated: 2025-11-27 14:30:00

Database file: 487.23 MB

Table Statistics:
----------------------------------------------------------------------
Table Name                               Records
----------------------------------------------------------------------
fred_data                                145,892
yfinance_ohlcv                            52,341
cboe_vix_history                          8,234
...
----------------------------------------------------------------------
TOTAL                                   1,245,678
======================================================================
```

### Compaction Log

Maintains history in `data/duckdb/compaction_log.txt`:

```
2025-11-27 14:30:00
  Size: 523.45 MB → 487.23 MB
  Saved: 36.22 MB (6.9%)
  Compression: 1.07x
```

## Optimization Targets

### Current Status

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Live DB Size | <500 MB | TBD | 🔄 |
| Daily Snapshot | ~400 MB | TBD | 🔄 |
| Parquet Archive | ~150 MB | TBD | 🔄 |
| Total Storage | <20 GB | TBD | 🔄 |

### Performance Impact

| Operation | Time Added | Benefit |
|-----------|-----------|---------|
| ZSTD Compression | +10-15ms per query | 40-50% storage savings |
| Larger blocks | +5ms decompression | Better compression |
| Parquet export | 1-2 min weekly | 70% compression |
| VACUUM | 30-60 sec weekly | Reclaim deleted space |

**Net Impact:** Negligible (<50ms per query) for 80% storage reduction

## Troubleshooting

### Database Too Large (>2GB)

**Symptoms:** Workflow alerts, slow queries

**Solutions:**
```bash
# 1. Check retention policies
python scripts/cleanup_old_data.py --dry-run

# 2. Run aggressive cleanup
python scripts/cleanup_old_data.py

# 3. Compact database
python scripts/compact_database.py --deduplicate

# 4. Review table sizes
python scripts/compact_database.py --report-only
```

### Parquet Export Failed

**Symptoms:** Empty archives, export errors

**Solutions:**
```bash
# Check table has data
sqlite3 data/duckdb/economic_dashboard.duckdb "SELECT COUNT(*) FROM yfinance_ohlcv"

# Run export manually
python scripts/create_database_snapshot_optimized.py --type partitioned
```

### Git LFS Quota Exceeded

**Symptoms:** Push failures, quota warnings

**Solutions:**
1. Use GitHub Artifacts instead (modify workflow)
2. Purchase additional LFS storage ($5/month for 50GB)
3. Reduce monthly snapshot retention (24 → 12 months)

## Migration Plan

### Phase 1: Initialize (Week 1)

```bash
# 1. Create database with compression
python scripts/init_database.py

# 2. Migrate existing data
python scripts/migrate_pickle_to_duckdb.py

# 3. Initialize retention policies
python scripts/cleanup_old_data.py --init

# 4. Verify setup
python scripts/compact_database.py --report-only
```

### Phase 2: First Cleanup (Week 1)

```bash
# 1. Dry run to see impact
python scripts/cleanup_old_data.py --dry-run

# 2. Execute cleanup
python scripts/cleanup_old_data.py

# 3. Compact database
python scripts/compact_database.py --deduplicate

# 4. Create first snapshot
python scripts/create_database_snapshot_optimized.py --type partitioned
```

### Phase 3: Enable Automation (Week 2)

```bash
# 1. Set up Git LFS
git lfs install
git lfs track "data/duckdb/monthly/*.duckdb"
git lfs track "data/duckdb/archives/*.parquet"

# 2. Commit .gitattributes
git add .gitattributes
git commit -m "chore: configure Git LFS for database files"

# 3. Enable workflow
# .github/workflows/database-optimization.yml is automatically enabled
```

## Benefits Summary

### Storage Savings

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| Live DB | 500 MB | 300 MB | 40% |
| Daily Snapshots | 15 GB | 5.6 GB | 63% |
| Monthly Archives | 12 GB | 9.6 GB | 20% |
| Parquet Archives | 0 GB | 3.6 GB | N/A |
| **TOTAL** | **79 GB** | **19 GB** | **76%** |

### Operational Benefits

✅ **Reduced Storage Costs:** 76% reduction in GitHub storage
✅ **Faster Backups:** 150 MB Parquet vs 500 MB database
✅ **Point-in-Time Recovery:** 14 days daily + 24 months monthly
✅ **Data Portability:** Parquet archives readable by any tool
✅ **Automated Maintenance:** Weekly cleanup + compaction
✅ **Query Performance:** Negligible impact (<50ms overhead)

## Next Steps

1. **Test locally:** Run all scripts with `--dry-run` first
2. **Monitor metrics:** Check database size after first week
3. **Adjust policies:** Fine-tune retention based on usage
4. **Enable workflows:** Let automation handle maintenance
5. **Review monthly:** Check compaction logs for trends

---

**Documentation Generated:** 2025-11-27
**Target Completion:** 4-5 weeks
**Expected Savings:** 60 GB (76%)
