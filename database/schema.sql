-- AMDX/XAMD 模式分析系统数据库结构
-- 创建时间: 2024

-- ==================== 交易对配置表 ====================
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    display_name TEXT,
    exchange TEXT NOT NULL DEFAULT 'binance',
    is_active BOOLEAN DEFAULT 1,
    data_start_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 周数据表 ====================
CREATE TABLE IF NOT EXISTS weekly_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_id INTEGER NOT NULL,
    week_start DATETIME NOT NULL,           -- 周一早上8点(UTC+9)
    week_end DATETIME NOT NULL,             -- 下周一早上7:59(UTC+9)
    week_start_utc DATETIME NOT NULL,       -- UTC时间（用于API查询）
    week_end_utc DATETIME NOT NULL,         -- UTC时间
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,          -- 一年中的第几周
    week_of_month INTEGER NOT NULL,         -- 一月中的第几周
    week_high DECIMAL(20, 8) NOT NULL,      -- 周最高价
    week_low DECIMAL(20, 8) NOT NULL,       -- 周最低价
    week_open DECIMAL(20, 8),               -- 周开盘价
    week_close DECIMAL(20, 8),              -- 周收盘价
    data_points INTEGER,                     -- 数据点数量
    data_quality_score INTEGER DEFAULT 100, -- 数据质量分数 (0-100)
    data_source TEXT DEFAULT 'binance_api',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol_id) REFERENCES symbols(id),
    UNIQUE(symbol_id, week_start)
);

-- 周数据索引
CREATE INDEX IF NOT EXISTS idx_weekly_symbol_year_month ON weekly_data(symbol_id, year, month);
CREATE INDEX IF NOT EXISTS idx_weekly_start ON weekly_data(week_start);
CREATE INDEX IF NOT EXISTS idx_weekly_year_month ON weekly_data(year, month);

-- ==================== 月度模式判断表 ====================
CREATE TABLE IF NOT EXISTS monthly_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    first_week_id INTEGER NOT NULL,         -- 该月第一周的数据ID
    previous_week_id INTEGER,               -- 前一周的数据ID
    first_week_start DATETIME,              -- 第一周开始时间
    pattern TEXT NOT NULL CHECK(pattern IN ('AMDX', 'XAMD')),
    first_week_high DECIMAL(20, 8) NOT NULL,
    first_week_low DECIMAL(20, 8) NOT NULL,
    previous_week_high DECIMAL(20, 8),
    previous_week_low DECIMAL(20, 8),
    is_breakout_up BOOLEAN DEFAULT 0,       -- 是否向上突破
    is_breakout_down BOOLEAN DEFAULT 0,     -- 是否向下突破
    breakout_up_amount DECIMAL(20, 8),      -- 向上突破金额
    breakout_down_amount DECIMAL(20, 8),    -- 向下突破金额
    breakout_up_percent DECIMAL(10, 4),     -- 向上突破幅度(%)
    breakout_down_percent DECIMAL(10, 4),   -- 向下突破幅度(%)
    data_quality_score INTEGER DEFAULT 100, -- 数据质量分数
    notes TEXT,                              -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol_id) REFERENCES symbols(id),
    FOREIGN KEY (first_week_id) REFERENCES weekly_data(id),
    FOREIGN KEY (previous_week_id) REFERENCES weekly_data(id),
    UNIQUE(symbol_id, year, month)
);

-- 月度模式索引
CREATE INDEX IF NOT EXISTS idx_patterns_symbol_year ON monthly_patterns(symbol_id, year);
CREATE INDEX IF NOT EXISTS idx_patterns_pattern ON monthly_patterns(pattern);
CREATE INDEX IF NOT EXISTS idx_patterns_year_month ON monthly_patterns(year, month);

-- ==================== 数据质量日志表 ====================
CREATE TABLE IF NOT EXISTS data_quality_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_id INTEGER,
    check_date DATETIME NOT NULL,
    check_type TEXT NOT NULL,               -- 检查类型
    status TEXT NOT NULL,                   -- PASS/WARN/FAIL
    message TEXT,
    affected_records INTEGER,
    details TEXT,                           -- JSON格式的详细信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- ==================== 数据更新日志表 ====================
CREATE TABLE IF NOT EXISTS update_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_id INTEGER,
    update_type TEXT NOT NULL,              -- FULL/INCREMENTAL
    start_date DATETIME,
    end_date DATETIME,
    records_added INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    status TEXT NOT NULL,                   -- SUCCESS/FAILED/PARTIAL
    error_message TEXT,
    execution_time_seconds DECIMAL(10, 2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- ==================== 系统配置表 ====================
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认配置
INSERT OR IGNORE INTO system_config (key, value, description) VALUES
('last_update', NULL, '最后更新时间'),
('data_version', '1.0', '数据版本'),
('schema_version', '1.0', '数据库结构版本');

-- ==================== 小时数据表 ====================
CREATE TABLE IF NOT EXISTS hourly_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_id INTEGER NOT NULL,
    timestamp INTEGER NOT NULL,                -- Unix时间戳（秒）
    datetime DATETIME NOT NULL,                -- 日期时间（UTC+9）
    open DECIMAL(20, 8) NOT NULL,              -- 开盘价
    high DECIMAL(20, 8) NOT NULL,              -- 最高价
    low DECIMAL(20, 8) NOT NULL,               -- 最低价
    close DECIMAL(20, 8) NOT NULL,             -- 收盘价
    volume DECIMAL(20, 8),                      -- 成交量
    data_source TEXT DEFAULT 'api',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol_id) REFERENCES symbols(id),
    UNIQUE(symbol_id, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_hourly_symbol_timestamp ON hourly_data(symbol_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_hourly_datetime ON hourly_data(datetime);

-- ==================== 日数据表 ====================
CREATE TABLE IF NOT EXISTS daily_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_id INTEGER NOT NULL,
    trade_date DATE NOT NULL,                  -- 交易日期（UTC+9）
    trade_date_utc9 DATETIME NOT NULL,         -- 交易日期时间（UTC+9，当天00:00:00）
    day_of_week INTEGER NOT NULL,              -- 星期几（0=周一, 6=周日）
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_high DECIMAL(20, 8) NOT NULL,          -- 日最高价
    day_low DECIMAL(20, 8) NOT NULL,           -- 日最低价
    day_open DECIMAL(20, 8) NOT NULL,          -- 日开盘价
    day_close DECIMAL(20, 8) NOT NULL,         -- 日收盘价
    day_volume DECIMAL(20, 8),                  -- 日成交量
    data_points INTEGER,                        -- 数据点数量（小时K线数，正常24个）
    data_quality_score INTEGER DEFAULT 100,    -- 数据质量分数
    data_source TEXT DEFAULT 'binance_api',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol_id) REFERENCES symbols(id),
    UNIQUE(symbol_id, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_symbol_date ON daily_data(symbol_id, trade_date);
CREATE INDEX IF NOT EXISTS idx_daily_year_month ON daily_data(year, month);
CREATE INDEX IF NOT EXISTS idx_daily_day_of_week ON daily_data(day_of_week);

-- ==================== 周度模式表（7字母模式）====================
CREATE TABLE IF NOT EXISTS weekly_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_id INTEGER NOT NULL,
    week_start DATETIME NOT NULL,              -- 周一早上8点(UTC+9)
    week_end DATETIME NOT NULL,                -- 下周一早上7:59(UTC+9)
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    -- 周一到周日的日数据ID
    monday_id INTEGER,
    tuesday_id INTEGER,
    wednesday_id INTEGER,
    thursday_id INTEGER,
    friday_id INTEGER,
    saturday_id INTEGER,
    sunday_id INTEGER,
    previous_sunday_id INTEGER,                 -- 前一周周日数据ID
    -- 周度模式（固定为XAMDXAM或AMDXAMD）
    pattern TEXT NOT NULL CHECK(pattern IN ('XAMDXAM', 'AMDXAMD')),
    -- 周一相对于上周日的数据
    monday_high DECIMAL(20, 8),
    monday_low DECIMAL(20, 8),
    previous_sunday_high DECIMAL(20, 8),
    previous_sunday_low DECIMAL(20, 8),
    monday_is_breakout_up BOOLEAN DEFAULT 0,   -- 周一是否向上突破
    monday_is_breakout_down BOOLEAN DEFAULT 0, -- 周一是否向下突破
    monday_breakout_up_percent DECIMAL(10, 4), -- 周一向上突破幅度(%)
    monday_breakout_down_percent DECIMAL(10, 4), -- 周一下向突破幅度(%)
    monday_trend_detail TEXT,                   -- 周一走势明细（相对于上周日）
    -- 走势明细（每天相对于前一天的走势，用于分析）
    tuesday_trend_detail TEXT,                 -- 周二走势明细（相对于周一）
    wednesday_trend_detail TEXT,               -- 周三走势明细（相对于周二）
    thursday_trend_detail TEXT,                -- 周四走势明细（相对于周三）
    friday_trend_detail TEXT,                  -- 周五走势明细（相对于周四）
    saturday_trend_detail TEXT,                -- 周六走势明细（相对于周五）
    sunday_trend_detail TEXT,                  -- 周日走势明细（相对于周六）
    -- 走势明细的突破数据（每天的突破幅度百分比）
    tuesday_breakout_up_percent DECIMAL(10, 4),
    tuesday_breakout_down_percent DECIMAL(10, 4),
    wednesday_breakout_up_percent DECIMAL(10, 4),
    wednesday_breakout_down_percent DECIMAL(10, 4),
    thursday_breakout_up_percent DECIMAL(10, 4),
    thursday_breakout_down_percent DECIMAL(10, 4),
    friday_breakout_up_percent DECIMAL(10, 4),
    friday_breakout_down_percent DECIMAL(10, 4),
    saturday_breakout_up_percent DECIMAL(10, 4),
    saturday_breakout_down_percent DECIMAL(10, 4),
    sunday_breakout_up_percent DECIMAL(10, 4),
    sunday_breakout_down_percent DECIMAL(10, 4),
    data_quality_score INTEGER DEFAULT 100,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol_id) REFERENCES symbols(id),
    FOREIGN KEY (monday_id) REFERENCES daily_data(id),
    FOREIGN KEY (tuesday_id) REFERENCES daily_data(id),
    FOREIGN KEY (wednesday_id) REFERENCES daily_data(id),
    FOREIGN KEY (thursday_id) REFERENCES daily_data(id),
    FOREIGN KEY (friday_id) REFERENCES daily_data(id),
    FOREIGN KEY (saturday_id) REFERENCES daily_data(id),
    FOREIGN KEY (sunday_id) REFERENCES daily_data(id),
    FOREIGN KEY (previous_sunday_id) REFERENCES daily_data(id),
    UNIQUE(symbol_id, week_start)
);

CREATE INDEX IF NOT EXISTS idx_weekly_patterns_symbol_year ON weekly_patterns(symbol_id, year);
CREATE INDEX IF NOT EXISTS idx_weekly_patterns_pattern ON weekly_patterns(pattern);
CREATE INDEX IF NOT EXISTS idx_weekly_patterns_week_start ON weekly_patterns(week_start);

