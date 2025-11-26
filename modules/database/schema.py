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
    
    create_feature_drift_table()
    print("✓ Created feature_drift table")
    
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
        'google_trends',
        'sentiment_summary',
        'news_sentiment',
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
        'fred_data'
    ]
    
    for table in tables:
        db.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"✓ Dropped {table}")
    
    print("\nAll tables dropped!")
