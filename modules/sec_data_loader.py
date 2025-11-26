"""
SEC Data Loading Module for Economic Dashboard.
Handles downloading and processing SEC EDGAR data including:
- Financial Statement Data Sets (quarterly XBRL data)
- Company Facts API (real-time company financials)
- Form 13F Holdings (institutional investor holdings)
- Fails-to-Deliver Data (settlement failures)
"""

import os
import io
import zipfile
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

# Import DuckDB database functions
try:
    from modules.database import get_db_connection
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

# SEC API Configuration
SEC_BASE_URL = "https://www.sec.gov"
SEC_DATA_URL = "https://data.sec.gov"
SEC_FSDS_URL = f"{SEC_BASE_URL}/files/dera/data/financial-statement-data-sets"
SEC_FTD_URL = f"{SEC_BASE_URL}/data/foiadocsfailsdocs"

# Required User-Agent for SEC API requests (per SEC guidelines)
SEC_USER_AGENT = "Economic-Dashboard/1.0 (contact@example.com)"
SEC_HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}

SEC_DATA_HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov"
}

# Rate limiting (SEC allows ~10 requests/second)
SEC_REQUEST_DELAY = 0.1  # 100ms between requests


def _get_cache_dir() -> Path:
    """Get the cache directory for SEC data."""
    cache_dir = Path(__file__).parent.parent / 'data' / 'cache' / 'sec'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _download_with_retry(url: str, headers: dict, max_retries: int = 3) -> Optional[requests.Response]:
    """Download a file from SEC with retry logic."""
    import time
    
    for attempt in range(max_retries):
        try:
            time.sleep(SEC_REQUEST_DELAY)  # Rate limiting
            response = requests.get(url, headers=headers, timeout=60)
            
            if response.status_code == 200:
                return response
            elif response.status_code == 404:
                return None
            elif response.status_code == 429:  # Rate limited
                wait_time = (attempt + 1) * 5
                time.sleep(wait_time)
            else:
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return None


# =============================================================================
# Financial Statement Data Sets (FSDS)
# =============================================================================

def download_financial_statement_data(year: int, quarter: int) -> Dict[str, pd.DataFrame]:
    """
    Download SEC Financial Statement Data Set for a specific quarter.
    
    Args:
        year: Year (e.g., 2024)
        quarter: Quarter (1-4)
        
    Returns:
        Dictionary containing DataFrames for:
        - 'sub': Submission data (company info, filing metadata)
        - 'num': Numeric data (financial statement values)
        - 'pre': Presentation data (how items are presented)
        - 'tag': Tag data (XBRL taxonomy information)
    """
    filename = f"{year}q{quarter}.zip"
    url = f"{SEC_FSDS_URL}/{filename}"
    
    # Check cache first
    cache_dir = _get_cache_dir()
    cache_file = cache_dir / filename
    
    try:
        if cache_file.exists():
            # Check if cache is less than 7 days old
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age < timedelta(days=7):
                with zipfile.ZipFile(cache_file, 'r') as zf:
                    return _parse_fsds_zip(zf)
        
        # Download fresh data
        response = _download_with_retry(url, SEC_HEADERS)
        
        if response is None:
            st.warning(f"Financial statement data for {year}Q{quarter} not available")
            return {}
        
        # Save to cache
        with open(cache_file, 'wb') as f:
            f.write(response.content)
        
        # Parse the data
        with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zf:
            return _parse_fsds_zip(zf)
            
    except Exception as e:
        st.error(f"Error downloading financial statement data: {e}")
        return {}


def _parse_fsds_zip(zf: zipfile.ZipFile) -> Dict[str, pd.DataFrame]:
    """Parse the Financial Statement Data Set ZIP file."""
    result = {}
    
    file_mapping = {
        'sub.txt': 'sub',
        'num.txt': 'num',
        'pre.txt': 'pre',
        'tag.txt': 'tag'
    }
    
    for filename, key in file_mapping.items():
        try:
            with zf.open(filename) as f:
                df = pd.read_csv(f, sep='\t', low_memory=False)
                result[key] = df
        except Exception as e:
            st.warning(f"Could not parse {filename}: {e}")
            result[key] = pd.DataFrame()
    
    return result


def get_company_financials(fsds_data: Dict[str, pd.DataFrame], 
                           cik: Optional[str] = None,
                           ticker: Optional[str] = None) -> pd.DataFrame:
    """
    Extract financial data for a specific company from FSDS data.
    
    Args:
        fsds_data: Dictionary from download_financial_statement_data()
        cik: Company CIK number (10-digit string)
        ticker: Stock ticker symbol
        
    Returns:
        DataFrame with company's financial statement values
    """
    if not fsds_data or 'sub' not in fsds_data or 'num' not in fsds_data:
        return pd.DataFrame()
    
    sub_df = fsds_data['sub']
    num_df = fsds_data['num']
    
    # Filter by CIK or ticker
    if cik:
        sub_filtered = sub_df[sub_df['cik'] == int(cik)]
    elif ticker:
        # Handle ticker matching (SEC uses uppercase)
        sub_filtered = sub_df[sub_df['instance'].str.upper().str.contains(ticker.upper(), na=False)]
    else:
        return pd.DataFrame()
    
    if sub_filtered.empty:
        return pd.DataFrame()
    
    # Get ADSHs (accession numbers) for this company
    adshs = sub_filtered['adsh'].unique()
    
    # Filter numeric data
    company_nums = num_df[num_df['adsh'].isin(adshs)]
    
    # Merge with submission info
    result = company_nums.merge(
        sub_filtered[['adsh', 'cik', 'name', 'form', 'filed', 'period']],
        on='adsh',
        how='left'
    )
    
    return result


# =============================================================================
# Company Facts API (Real-time XBRL Data)
# =============================================================================

def get_company_facts(cik: str) -> Dict[str, Any]:
    """
    Get all XBRL facts for a company using SEC's Company Facts API.
    
    Args:
        cik: Company CIK number (will be zero-padded to 10 digits)
        
    Returns:
        Dictionary containing all company facts organized by taxonomy
    """
    # Zero-pad CIK to 10 digits
    cik_padded = str(cik).zfill(10)
    url = f"{SEC_DATA_URL}/api/xbrl/companyfacts/CIK{cik_padded}.json"
    
    try:
        response = _download_with_retry(url, SEC_DATA_HEADERS)
        
        if response is None:
            st.warning(f"Company facts not available for CIK {cik}")
            return {}
        
        return response.json()
        
    except Exception as e:
        st.error(f"Error fetching company facts: {e}")
        return {}


def extract_financial_metric(company_facts: Dict, 
                              concept: str,
                              taxonomy: str = "us-gaap") -> pd.DataFrame:
    """
    Extract a specific financial metric from company facts.
    
    Args:
        company_facts: Dictionary from get_company_facts()
        concept: XBRL concept name (e.g., 'Revenues', 'Assets', 'NetIncomeLoss')
        taxonomy: XBRL taxonomy (default: 'us-gaap')
        
    Returns:
        DataFrame with historical values for the concept
    """
    try:
        facts = company_facts.get('facts', {})
        taxonomy_facts = facts.get(taxonomy, {})
        concept_data = taxonomy_facts.get(concept, {})
        
        if not concept_data:
            return pd.DataFrame()
        
        # Get units (usually USD for monetary values)
        units = concept_data.get('units', {})
        
        all_values = []
        for unit_type, values in units.items():
            for value in values:
                record = {
                    'concept': concept,
                    'unit': unit_type,
                    'value': value.get('val'),
                    'end_date': value.get('end'),
                    'start_date': value.get('start'),
                    'fiscal_year': value.get('fy'),
                    'fiscal_period': value.get('fp'),
                    'form': value.get('form'),
                    'filed': value.get('filed'),
                    'accn': value.get('accn')
                }
                all_values.append(record)
        
        df = pd.DataFrame(all_values)
        
        if not df.empty:
            df['end_date'] = pd.to_datetime(df['end_date'])
            df['filed'] = pd.to_datetime(df['filed'])
            df = df.sort_values('end_date', ascending=False)
        
        return df
        
    except Exception as e:
        st.warning(f"Could not extract {concept}: {e}")
        return pd.DataFrame()


def get_key_financials(cik: str) -> pd.DataFrame:
    """
    Get key financial metrics for a company.
    
    Args:
        cik: Company CIK number
        
    Returns:
        DataFrame with key financial metrics (Revenue, Net Income, Assets, etc.)
    """
    company_facts = get_company_facts(cik)
    
    if not company_facts:
        return pd.DataFrame()
    
    # Key concepts to extract
    key_concepts = [
        'Revenues',
        'RevenueFromContractWithCustomerExcludingAssessedTax',
        'NetIncomeLoss',
        'Assets',
        'Liabilities',
        'StockholdersEquity',
        'OperatingIncomeLoss',
        'GrossProfit',
        'CashAndCashEquivalentsAtCarryingValue',
        'LongTermDebt',
        'EarningsPerShareBasic',
        'EarningsPerShareDiluted'
    ]
    
    all_data = []
    
    for concept in key_concepts:
        df = extract_financial_metric(company_facts, concept)
        if not df.empty:
            # Get only 10-K and 10-Q filings
            df_filtered = df[df['form'].isin(['10-K', '10-Q'])]
            if not df_filtered.empty:
                all_data.append(df_filtered)
    
    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        return result
    
    return pd.DataFrame()


# =============================================================================
# Company Submissions (Filing History)
# =============================================================================

def get_company_submissions(cik: str) -> Dict[str, Any]:
    """
    Get filing submission history for a company.
    
    Args:
        cik: Company CIK number
        
    Returns:
        Dictionary containing company info and filing history
    """
    cik_padded = str(cik).zfill(10)
    url = f"{SEC_DATA_URL}/submissions/CIK{cik_padded}.json"
    
    try:
        response = _download_with_retry(url, SEC_DATA_HEADERS)
        
        if response is None:
            st.warning(f"Submissions not available for CIK {cik}")
            return {}
        
        return response.json()
        
    except Exception as e:
        st.error(f"Error fetching company submissions: {e}")
        return {}


def get_recent_filings(cik: str, form_types: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Get recent SEC filings for a company.
    
    Args:
        cik: Company CIK number
        form_types: List of form types to filter (e.g., ['10-K', '10-Q', '8-K'])
        
    Returns:
        DataFrame with recent filings
    """
    submissions = get_company_submissions(cik)
    
    if not submissions:
        return pd.DataFrame()
    
    try:
        # Extract recent filings
        recent = submissions.get('filings', {}).get('recent', {})
        
        if not recent:
            return pd.DataFrame()
        
        df = pd.DataFrame(recent)
        
        # Filter by form type if specified
        if form_types:
            df = df[df['form'].isin(form_types)]
        
        # Convert dates
        if 'filingDate' in df.columns:
            df['filingDate'] = pd.to_datetime(df['filingDate'])
        if 'reportDate' in df.columns:
            df['reportDate'] = pd.to_datetime(df['reportDate'])
        
        # Add company info
        df['cik'] = cik
        df['company_name'] = submissions.get('name', '')
        df['tickers'] = str(submissions.get('tickers', []))
        
        return df
        
    except Exception as e:
        st.warning(f"Could not parse filings: {e}")
        return pd.DataFrame()


# =============================================================================
# Form 13F Holdings Data
# =============================================================================

def get_13f_holdings(cik: str, filing_date: Optional[str] = None) -> pd.DataFrame:
    """
    Get Form 13F holdings for an institutional investment manager.
    
    Note: This requires parsing the actual 13F-HR filings, which is more complex.
    For now, returns filing information. Full parsing can be added later.
    
    Args:
        cik: Institution CIK number
        filing_date: Optional specific filing date
        
    Returns:
        DataFrame with 13F filing information
    """
    filings = get_recent_filings(cik, form_types=['13F-HR', '13F-HR/A'])
    return filings


# =============================================================================
# Fails-to-Deliver Data
# =============================================================================

def download_fails_to_deliver(year: int, half: int) -> pd.DataFrame:
    """
    Download Fails-to-Deliver data from SEC.
    
    Args:
        year: Year (e.g., 2024)
        half: 1 for first half (Jan-Jun), 2 for second half (Jul-Dec)
        
    Returns:
        DataFrame with fails-to-deliver records
    """
    # SEC provides FTD data in semi-annual files
    suffix = "a" if half == 1 else "b"
    filename = f"cnsfails{year}{half:02d}{suffix}.zip"
    url = f"{SEC_FTD_URL}/{filename}"
    
    # Check cache first
    cache_dir = _get_cache_dir()
    cache_file = cache_dir / filename
    
    try:
        if cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age < timedelta(days=30):
                with zipfile.ZipFile(cache_file, 'r') as zf:
                    return _parse_ftd_zip(zf)
        
        response = _download_with_retry(url, SEC_HEADERS)
        
        if response is None:
            st.warning(f"Fails-to-deliver data for {year} H{half} not available")
            return pd.DataFrame()
        
        with open(cache_file, 'wb') as f:
            f.write(response.content)
        
        with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zf:
            return _parse_ftd_zip(zf)
            
    except Exception as e:
        st.error(f"Error downloading fails-to-deliver data: {e}")
        return pd.DataFrame()


def _parse_ftd_zip(zf: zipfile.ZipFile) -> pd.DataFrame:
    """Parse fails-to-deliver ZIP file."""
    all_data = []
    
    for filename in zf.namelist():
        if filename.endswith('.txt'):
            try:
                with zf.open(filename) as f:
                    df = pd.read_csv(
                        f, 
                        sep='|',
                        encoding='latin-1',
                        low_memory=False
                    )
                    all_data.append(df)
            except Exception as e:
                st.warning(f"Could not parse {filename}: {e}")
    
    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        
        # Clean column names
        result.columns = result.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Convert date column if present
        if 'settlement_date' in result.columns:
            result['settlement_date'] = pd.to_datetime(result['settlement_date'], format='%Y%m%d', errors='coerce')
        
        return result
    
    return pd.DataFrame()


# =============================================================================
# CIK Lookup
# =============================================================================

@st.cache_data(ttl=86400)  # Cache for 24 hours
def lookup_cik(ticker: str) -> Optional[str]:
    """
    Look up a company's CIK number by ticker symbol.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        CIK number as string, or None if not found
    """
    url = f"{SEC_DATA_URL}/submissions/CIK{ticker.upper()}.json"
    
    # First try direct lookup (some tickers work directly)
    try:
        response = _download_with_retry(url, SEC_DATA_HEADERS)
        if response:
            data = response.json()
            return str(data.get('cik', '')).zfill(10)
    except Exception:
        pass
    
    # Try the company tickers JSON file
    try:
        tickers_url = f"{SEC_DATA_URL}/company_tickers.json"
        response = _download_with_retry(tickers_url, SEC_DATA_HEADERS)
        
        if response:
            tickers_data = response.json()
            
            for entry in tickers_data.values():
                if entry.get('ticker', '').upper() == ticker.upper():
                    return str(entry.get('cik_str', '')).zfill(10)
    except Exception as e:
        st.warning(f"CIK lookup failed: {e}")
    
    return None


@st.cache_data(ttl=86400)
def get_company_tickers() -> pd.DataFrame:
    """
    Get a list of all company tickers and CIKs from SEC.
    
    Returns:
        DataFrame with columns: cik, ticker, title
    """
    url = f"{SEC_DATA_URL}/company_tickers.json"
    
    try:
        response = _download_with_retry(url, SEC_DATA_HEADERS)
        
        if response:
            data = response.json()
            df = pd.DataFrame(data.values())
            df.columns = ['cik', 'ticker', 'title']
            df['cik'] = df['cik'].astype(str).str.zfill(10)
            return df
    except Exception as e:
        st.error(f"Error fetching company tickers: {e}")
    
    return pd.DataFrame()


# =============================================================================
# Database Integration Functions
# =============================================================================

def save_financial_statements_to_db(fsds_data: Dict[str, pd.DataFrame], 
                                    year: int, 
                                    quarter: int) -> int:
    """
    Save Financial Statement Data Sets to DuckDB.
    
    Args:
        fsds_data: Dictionary from download_financial_statement_data()
        year: Year of the data
        quarter: Quarter of the data
        
    Returns:
        Number of records saved
    """
    if not DUCKDB_AVAILABLE:
        st.warning("DuckDB not available for saving SEC data")
        return 0
    
    db = get_db_connection()
    total_records = 0
    
    # Save numeric data (main financial values)
    if 'num' in fsds_data and not fsds_data['num'].empty:
        num_df = fsds_data['num'].copy()
        num_df['data_year'] = year
        num_df['data_quarter'] = quarter
        
        try:
            db.insert_df(num_df, 'sec_financial_statements', if_exists='append')
            total_records += len(num_df)
        except Exception as e:
            st.warning(f"Could not save numeric data: {e}")
    
    # Save submission metadata
    if 'sub' in fsds_data and not fsds_data['sub'].empty:
        sub_df = fsds_data['sub'].copy()
        sub_df['data_year'] = year
        sub_df['data_quarter'] = quarter
        
        try:
            db.insert_df(sub_df, 'sec_submissions', if_exists='append')
            total_records += len(sub_df)
        except Exception as e:
            st.warning(f"Could not save submission data: {e}")
    
    return total_records


def save_company_facts_to_db(cik: str, company_facts: Dict) -> int:
    """
    Save company facts to DuckDB.
    
    Args:
        cik: Company CIK number
        company_facts: Dictionary from get_company_facts()
        
    Returns:
        Number of records saved
    """
    if not DUCKDB_AVAILABLE:
        st.warning("DuckDB not available for saving SEC data")
        return 0
    
    # Extract and save key metrics
    key_financials = get_key_financials(cik)
    
    if key_financials.empty:
        return 0
    
    db = get_db_connection()
    key_financials['cik'] = cik
    
    try:
        db.insert_df(key_financials, 'sec_company_facts', if_exists='append')
        return len(key_financials)
    except Exception as e:
        st.warning(f"Could not save company facts: {e}")
        return 0
