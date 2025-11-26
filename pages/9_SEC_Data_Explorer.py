"""
SEC Data Dashboard - Company Filings & Financial Statements
Explore SEC EDGAR data including financial statements, company filings, and institutional holdings.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional

# Import SEC data loader
try:
    from modules.sec_data_loader import (
        get_company_facts,
        get_key_financials,
        get_recent_filings,
        get_company_submissions,
        lookup_cik,
        get_company_tickers,
        download_financial_statement_data,
        extract_financial_metric
    )
    SEC_AVAILABLE = True
except ImportError as e:
    SEC_AVAILABLE = False
    SEC_ERROR = str(e)

# Import database functions
try:
    from modules.database import (
        get_sec_company_facts,
        get_sec_filings,
        get_sec_data_freshness
    )
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="SEC Data - Economic Dashboard",
    page_icon="📄",
    layout="wide"
)

st.title("📄 SEC EDGAR Data Explorer")
st.markdown("""
Explore SEC filings, financial statements, and company data from the SEC EDGAR database.
""")

if not SEC_AVAILABLE:
    st.error(f"SEC data module not available: {SEC_ERROR}")
    st.stop()

st.divider()

# Sidebar controls
with st.sidebar:
    st.header("🔍 Search Options")
    
    search_method = st.radio(
        "Search By:",
        ["Ticker Symbol", "Company CIK", "Browse Companies"]
    )
    
    st.divider()
    
    st.header("📊 Data Options")
    
    show_filings = st.checkbox("Show Recent Filings", value=True)
    show_financials = st.checkbox("Show Key Financials", value=True)
    show_charts = st.checkbox("Show Financial Charts", value=True)
    
    filing_types = st.multiselect(
        "Filter Filing Types:",
        ["10-K", "10-Q", "8-K", "4", "13F-HR", "DEF 14A", "S-1"],
        default=["10-K", "10-Q"]
    )

# Main content
tab1, tab2, tab3, tab4 = st.tabs([
    "🏢 Company Overview", 
    "📈 Financial Analysis",
    "📋 Filings History",
    "📊 Market Data"
])

# Determine CIK based on search method
cik = None
company_name = None
ticker_input = None
cik_input = None

if search_method == "Ticker Symbol":
    ticker_input = st.sidebar.text_input(
        "Enter Ticker Symbol:",
        placeholder="e.g., AAPL, MSFT, GOOGL",
        key="ticker_input_field"
    ).upper().strip()
    
    if ticker_input:
        with st.spinner(f"Looking up {ticker_input}..."):
            cik = lookup_cik(ticker_input)
            if cik:
                st.sidebar.success(f"Found CIK: {cik}")
            else:
                st.sidebar.warning(f"Could not find CIK for {ticker_input}")

elif search_method == "Company CIK":
    cik_input = st.sidebar.text_input(
        "Enter CIK Number:",
        placeholder="e.g., 0000320193",
        key="cik_input_field"
    ).strip()
    
    if cik_input:
        cik = cik_input.zfill(10)

elif search_method == "Browse Companies":
    # Load company tickers for selection
    with st.spinner("Loading company list..."):
        tickers_df = get_company_tickers()
        if not tickers_df.empty:
            # Create searchable selection
            search_term = st.sidebar.text_input("Search companies:", "")
            
            if search_term:
                filtered = tickers_df[
                    tickers_df['ticker'].str.contains(search_term.upper(), na=False) |
                    tickers_df['title'].str.upper().str.contains(search_term.upper(), na=False)
                ].head(20)
                
                if not filtered.empty:
                    options = filtered.apply(
                        lambda x: f"{x['ticker']} - {x['title'][:50]}", axis=1
                    ).tolist()
                    
                    selected = st.sidebar.selectbox("Select company:", options)
                    
                    if selected:
                        ticker = selected.split(" - ")[0]
                        cik = filtered[filtered['ticker'] == ticker]['cik'].iloc[0]


# ============================================================================
# Tab 1: Company Overview
# ============================================================================
with tab1:
    if cik:
        st.subheader("Company Information")
        
        with st.spinner("Loading company data..."):
            submissions = get_company_submissions(cik)
            
            if submissions:
                col1, col2 = st.columns(2)
                
                with col1:
                    company_name = submissions.get('name', 'Unknown')
                    st.markdown(f"### {company_name}")
                    
                    st.markdown("**Company Details:**")
                    details = {
                        "CIK": cik,
                        "SIC Code": submissions.get('sic', 'N/A'),
                        "SIC Description": submissions.get('sicDescription', 'N/A'),
                        "State of Incorporation": submissions.get('stateOfIncorporation', 'N/A'),
                        "Fiscal Year End": submissions.get('fiscalYearEnd', 'N/A'),
                    }
                    
                    for key, value in details.items():
                        st.text(f"{key}: {value}")
                
                with col2:
                    tickers = submissions.get('tickers', [])
                    exchanges = submissions.get('exchanges', [])
                    
                    st.markdown("**Trading Information:**")
                    if tickers:
                        st.text(f"Tickers: {', '.join(tickers)}")
                    if exchanges:
                        st.text(f"Exchanges: {', '.join(exchanges)}")
                    
                    addresses = submissions.get('addresses', {})
                    if addresses and 'business' in addresses:
                        biz = addresses['business']
                        st.markdown("**Business Address:**")
                        st.text(f"{biz.get('street1', '')}")
                        st.text(f"{biz.get('city', '')}, {biz.get('stateOrCountry', '')} {biz.get('zipCode', '')}")
                
                # Filing statistics
                st.divider()
                st.subheader("📊 Filing Statistics")
                
                filings = submissions.get('filings', {}).get('recent', {})
                if filings:
                    forms = filings.get('form', [])
                    if forms:
                        form_counts = pd.Series(forms).value_counts().head(10)
                        
                        fig = px.bar(
                            x=form_counts.index,
                            y=form_counts.values,
                            labels={'x': 'Form Type', 'y': 'Count'},
                            title="Recent Filing Types"
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Could not load company information.")
    else:
        st.info("👆 Enter a ticker symbol or CIK number in the sidebar to get started.")
        
        # Show example companies
        st.subheader("📋 Example Companies")
        
        examples = pd.DataFrame({
            'Company': ['Apple Inc.', 'Microsoft Corp.', 'Amazon.com Inc.', 'Alphabet Inc.', 'Tesla Inc.'],
            'Ticker': ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA'],
            'CIK': ['0000320193', '0000789019', '0001018724', '0001652044', '0001318605']
        })
        
        st.dataframe(examples, use_container_width=True, hide_index=True)


# ============================================================================
# Tab 2: Financial Analysis
# ============================================================================
with tab2:
    if cik and show_financials:
        st.subheader("📊 Key Financial Metrics")
        
        with st.spinner("Loading financial data..."):
            company_facts = get_company_facts(cik)
            
            if company_facts:
                # Display company info
                st.markdown(f"**Entity:** {company_facts.get('entityName', 'Unknown')}")
                
                # Key metrics to display
                key_metrics = [
                    ('Revenues', 'Total Revenue'),
                    ('RevenueFromContractWithCustomerExcludingAssessedTax', 'Contract Revenue'),
                    ('NetIncomeLoss', 'Net Income'),
                    ('Assets', 'Total Assets'),
                    ('Liabilities', 'Total Liabilities'),
                    ('StockholdersEquity', 'Shareholders Equity'),
                    ('OperatingIncomeLoss', 'Operating Income'),
                    ('EarningsPerShareDiluted', 'Diluted EPS'),
                ]
                
                # Extract and display metrics
                metrics_data = []
                
                for concept, display_name in key_metrics:
                    df = extract_financial_metric(company_facts, concept)
                    if not df.empty:
                        # Get latest annual value (10-K)
                        annual = df[df['form'] == '10-K']
                        if not annual.empty:
                            latest = annual.iloc[0]
                            metrics_data.append({
                                'Metric': display_name,
                                'Latest Value': latest['value'],
                                'Period End': latest['end_date'].strftime('%Y-%m-%d') if pd.notna(latest['end_date']) else 'N/A',
                                'Fiscal Year': latest['fiscal_year'],
                                'Unit': latest['unit']
                            })
                
                if metrics_data:
                    metrics_df = pd.DataFrame(metrics_data)
                    
                    # Format values
                    def format_value(row):
                        val = row['Latest Value']
                        unit = row['Unit']
                        if pd.isna(val):
                            return 'N/A'
                        if 'USD' in str(unit):
                            if abs(val) >= 1e9:
                                return f"${val/1e9:.2f}B"
                            elif abs(val) >= 1e6:
                                return f"${val/1e6:.2f}M"
                            else:
                                return f"${val:,.2f}"
                        return f"{val:,.2f}"
                    
                    metrics_df['Formatted Value'] = metrics_df.apply(format_value, axis=1)
                    
                    # Display as metrics
                    cols = st.columns(4)
                    for i, row in metrics_df.iterrows():
                        with cols[i % 4]:
                            st.metric(
                                label=row['Metric'],
                                value=row['Formatted Value'],
                                help=f"FY{row['Fiscal Year']} - {row['Period End']}"
                            )
                    
                    st.divider()
                    
                    # Show detailed table
                    with st.expander("📋 View Full Details"):
                        display_df = metrics_df[['Metric', 'Formatted Value', 'Period End', 'Fiscal Year']]
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Financial trends chart
                if show_charts:
                    st.subheader("📈 Revenue & Net Income Trend")
                    
                    revenue_df = extract_financial_metric(company_facts, 'Revenues')
                    if revenue_df.empty:
                        revenue_df = extract_financial_metric(
                            company_facts, 
                            'RevenueFromContractWithCustomerExcludingAssessedTax'
                        )
                    
                    income_df = extract_financial_metric(company_facts, 'NetIncomeLoss')
                    
                    if not revenue_df.empty or not income_df.empty:
                        fig = go.Figure()
                        
                        if not revenue_df.empty:
                            annual_rev = revenue_df[revenue_df['form'] == '10-K'].copy()
                            annual_rev = annual_rev.sort_values('end_date')
                            
                            fig.add_trace(go.Bar(
                                x=annual_rev['end_date'],
                                y=annual_rev['value'] / 1e9,
                                name='Revenue (Billions)',
                                marker_color='#0068c9'
                            ))
                        
                        if not income_df.empty:
                            annual_income = income_df[income_df['form'] == '10-K'].copy()
                            annual_income = annual_income.sort_values('end_date')
                            
                            fig.add_trace(go.Scatter(
                                x=annual_income['end_date'],
                                y=annual_income['value'] / 1e9,
                                name='Net Income (Billions)',
                                mode='lines+markers',
                                line=dict(color='#00cc66', width=3),
                                yaxis='y2'
                            ))
                        
                        fig.update_layout(
                            title="Annual Revenue & Net Income",
                            xaxis_title="Period",
                            yaxis=dict(title="Revenue ($B)", side='left'),
                            yaxis2=dict(title="Net Income ($B)", side='right', overlaying='y'),
                            height=400,
                            legend=dict(x=0, y=1.1, orientation='h')
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Revenue/Income data not available for charting.")
            else:
                st.warning("Could not load financial data for this company.")
    elif not cik:
        st.info("👆 Select a company to view financial analysis.")
    else:
        st.info("Enable 'Show Key Financials' in the sidebar to view financial data.")


# ============================================================================
# Tab 3: Filings History
# ============================================================================
with tab3:
    if cik and show_filings:
        st.subheader("📋 Recent SEC Filings")
        
        with st.spinner("Loading filings..."):
            filings_df = get_recent_filings(cik, form_types=filing_types if filing_types else None)
            
            if not filings_df.empty:
                # Display summary
                st.markdown(f"**Found {len(filings_df)} recent filings**")
                
                # Format the dataframe for display
                display_cols = ['form', 'filingDate', 'reportDate', 'primaryDocument', 'description']
                available_cols = [c for c in display_cols if c in filings_df.columns]
                
                if available_cols:
                    display_df = filings_df[available_cols].copy()
                    
                    # Rename columns for display
                    display_df.columns = [
                        col.replace('filingDate', 'Filing Date')
                           .replace('reportDate', 'Report Date')
                           .replace('form', 'Form Type')
                           .replace('primaryDocument', 'Document')
                           .replace('description', 'Description')
                        for col in display_df.columns
                    ]
                    
                    # Add links to SEC EDGAR
                    if 'accessionNumber' in filings_df.columns:
                        def make_link(row):
                            accn = filings_df.loc[row.name, 'accessionNumber'].replace('-', '')
                            return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn}"
                        
                        # Can't add clickable links easily in st.dataframe
                    
                    st.dataframe(display_df.head(50), use_container_width=True, hide_index=True)
                    
                    # Filing type distribution
                    st.divider()
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Filing Types Distribution**")
                        form_counts = filings_df['form'].value_counts()
                        fig = px.pie(
                            values=form_counts.values,
                            names=form_counts.index,
                            title=""
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.markdown("**Filings Over Time**")
                        if 'filingDate' in filings_df.columns:
                            filings_df['month'] = pd.to_datetime(filings_df['filingDate']).dt.to_period('M')
                            monthly = filings_df.groupby('month').size()
                            
                            fig = px.line(
                                x=monthly.index.astype(str),
                                y=monthly.values,
                                labels={'x': 'Month', 'y': 'Filing Count'}
                            )
                            fig.update_layout(height=300)
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Filings data format not recognized.")
            else:
                st.info("No filings found for the selected criteria.")
    elif not cik:
        st.info("👆 Select a company to view filings history.")
    else:
        st.info("Enable 'Show Recent Filings' in the sidebar to view filing history.")


# ============================================================================
# Tab 4: Market Data (Additional SEC datasets)
# ============================================================================
with tab4:
    st.subheader("📊 SEC Market Data")
    
    st.markdown("""
    Additional SEC datasets available for analysis:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📁 Available Datasets")
        
        datasets = [
            ("Financial Statement Data Sets", "Quarterly XBRL financial data from all filers"),
            ("Form 13F Holdings", "Institutional investment manager holdings"),
            ("Fails-to-Deliver Data", "Securities with failed delivery"),
            ("Insider Transactions", "Form 4 insider trading reports"),
            ("Company Tickers", "All SEC registered company tickers/CIKs"),
        ]
        
        for name, desc in datasets:
            with st.expander(name):
                st.write(desc)
    
    with col2:
        st.markdown("### 📈 Quick Stats")
        
        # Load company count
        with st.spinner("Loading statistics..."):
            tickers_df = get_company_tickers()
            if not tickers_df.empty:
                st.metric("Registered Companies", f"{len(tickers_df):,}")
        
        # Show database freshness if available
        if DB_AVAILABLE:
            try:
                freshness = get_sec_data_freshness()
                if not freshness.empty:
                    st.markdown("**Data Freshness:**")
                    for _, row in freshness.iterrows():
                        if row['total_records'] > 0:
                            st.text(f"{row['source']}: {row['total_records']:,} records")
            except Exception:
                pass
    
    st.divider()
    
    # Financial Statement Data Sets download
    st.subheader("📥 Download Financial Statement Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        year = st.selectbox(
            "Year:",
            options=list(range(datetime.now().year, 2009, -1)),
            index=0
        )
    
    with col2:
        quarter = st.selectbox(
            "Quarter:",
            options=[1, 2, 3, 4],
            index=0
        )
    
    with col3:
        if st.button("📥 Download Data", type="primary"):
            with st.spinner(f"Downloading {year}Q{quarter} data..."):
                fsds_data = download_financial_statement_data(year, quarter)
                
                if fsds_data:
                    st.success(f"Downloaded {year}Q{quarter} data successfully!")
                    
                    # Show summary
                    for key, df in fsds_data.items():
                        if not df.empty:
                            st.text(f"• {key}: {len(df):,} records")
                else:
                    st.error("Could not download data. It may not be available yet.")

# Footer
st.divider()
st.caption("""
Data sourced from SEC EDGAR. For more information, visit [SEC Data Resources](https://www.sec.gov/data-research).

**Rate Limits:** SEC APIs allow approximately 10 requests per second. Please be mindful of usage.
""")
