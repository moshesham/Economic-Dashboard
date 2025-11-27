"""
Database Schema Definitions

Defines all tables for the Economic Dashboard DuckDB database.
"""

from .connection import get_db_connection


def create_fred_data_table():
    """Create table for FRED economic data"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS fred_data (
            series_id VARCHAR NOT NULL,
            date DATE NOT NULL,
            value DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (series_id, date)
        )
    """)
    
    # Create indexes for common queries
    db.execute("CREATE INDEX IF NOT EXISTS idx_fred_series ON fred_data(series_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_fred_date ON fred_data(date)")


def create_yfinance_ohlcv_table():
    """Create table for stock OHLCV data"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS yfinance_ohlcv (
            ticker VARCHAR NOT NULL,
            date DATE NOT NULL,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume BIGINT,
            adj_close DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, date)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_yf_ticker ON yfinance_ohlcv(ticker)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_yf_date ON yfinance_ohlcv(date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_yf_ticker_date ON yfinance_ohlcv(ticker, date)")


def create_options_data_table():
    """Create table for options data"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS options_data (
            ticker VARCHAR NOT NULL,
            date DATE NOT NULL,
            expiration_date DATE NOT NULL,
            put_volume BIGINT,
            call_volume BIGINT,
            put_open_interest BIGINT,
            call_open_interest BIGINT,
            put_call_volume_ratio DOUBLE,
            put_call_oi_ratio DOUBLE,
            total_put_iv DOUBLE,
            total_call_iv DOUBLE,
            iv_rank DOUBLE,
            iv_percentile DOUBLE,
            skew DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, date, expiration_date)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_options_ticker ON options_data(ticker)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_options_date ON options_data(date)")


def create_market_indicators_table():
    """Create table for market-level indicators"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS market_indicators (
            date DATE NOT NULL,
            vix DOUBLE,
            vix_3m DOUBLE,
            vvix DOUBLE,
            skew DOUBLE,
            put_call_ratio DOUBLE,
            high_yield_spread DOUBLE,
            term_spread DOUBLE,
            credit_spread DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_market_date ON market_indicators(date)")


def create_technical_features_table():
    """Create table for technical analysis features"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS technical_features (
            ticker VARCHAR NOT NULL,
            date DATE NOT NULL,
            -- Momentum indicators
            rsi_14 DOUBLE,
            rsi_28 DOUBLE,
            stoch_k DOUBLE,
            stoch_d DOUBLE,
            williams_r DOUBLE,
            roc_10 DOUBLE,
            roc_20 DOUBLE,
            -- Trend indicators
            sma_20 DOUBLE,
            sma_50 DOUBLE,
            sma_200 DOUBLE,
            ema_12 DOUBLE,
            ema_26 DOUBLE,
            macd DOUBLE,
            macd_signal DOUBLE,
            macd_histogram DOUBLE,
            adx DOUBLE,
            -- Volatility indicators
            bb_upper DOUBLE,
            bb_middle DOUBLE,
            bb_lower DOUBLE,
            bb_width DOUBLE,
            atr_14 DOUBLE,
            keltner_upper DOUBLE,
            keltner_lower DOUBLE,
            -- Volume indicators
            obv DOUBLE,
            obv_sma DOUBLE,
            mfi DOUBLE,
            ad_line DOUBLE,
            cmf DOUBLE,
            vwap DOUBLE,
            -- Custom indicators
            price_to_sma20 DOUBLE,
            price_to_sma50 DOUBLE,
            price_to_sma200 DOUBLE,
            volume_ratio DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, date)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_tech_ticker ON technical_features(ticker)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_tech_date ON technical_features(date)")


def create_derived_features_table():
    """Create table for derived/engineered features"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS derived_features (
            ticker VARCHAR NOT NULL,
            date DATE NOT NULL,
            -- Feature interactions
            rsi_macd_interaction DOUBLE,
            volume_price_divergence DOUBLE,
            momentum_volatility_ratio DOUBLE,
            -- Regime detection
            volatility_regime VARCHAR,
            trend_regime VARCHAR,
            volume_regime VARCHAR,
            -- Z-scores
            price_zscore DOUBLE,
            volume_zscore DOUBLE,
            rsi_zscore DOUBLE,
            -- Cross-asset features
            sp500_correlation_30d DOUBLE,
            sector_relative_strength DOUBLE,
            market_beta DOUBLE,
            -- Time-based features
            day_of_week INTEGER,
            week_of_month INTEGER,
            month INTEGER,
            quarter INTEGER,
            -- Sentiment proxies
            high_low_range DOUBLE,
            close_position_in_range DOUBLE,
            gap_percentage DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, date)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_derived_ticker ON derived_features(ticker)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_derived_date ON derived_features(date)")


def create_ml_training_data_table():
    """Create table for ML training datasets"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS ml_training_data (
            ticker VARCHAR NOT NULL,
            as_of_date DATE NOT NULL,
            target_date DATE NOT NULL,
            target_direction BOOLEAN,
            target_return DOUBLE,
            split_type VARCHAR,  -- 'train', 'validation', 'test'
            fold_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, as_of_date)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_ml_train_ticker ON ml_training_data(ticker)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_ml_train_split ON ml_training_data(split_type)")


def create_ml_predictions_table():
    """Create table for ML model predictions"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS ml_predictions (
            ticker VARCHAR NOT NULL,
            prediction_date DATE NOT NULL,
            target_date DATE NOT NULL,
            model_version VARCHAR NOT NULL,
            predicted_direction BOOLEAN,
            predicted_probability DOUBLE,
            xgboost_prob DOUBLE,
            lightgbm_prob DOUBLE,
            lstm_prob DOUBLE,
            ensemble_prob DOUBLE,
            confidence_score DOUBLE,
            top_features JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, prediction_date, model_version)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_ml_pred_ticker ON ml_predictions(ticker)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_ml_pred_date ON ml_predictions(prediction_date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_ml_pred_target ON ml_predictions(target_date)")


def create_model_performance_table():
    """Create table for tracking model performance"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS model_performance (
            model_version VARCHAR NOT NULL,
            evaluation_date DATE NOT NULL,
            ticker VARCHAR,
            accuracy DOUBLE,
            precision DOUBLE,
            recall DOUBLE,
            f1_score DOUBLE,
            auc_roc DOUBLE,
            log_loss DOUBLE,
            brier_score DOUBLE,
            sharpe_ratio DOUBLE,
            total_predictions INTEGER,
            correct_predictions INTEGER,
            evaluation_period_days INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (model_version, evaluation_date, ticker)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_perf_model ON model_performance(model_version)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_perf_date ON model_performance(evaluation_date)")


def create_data_refresh_log_table():
    """Create table for tracking data refresh operations"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS data_refresh_log (
            refresh_id INTEGER PRIMARY KEY,
            data_source VARCHAR NOT NULL,
            refresh_start TIMESTAMP NOT NULL,
            refresh_end TIMESTAMP,
            status VARCHAR,  -- 'running', 'completed', 'failed'
            records_processed INTEGER,
            error_message VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    db.execute("CREATE SEQUENCE IF NOT EXISTS refresh_id_seq START 1")
    db.execute("CREATE INDEX IF NOT EXISTS idx_refresh_source ON data_refresh_log(data_source)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_refresh_status ON data_refresh_log(status)")


def create_data_retention_policy_table():
    """Create table for defining data retention policies"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS data_retention_policy (
            table_name VARCHAR PRIMARY KEY,
            retention_days INTEGER NOT NULL,
            archive_to_parquet BOOLEAN DEFAULT true,
            partition_column VARCHAR,
            description VARCHAR,
            last_cleanup TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def create_feature_drift_table():
    """Create table for monitoring feature drift"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS feature_drift (
            feature_name VARCHAR NOT NULL,
            analysis_date DATE NOT NULL,
            reference_start_date DATE,
            reference_end_date DATE,
            current_start_date DATE,
            current_end_date DATE,
            ks_statistic DOUBLE,
            psi_value DOUBLE,
            drift_detected BOOLEAN,
            drift_severity VARCHAR,  -- 'none', 'low', 'medium', 'high'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (feature_name, analysis_date)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_drift_feature ON feature_drift(feature_name)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_drift_date ON feature_drift(analysis_date)")


# =============================================================================
# SEC Data Tables
# =============================================================================

def create_sec_submissions_table():
    """Create table for SEC filing submissions metadata"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS sec_submissions (
            adsh VARCHAR NOT NULL,
            cik BIGINT NOT NULL,
            name VARCHAR,
            sic BIGINT,
            countryba VARCHAR,
            stprba VARCHAR,
            cityba VARCHAR,
            zipba VARCHAR,
            bas1 VARCHAR,
            bas2 VARCHAR,
            baph VARCHAR,
            countryma VARCHAR,
            stprma VARCHAR,
            cityma VARCHAR,
            zipma VARCHAR,
            mas1 VARCHAR,
            mas2 VARCHAR,
            countryinc VARCHAR,
            stprinc VARCHAR,
            ein BIGINT,
            former VARCHAR,
            changed VARCHAR,
            accession VARCHAR,
            form VARCHAR,
            period DATE,
            fy INTEGER,
            fp VARCHAR,
            filed DATE,
            accepted TIMESTAMP,
            preaccession VARCHAR,
            instance VARCHAR,
            nciks INTEGER,
            aciks VARCHAR,
            data_year INTEGER,
            data_quarter INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (adsh)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_sub_cik ON sec_submissions(cik)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_sub_form ON sec_submissions(form)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_sub_filed ON sec_submissions(filed)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_sub_period ON sec_submissions(period)")


def create_sec_financial_statements_table():
    """Create table for SEC financial statement numeric data"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS sec_financial_statements (
            adsh VARCHAR NOT NULL,
            tag VARCHAR NOT NULL,
            version VARCHAR,
            coreg VARCHAR,
            ddate DATE,
            qtrs INTEGER,
            uom VARCHAR,
            value DOUBLE,
            footnote VARCHAR,
            data_year INTEGER,
            data_quarter INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (adsh, tag, ddate, qtrs, coreg)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_fs_adsh ON sec_financial_statements(adsh)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_fs_tag ON sec_financial_statements(tag)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_fs_ddate ON sec_financial_statements(ddate)")


def create_sec_company_facts_table():
    """Create table for SEC company facts (XBRL data)"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS sec_company_facts (
            cik VARCHAR NOT NULL,
            concept VARCHAR NOT NULL,
            unit VARCHAR,
            value DOUBLE,
            end_date DATE,
            start_date DATE,
            fiscal_year INTEGER,
            fiscal_period VARCHAR,
            form VARCHAR,
            filed DATE,
            accn VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (cik, concept, end_date, form, accn)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_facts_cik ON sec_company_facts(cik)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_facts_concept ON sec_company_facts(concept)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_facts_end_date ON sec_company_facts(end_date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_facts_form ON sec_company_facts(form)")


def create_sec_filings_table():
    """Create table for SEC filing history"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS sec_filings (
            cik VARCHAR NOT NULL,
            accession_number VARCHAR NOT NULL,
            company_name VARCHAR,
            form VARCHAR,
            filing_date DATE,
            report_date DATE,
            primary_document VARCHAR,
            description VARCHAR,
            tickers VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (cik, accession_number)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_filings_cik ON sec_filings(cik)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_filings_form ON sec_filings(form)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_filings_date ON sec_filings(filing_date)")


def create_sec_fails_to_deliver_table():
    """Create table for SEC fails-to-deliver data"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS sec_fails_to_deliver (
            settlement_date DATE NOT NULL,
            cusip VARCHAR NOT NULL,
            symbol VARCHAR,
            quantity BIGINT,
            description VARCHAR,
            price DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (settlement_date, cusip)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_ftd_date ON sec_fails_to_deliver(settlement_date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_ftd_cusip ON sec_fails_to_deliver(cusip)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_ftd_symbol ON sec_fails_to_deliver(symbol)")


def create_sec_13f_holdings_table():
    """Create table for Form 13F institutional holdings"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS sec_13f_holdings (
            cik VARCHAR NOT NULL,
            filing_date DATE NOT NULL,
            report_date DATE,
            manager_name VARCHAR,
            cusip VARCHAR,
            issuer_name VARCHAR,
            title_class VARCHAR,
            value_usd BIGINT,
            shares_amount BIGINT,
            shares_type VARCHAR,
            investment_discretion VARCHAR,
            voting_authority_sole BIGINT,
            voting_authority_shared BIGINT,
            voting_authority_none BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (cik, filing_date, cusip)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_13f_cik ON sec_13f_holdings(cik)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_13f_filing_date ON sec_13f_holdings(filing_date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sec_13f_cusip ON sec_13f_holdings(cusip)")


def create_leverage_metrics_table():
    """Create table for leverage and margin metrics"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS leverage_metrics (
            ticker VARCHAR NOT NULL,
            date DATE NOT NULL,
            short_interest BIGINT,
            short_interest_ratio DOUBLE,
            days_to_cover DOUBLE,
            short_percent_float DOUBLE,
            shares_outstanding BIGINT,
            float_shares BIGINT,
            avg_volume_10d BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, date)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_leverage_ticker ON leverage_metrics(ticker)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_leverage_date ON leverage_metrics(date)")


def create_vix_term_structure_table():
    """Create table for VIX and volatility term structure"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS vix_term_structure (
            date DATE NOT NULL,
            vix DOUBLE,
            vix_3m DOUBLE,
            vix_6m DOUBLE,
            vvix DOUBLE,
            vix_term_spread DOUBLE,
            vix_regime VARCHAR,
            backwardation_ratio DOUBLE,
            stress_score DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_vix_date ON vix_term_structure(date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_vix_regime ON vix_term_structure(vix_regime)")


def create_leveraged_etf_data_table():
    """Create table for leveraged ETF tracking"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS leveraged_etf_data (
            ticker VARCHAR NOT NULL,
            date DATE NOT NULL,
            close DOUBLE,
            volume BIGINT,
            volume_ratio DOUBLE,
            intraday_volatility DOUBLE,
            tracking_error DOUBLE,
            premium_discount DOUBLE,
            stress_indicator DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, date)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_lev_etf_ticker ON leveraged_etf_data(ticker)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_lev_etf_date ON leveraged_etf_data(date)")


def create_margin_call_risk_table():
    """Create table for composite margin call risk scores"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS margin_call_risk (
            ticker VARCHAR NOT NULL,
            date DATE NOT NULL,
            leverage_score DOUBLE,
            volatility_score DOUBLE,
            options_score DOUBLE,
            liquidity_score DOUBLE,
            composite_risk_score DOUBLE,
            risk_level VARCHAR,
            vix_regime VARCHAR,
            short_interest_pct DOUBLE,
            put_call_ratio DOUBLE,
            iv_rank DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, date)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_margin_risk_ticker ON margin_call_risk(ticker)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_margin_risk_date ON margin_call_risk(date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_margin_risk_level ON margin_call_risk(risk_level)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_margin_composite ON margin_call_risk(composite_risk_score)")


def create_news_sentiment_table():
    """Create table for news article sentiment data"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS news_sentiment (
            id INTEGER PRIMARY KEY,
            ticker VARCHAR NOT NULL,
            title VARCHAR,
            description VARCHAR,
            source VARCHAR,
            published_at TIMESTAMP,
            url VARCHAR,
            sentiment_score DOUBLE,
            sentiment_label VARCHAR,  -- 'positive', 'negative', 'neutral'
            subjectivity DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_news_ticker ON news_sentiment(ticker)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_news_published ON news_sentiment(published_at)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_news_sentiment ON news_sentiment(sentiment_label)")


def create_sentiment_summary_table():
    """Create table for aggregated sentiment summaries"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_summary (
            ticker VARCHAR NOT NULL,
            analysis_date DATE NOT NULL,
            article_count INTEGER,
            avg_sentiment DOUBLE,
            median_sentiment DOUBLE,
            positive_count INTEGER,
            negative_count INTEGER,
            neutral_count INTEGER,
            sentiment_trend VARCHAR,  -- 'bullish', 'slightly_bullish', 'neutral', 'slightly_bearish', 'bearish'
            momentum DOUBLE,
            confidence DOUBLE,
            recommendation VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ticker, analysis_date)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_summary_ticker ON sentiment_summary(ticker)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_summary_date ON sentiment_summary(analysis_date)")


def create_google_trends_table():
    """Create table for Google Trends data"""
    db = get_db_connection()
    db.execute("""
        CREATE TABLE IF NOT EXISTS google_trends (
            keyword VARCHAR NOT NULL,
            date DATE NOT NULL,
            interest_value DOUBLE,
            geo VARCHAR DEFAULT 'US',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (keyword, date, geo)
        )
    """)
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_trends_keyword ON google_trends(keyword)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_trends_date ON google_trends(date)")


def create_all_tables():
    """Create all database tables"""
    print("Creating database schema...")
    
    create_fred_data_table()
    print("✓ Created fred_data table")
    
    create_yfinance_ohlcv_table()
    print("✓ Created yfinance_ohlcv table")
    
    create_options_data_table()
    print("✓ Created options_data table")
    
    create_market_indicators_table()
    print("✓ Created market_indicators table")
    
    create_technical_features_table()
    print("✓ Created technical_features table")
    
    create_derived_features_table()
    print("✓ Created derived_features table")
    
    create_ml_training_data_table()
    print("✓ Created ml_training_data table")
    
    create_ml_predictions_table()
    print("✓ Created ml_predictions table")
    
    create_model_performance_table()
    print("✓ Created model_performance table")
    
    create_data_refresh_log_table()
    print("✓ Created data_refresh_log table")
    
    create_data_retention_policy_table()
    print("✓ Created data_retention_policy table")
    
    create_feature_drift_table()
    print("✓ Created feature_drift table")
    
    # Margin Call Risk Tables
    create_leverage_metrics_table()
    print("✓ Created leverage_metrics table")
    
    create_vix_term_structure_table()
    print("✓ Created vix_term_structure table")
    
    create_leveraged_etf_data_table()
    print("✓ Created leveraged_etf_data table")
    
    create_margin_call_risk_table()
    print("✓ Created margin_call_risk table")
    
    # SEC Data Tables
    create_sec_submissions_table()
    print("✓ Created sec_submissions table")
    
    create_sec_financial_statements_table()
    print("✓ Created sec_financial_statements table")
    
    create_sec_company_facts_table()
    print("✓ Created sec_company_facts table")
    
    create_sec_filings_table()
    print("✓ Created sec_filings table")
    
    create_sec_fails_to_deliver_table()
    print("✓ Created sec_fails_to_deliver table")
    
    create_sec_13f_holdings_table()
    print("✓ Created sec_13f_holdings table")
    create_news_sentiment_table()
    print("✓ Created news_sentiment table")
    
    create_sentiment_summary_table()
    print("✓ Created sentiment_summary table")
    
    create_google_trends_table()
    print("✓ Created google_trends table")
    
    print("\nDatabase schema created successfully!")


def drop_all_tables():
    """Drop all tables (use with caution!)"""
    db = get_db_connection()
    tables = [
        'cboe_vix_term_structure',
        'cboe_vix_history',
        'ici_etf_weekly_flows',
        'ici_etf_flows',
        'google_trends',
        'sentiment_summary',
        'news_sentiment',
        'margin_call_risk',
        'leveraged_etf_data',
        'vix_term_structure',
        'leverage_metrics',
        'feature_drift',
        'data_refresh_log',
        'model_performance',
        'ml_predictions',
        'ml_training_data',
        'derived_features',
        'technical_features',
        'market_indicators',
        'options_data',
        'yfinance_ohlcv',
        'fred_data',
        'sec_submissions',
        'sec_financial_statements',
        'sec_company_facts',
        'sec_filings',
        'sec_fails_to_deliver',
        'sec_13f_holdings'
    ]
    
    for table in tables:
        db.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"✓ Dropped {table}")
    
    print("\nAll tables dropped!")
