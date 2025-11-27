"""
Insider Trading Tracker Module

Analyzes SEC Form 4 filings to track insider transactions and generate trading signals.
Provides sentiment scores, unusual activity detection, and backtesting capabilities.

Form 4 Transaction Codes:
- P: Purchase (Open Market)
- S: Sale (Open Market)
- A: Grant/Award
- D: Sale to Issuer
- F: Tax Withholding
- M: Exercise of Options
- C: Conversion
- E: Expiration
- G: Gift
- L: Small Acquisition
- W: Acquisition or Disposition by Will
- Z: Deposit/Withdrawal from voting trust
"""

import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import xml.etree.ElementTree as ET

try:
    from modules.database import get_db_connection
    from modules.sec_data_loader import get_company_submissions, lookup_cik, _download_with_retry, SEC_DATA_HEADERS, SEC_BASE_URL
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


class InsiderTradingTracker:
    """
    Tracks and analyzes insider trading activity from SEC Form 4 filings.
    
    Key Features:
    - Parse Form 4 XML filings for transaction details
    - Calculate insider sentiment scores
    - Detect unusual insider activity
    - Generate buy/sell signals based on insider behavior
    - Backtest insider trading signals
    
    Research shows insider purchases outperform market by 6-10% annually.
    """
    
    def __init__(self):
        """Initialize the Insider Trading Tracker."""
        self.transaction_codes = {
            'P': 'Open Market Purchase',
            'S': 'Open Market Sale',
            'A': 'Grant/Award',
            'D': 'Sale to Issuer',
            'F': 'Tax Withholding',
            'M': 'Exercise of Options',
            'C': 'Conversion',
            'E': 'Expiration',
            'G': 'Gift',
            'L': 'Small Acquisition',
            'W': 'Will Transfer',
            'Z': 'Trust Deposit/Withdrawal'
        }
        
        # Transaction codes that indicate real buying intent
        self.bullish_codes = ['P', 'M']  # Purchase, Exercise
        
        # Transaction codes that indicate selling (excluding tax/automatic)
        self.bearish_codes = ['S']  # Open market sales
        
        # Neutral/automatic transactions (excluded from sentiment)
        self.neutral_codes = ['A', 'D', 'F', 'G', 'E']
    
    def get_insider_transactions(self, ticker: str, days_back: int = 180) -> pd.DataFrame:
        """
        Fetch recent insider transactions for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            days_back: Number of days to look back
            
        Returns:
            DataFrame with insider transactions
        """
        cik = lookup_cik(ticker)
        if not cik:
            st.warning(f"Could not find CIK for {ticker}")
            return pd.DataFrame()
        
        # Get company submissions
        submissions = get_company_submissions(cik)
        if not submissions:
            return pd.DataFrame()
        
        # Extract Form 4 filings
        recent = submissions.get('filings', {}).get('recent', {})
        if not recent:
            return pd.DataFrame()
        
        # Convert to DataFrame
        filings_df = pd.DataFrame(recent)
        
        # Filter for Form 4 (insider transactions)
        form4_df = filings_df[filings_df['form'] == '4'].copy()
        
        if form4_df.empty:
            return pd.DataFrame()
        
        # Convert dates
        form4_df['filingDate'] = pd.to_datetime(form4_df['filingDate'])
        
        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=days_back)
        form4_df = form4_df[form4_df['filingDate'] >= cutoff_date]
        
        if form4_df.empty:
            return pd.DataFrame()
        
        # Parse each Form 4 filing to extract transaction details
        transactions = []
        for _, row in form4_df.iterrows():
            accession = row['accessionNumber']
            filing_date = row['filingDate']
            
            # Attempt to parse the Form 4 XML
            parsed_data = self._parse_form4_filing(cik, accession, filing_date)
            if parsed_data:
                transactions.extend(parsed_data)
        
        if not transactions:
            # If XML parsing fails, return basic filing info
            return form4_df[['filingDate', 'accessionNumber', 'primaryDocument']].rename(columns={
                'filingDate': 'transaction_date',
                'accessionNumber': 'accession_number',
                'primaryDocument': 'document'
            })
        
        # Convert to DataFrame
        transactions_df = pd.DataFrame(transactions)
        transactions_df['ticker'] = ticker
        transactions_df['cik'] = cik
        
        return transactions_df
    
    def _parse_form4_filing(self, cik: str, accession: str, filing_date: datetime) -> List[Dict[str, Any]]:
        """
        Parse a Form 4 XML filing to extract transaction details.
        
        Form 4 XML structure contains:
        - Reporting owner information (name, title)
        - Non-derivative transactions (common stock)
        - Derivative transactions (options, warrants)
        
        Args:
            cik: Company CIK
            accession: Filing accession number
            filing_date: Date of filing
            
        Returns:
            List of transaction dictionaries
        """
        # Build URL to Form 4 XML
        # SEC EDGAR URLs: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=...
        # Direct filing access: https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION-NO-DASHES}/{PRIMARY-DOC}
        
        accession_no_dashes = accession.replace('-', '')
        
        # Try common Form 4 XML filenames
        possible_files = [
            f"wf-form4_{filing_date.strftime('%Y%m%d')}.xml",
            "form4.xml",
            "doc4.xml",
            "primary_doc.xml"
        ]
        
        transactions = []
        
        for filename in possible_files:
            try:
                url = f"{SEC_BASE_URL}/Archives/edgar/data/{cik.lstrip('0')}/{accession_no_dashes}/{filename}"
                response = _download_with_retry(url, SEC_DATA_HEADERS)
                
                if response and response.status_code == 200:
                    # Parse XML
                    root = ET.fromstring(response.content)
                    
                    # Extract reporting owner info
                    owner_name = self._get_xml_text(root, './/reportingOwner/reportingOwnerId/rptOwnerName')
                    owner_title = self._get_xml_text(root, './/reportingOwner/reportingOwnerRelationship/officerTitle')
                    is_director = self._get_xml_text(root, './/reportingOwner/reportingOwnerRelationship/isDirector')
                    is_officer = self._get_xml_text(root, './/reportingOwner/reportingOwnerRelationship/isOfficer')
                    
                    # Extract non-derivative transactions (common stock)
                    for trans in root.findall('.//nonDerivativeTransaction'):
                        transaction = self._parse_transaction_xml(
                            trans, owner_name, owner_title, filing_date, is_director, is_officer
                        )
                        if transaction:
                            transactions.append(transaction)
                    
                    # Extract derivative transactions (options)
                    for trans in root.findall('.//derivativeTransaction'):
                        transaction = self._parse_derivative_transaction_xml(
                            trans, owner_name, owner_title, filing_date, is_director, is_officer
                        )
                        if transaction:
                            transactions.append(transaction)
                    
                    break  # Successfully parsed, exit loop
                    
            except Exception as e:
                # Try next filename
                continue
        
        return transactions
    
    def _parse_transaction_xml(self, trans_elem: ET.Element, owner_name: str, 
                                 owner_title: str, filing_date: datetime,
                                 is_director: str, is_officer: str) -> Optional[Dict[str, Any]]:
        """Parse a non-derivative transaction XML element."""
        try:
            trans_date = self._get_xml_text(trans_elem, './/transactionDate/value')
            trans_code = self._get_xml_text(trans_elem, './/transactionCoding/transactionCode')
            shares = self._get_xml_text(trans_elem, './/transactionAmounts/transactionShares/value')
            price = self._get_xml_text(trans_elem, './/transactionAmounts/transactionPricePerShare/value')
            acquired_disposed = self._get_xml_text(trans_elem, './/transactionAmounts/transactionAcquiredDisposedCode/value')
            shares_owned = self._get_xml_text(trans_elem, './/postTransactionAmounts/sharesOwnedFollowingTransaction/value')
            
            if not trans_date or not trans_code:
                return None
            
            # Calculate transaction value
            try:
                shares_num = float(shares) if shares else 0
                price_num = float(price) if price else 0
                transaction_value = shares_num * price_num
            except:
                transaction_value = 0
            
            return {
                'transaction_date': pd.to_datetime(trans_date),
                'filing_date': filing_date,
                'insider_name': owner_name or 'Unknown',
                'insider_title': owner_title or 'Unknown',
                'is_director': is_director == '1',
                'is_officer': is_officer == '1',
                'transaction_code': trans_code,
                'transaction_type': self.transaction_codes.get(trans_code, 'Unknown'),
                'shares': float(shares) if shares else 0,
                'price_per_share': float(price) if price else 0,
                'transaction_value': transaction_value,
                'acquired_disposed': acquired_disposed,
                'shares_owned_after': float(shares_owned) if shares_owned else 0,
                'security_type': 'Common Stock'
            }
        except Exception as e:
            return None
    
    def _parse_derivative_transaction_xml(self, trans_elem: ET.Element, owner_name: str,
                                            owner_title: str, filing_date: datetime,
                                            is_director: str, is_officer: str) -> Optional[Dict[str, Any]]:
        """Parse a derivative transaction XML element (options, warrants)."""
        try:
            trans_date = self._get_xml_text(trans_elem, './/transactionDate/value')
            trans_code = self._get_xml_text(trans_elem, './/transactionCoding/transactionCode')
            shares = self._get_xml_text(trans_elem, './/transactionAmounts/transactionShares/value')
            price = self._get_xml_text(trans_elem, './/transactionAmounts/transactionPricePerShare/value')
            exercise_price = self._get_xml_text(trans_elem, './/conversionOrExercisePrice/value')
            security_title = self._get_xml_text(trans_elem, './/securityTitle/value')
            
            if not trans_date or not trans_code:
                return None
            
            # Calculate transaction value
            try:
                shares_num = float(shares) if shares else 0
                price_num = float(price) if price else float(exercise_price) if exercise_price else 0
                transaction_value = shares_num * price_num
            except:
                transaction_value = 0
            
            return {
                'transaction_date': pd.to_datetime(trans_date),
                'filing_date': filing_date,
                'insider_name': owner_name or 'Unknown',
                'insider_title': owner_title or 'Unknown',
                'is_director': is_director == '1',
                'is_officer': is_officer == '1',
                'transaction_code': trans_code,
                'transaction_type': self.transaction_codes.get(trans_code, 'Unknown'),
                'shares': float(shares) if shares else 0,
                'price_per_share': float(price) if price else 0,
                'transaction_value': transaction_value,
                'acquired_disposed': 'A',  # Derivatives typically acquired
                'shares_owned_after': 0,  # Not always available for derivatives
                'security_type': security_title or 'Stock Option'
            }
        except Exception as e:
            return None
    
    def _get_xml_text(self, root: ET.Element, xpath: str) -> Optional[str]:
        """Safely extract text from XML element."""
        try:
            elem = root.find(xpath)
            return elem.text if elem is not None and elem.text else None
        except:
            return None
    
    def calculate_insider_sentiment(self, transactions_df: pd.DataFrame, 
                                      days: int = 90) -> Dict[str, Any]:
        """
        Calculate insider sentiment score based on recent transactions.
        
        Methodology:
        1. Filter for meaningful transactions (exclude tax withholding, gifts, etc.)
        2. Weight by transaction value and insider importance
        3. Calculate net buying pressure
        4. Score from -100 (bearish) to +100 (bullish)
        
        Args:
            transactions_df: DataFrame of insider transactions
            days: Lookback period for sentiment calculation
            
        Returns:
            Dictionary with sentiment score and supporting metrics
        """
        if transactions_df.empty:
            return {
                'sentiment_score': 0,
                'signal': 'Neutral',
                'buy_value': 0,
                'sell_value': 0,
                'net_value': 0,
                'num_buyers': 0,
                'num_sellers': 0,
                'confidence': 'Low'
            }
        
        # Filter recent transactions
        cutoff = datetime.now() - timedelta(days=days)
        df = transactions_df[transactions_df['transaction_date'] >= cutoff].copy()
        
        if df.empty:
            return {
                'sentiment_score': 0,
                'signal': 'Neutral',
                'buy_value': 0,
                'sell_value': 0,
                'net_value': 0,
                'num_buyers': 0,
                'num_sellers': 0,
                'confidence': 'Low'
            }
        
        # Calculate buy and sell values (only meaningful transactions)
        buy_mask = df['transaction_code'].isin(self.bullish_codes) & (df['transaction_value'] > 0)
        sell_mask = df['transaction_code'].isin(self.bearish_codes) & (df['transaction_value'] > 0)
        
        buy_value = df[buy_mask]['transaction_value'].sum()
        sell_value = df[sell_mask]['transaction_value'].sum()
        
        # Count unique insiders
        num_buyers = df[buy_mask]['insider_name'].nunique()
        num_sellers = df[sell_mask]['insider_name'].nunique()
        
        # Weight transactions by insider importance (CEOs, CFOs get higher weight)
        df['insider_weight'] = df['insider_title'].apply(self._get_insider_weight)
        
        weighted_buy = (df[buy_mask]['transaction_value'] * df[buy_mask]['insider_weight']).sum()
        weighted_sell = (df[sell_mask]['transaction_value'] * df[sell_mask]['insider_weight']).sum()
        
        # Calculate sentiment score (-100 to +100)
        total_weighted = weighted_buy + weighted_sell
        if total_weighted > 0:
            sentiment_score = ((weighted_buy - weighted_sell) / total_weighted) * 100
        else:
            sentiment_score = 0
        
        # Determine signal
        if sentiment_score > 30:
            signal = 'Strong Buy'
        elif sentiment_score > 10:
            signal = 'Buy'
        elif sentiment_score < -30:
            signal = 'Strong Sell'
        elif sentiment_score < -10:
            signal = 'Sell'
        else:
            signal = 'Neutral'
        
        # Confidence based on number of transactions and insiders
        total_transactions = len(df[buy_mask | sell_mask])
        total_insiders = num_buyers + num_sellers
        
        if total_transactions >= 10 and total_insiders >= 5:
            confidence = 'High'
        elif total_transactions >= 5 and total_insiders >= 3:
            confidence = 'Medium'
        else:
            confidence = 'Low'
        
        return {
            'sentiment_score': round(sentiment_score, 2),
            'signal': signal,
            'buy_value': buy_value,
            'sell_value': sell_value,
            'net_value': buy_value - sell_value,
            'num_buyers': num_buyers,
            'num_sellers': num_sellers,
            'total_transactions': total_transactions,
            'confidence': confidence
        }
    
    def _get_insider_weight(self, title: str) -> float:
        """
        Assign weight to insider based on title/position.
        
        Higher weight = more meaningful signal
        CEO/CFO trades are most predictive of future performance.
        """
        if not title or title == 'Unknown':
            return 1.0
        
        title_lower = title.lower()
        
        # C-Suite executives (highest weight)
        if any(role in title_lower for role in ['ceo', 'chief executive', 'president']):
            return 3.0
        if any(role in title_lower for role in ['cfo', 'chief financial']):
            return 2.5
        if any(role in title_lower for role in ['coo', 'chief operating']):
            return 2.0
        if 'chief' in title_lower:
            return 2.0
        
        # Directors and VPs (medium weight)
        if 'director' in title_lower:
            return 1.5
        if any(role in title_lower for role in ['vp', 'vice president', 'svp', 'evp']):
            return 1.5
        
        # Other officers (base weight)
        return 1.0
    
    def detect_unusual_activity(self, transactions_df: pd.DataFrame,
                                  lookback_days: int = 90,
                                  baseline_days: int = 365) -> Dict[str, Any]:
        """
        Detect unusual insider trading activity.
        
        Compares recent activity to historical baseline:
        - Volume spike: 2x+ normal transaction volume
        - Value spike: 2x+ normal dollar value
        - Cluster buying: 3+ insiders buying within short period
        - Unanimous buying: All transactions are buys (no sells)
        
        Args:
            transactions_df: DataFrame of insider transactions
            lookback_days: Recent period to analyze
            baseline_days: Historical baseline period
            
        Returns:
            Dictionary with unusual activity flags and metrics
        """
        if transactions_df.empty:
            return {
                'is_unusual': False,
                'alerts': [],
                'volume_ratio': 0,
                'value_ratio': 0
            }
        
        cutoff_recent = datetime.now() - timedelta(days=lookback_days)
        cutoff_baseline = datetime.now() - timedelta(days=baseline_days)
        
        # Recent transactions
        recent_df = transactions_df[transactions_df['transaction_date'] >= cutoff_recent]
        
        # Baseline transactions (excluding recent period)
        baseline_df = transactions_df[
            (transactions_df['transaction_date'] >= cutoff_baseline) &
            (transactions_df['transaction_date'] < cutoff_recent)
        ]
        
        alerts = []
        
        # Calculate metrics
        recent_count = len(recent_df)
        baseline_avg_count = len(baseline_df) / max(1, (baseline_days - lookback_days) / lookback_days)
        
        recent_value = recent_df['transaction_value'].sum()
        baseline_avg_value = baseline_df['transaction_value'].sum() / max(1, (baseline_days - lookback_days) / lookback_days)
        
        volume_ratio = recent_count / max(1, baseline_avg_count)
        value_ratio = recent_value / max(1, baseline_avg_value)
        
        # Check for volume spike
        if volume_ratio >= 2.0:
            alerts.append(f"⚠️ Transaction volume {volume_ratio:.1f}x higher than normal")
        
        # Check for value spike
        if value_ratio >= 2.0:
            alerts.append(f"💰 Transaction value {value_ratio:.1f}x higher than normal")
        
        # Check for cluster buying
        buy_mask = recent_df['transaction_code'].isin(self.bullish_codes)
        unique_buyers = recent_df[buy_mask]['insider_name'].nunique()
        
        if unique_buyers >= 3:
            total_buy_value = recent_df[buy_mask]['transaction_value'].sum()
            alerts.append(f"📈 {unique_buyers} insiders purchased ${total_buy_value:,.0f} in stock")
        
        # Check for unanimous buying (no sells)
        sell_mask = recent_df['transaction_code'].isin(self.bearish_codes)
        has_sells = sell_mask.any()
        
        if not has_sells and unique_buyers >= 2:
            alerts.append(f"🚨 Unanimous buying - {unique_buyers} insiders bought with ZERO sales")
        
        # Check for large individual transactions
        large_transactions = recent_df[recent_df['transaction_value'] > 1_000_000]
        if not large_transactions.empty:
            for _, trans in large_transactions.iterrows():
                alerts.append(
                    f"💵 Large transaction: {trans['insider_name']} "
                    f"({trans['transaction_type']}) ${trans['transaction_value']:,.0f}"
                )
        
        is_unusual = len(alerts) > 0
        
        return {
            'is_unusual': is_unusual,
            'alerts': alerts,
            'volume_ratio': round(volume_ratio, 2),
            'value_ratio': round(value_ratio, 2),
            'recent_transactions': recent_count,
            'baseline_avg_transactions': round(baseline_avg_count, 1),
            'recent_value': recent_value,
            'unique_buyers': unique_buyers
        }
    
    def backtest_insider_signals(self, ticker: str, 
                                   transactions_df: pd.DataFrame,
                                   signal_threshold: float = 20,
                                   holding_period_days: int = 90) -> Dict[str, Any]:
        """
        Backtest insider trading signals against stock performance.
        
        Methodology:
        1. Identify dates when insider sentiment crossed threshold
        2. Calculate returns over various holding periods
        3. Compare to buy-and-hold benchmark
        4. Calculate win rate and average returns
        
        Args:
            ticker: Stock ticker symbol
            transactions_df: DataFrame of insider transactions
            signal_threshold: Sentiment score threshold for signals (default: 20 = "Buy")
            holding_period_days: Days to hold after signal
            
        Returns:
            Dictionary with backtest results
        """
        if transactions_df.empty:
            return {
                'total_signals': 0,
                'win_rate': 0,
                'avg_return': 0,
                'benchmark_return': 0,
                'alpha': 0
            }
        
        # Get historical price data
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='2y')
            
            if hist.empty:
                return {'error': 'Could not fetch price data'}
        except Exception as e:
            return {'error': f'Price data error: {str(e)}'}
        
        # Generate signals based on rolling sentiment
        transactions_df = transactions_df.sort_values('transaction_date')
        
        signals = []
        signal_dates = []
        
        # Calculate sentiment for each transaction date
        for trans_date in transactions_df['transaction_date'].unique():
            # Get transactions up to this date (90-day window)
            window_start = trans_date - timedelta(days=90)
            window_df = transactions_df[
                (transactions_df['transaction_date'] >= window_start) &
                (transactions_df['transaction_date'] <= trans_date)
            ]
            
            sentiment = self.calculate_insider_sentiment(window_df, days=90)
            
            # Check if signal crossed threshold
            if abs(sentiment['sentiment_score']) >= signal_threshold:
                signals.append(sentiment)
                signal_dates.append(trans_date)
        
        if not signals:
            return {
                'total_signals': 0,
                'win_rate': 0,
                'avg_return': 0,
                'benchmark_return': 0,
                'alpha': 0,
                'message': f'No signals above threshold {signal_threshold}'
            }
        
        # Calculate returns for each signal
        returns = []
        
        for signal_date in signal_dates:
            # Find closest trading day
            try:
                entry_date = hist.index[hist.index >= pd.Timestamp(signal_date)][0]
                exit_date = entry_date + timedelta(days=holding_period_days)
                
                # Get prices
                entry_price = hist.loc[entry_date, 'Close']
                
                # Find exit price (closest available date)
                exit_prices = hist[hist.index >= pd.Timestamp(exit_date)]
                if not exit_prices.empty:
                    exit_price = exit_prices.iloc[0]['Close']
                    
                    # Calculate return
                    signal_return = (exit_price - entry_price) / entry_price * 100
                    returns.append(signal_return)
            except:
                continue
        
        if not returns:
            return {
                'total_signals': len(signals),
                'win_rate': 0,
                'avg_return': 0,
                'message': 'Could not calculate returns'
            }
        
        # Calculate benchmark (buy and hold)
        try:
            benchmark_start = hist.iloc[0]['Close']
            benchmark_end = hist.iloc[-1]['Close']
            benchmark_return = (benchmark_end - benchmark_start) / benchmark_start * 100
            
            # Annualize benchmark
            days_held = (hist.index[-1] - hist.index[0]).days
            benchmark_annual = (1 + benchmark_return/100) ** (365/days_held) - 1
            benchmark_annual *= 100
        except:
            benchmark_return = 0
            benchmark_annual = 0
        
        # Calculate metrics
        avg_return = np.mean(returns)
        win_rate = sum(1 for r in returns if r > 0) / len(returns) * 100
        
        # Calculate alpha (excess return over benchmark)
        # Annualize signal returns
        signal_annual = (1 + avg_return/100) ** (365/holding_period_days) - 1
        signal_annual *= 100
        
        alpha = signal_annual - benchmark_annual
        
        return {
            'total_signals': len(signals),
            'valid_trades': len(returns),
            'win_rate': round(win_rate, 2),
            'avg_return': round(avg_return, 2),
            'median_return': round(np.median(returns), 2),
            'best_return': round(max(returns), 2),
            'worst_return': round(min(returns), 2),
            'benchmark_return': round(benchmark_return, 2),
            'annualized_signal_return': round(signal_annual, 2),
            'annualized_benchmark': round(benchmark_annual, 2),
            'alpha': round(alpha, 2),
            'holding_period_days': holding_period_days,
            'signal_threshold': signal_threshold
        }
    
    def get_top_insider_buyers(self, transactions_df: pd.DataFrame, 
                                 days: int = 30, 
                                 top_n: int = 10) -> pd.DataFrame:
        """
        Get top insider buyers by transaction value in recent period.
        
        Args:
            transactions_df: DataFrame of insider transactions
            days: Lookback period
            top_n: Number of top buyers to return
            
        Returns:
            DataFrame with top buyers ranked by purchase value
        """
        if transactions_df.empty:
            return pd.DataFrame()
        
        # Filter recent purchases
        cutoff = datetime.now() - timedelta(days=days)
        buy_mask = (
            (transactions_df['transaction_date'] >= cutoff) &
            (transactions_df['transaction_code'].isin(self.bullish_codes))
        )
        
        buys_df = transactions_df[buy_mask].copy()
        
        if buys_df.empty:
            return pd.DataFrame()
        
        # Aggregate by insider
        top_buyers = buys_df.groupby(['insider_name', 'insider_title']).agg({
            'transaction_value': 'sum',
            'shares': 'sum',
            'transaction_date': 'max'
        }).reset_index()
        
        top_buyers = top_buyers.sort_values('transaction_value', ascending=False).head(top_n)
        top_buyers.columns = ['Insider', 'Title', 'Total Value', 'Total Shares', 'Last Transaction']
        
        return top_buyers
    
    def save_to_database(self, transactions_df: pd.DataFrame) -> int:
        """
        Save insider transactions to database.
        
        Args:
            transactions_df: DataFrame of insider transactions
            
        Returns:
            Number of records saved
        """
        if not DB_AVAILABLE or transactions_df.empty:
            return 0
        
        try:
            db = get_db_connection()
            
            # Ensure table exists (will be created by schema module)
            transactions_df.to_sql(
                'insider_transactions',
                db.connection,
                if_exists='append',
                index=False
            )
            
            return len(transactions_df)
        except Exception as e:
            st.warning(f"Could not save to database: {e}")
            return 0
