#Generates technical signals only (e.g., crossover, RSI).

# Calculate Trading Indicators

# 1. Relative Strength Index (RSI)

def calculate_rsi(df, window=14):
    delta = df['closing_price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    return df

# 2. Moving Average Convergence Divergence (MACD)

def calculate_macd(df, fast=12, slow=26, signal=9):
    df['MACD'] = df['closing_price'].ewm(span=fast, adjust=False).mean() - df['closing_price'].ewm(span=slow, adjust=False).mean()
    df['MACD_signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()

    return df

# 3. Bollinger Bands

def calculate_bollinger_bands(df, window=20):
    df['MA_20'] = df['closing_price'].rolling(window=window).mean()
    df['STD_20'] = df['closing_price'].rolling(window=window).std()
    df['Bollinger_upper'] = df['MA_20'] + (2 * df['STD_20'])
    df['Bollinger_lower'] = df['MA_20'] - (2 * df['STD_20'])

    return df

# 4. Simple Moving Average (SMA)

def calculate_sma(df, window=50):
    df['SMA_50'] = df['closing_price'].rolling(window=50).mean()
    df['SMA_20'] = df['closing_price'].rolling(window=20).mean()

    return df


# 5. EMA (Exponential Moving Average)
def calculate_ema(df, periods=[9, 21]):
    for period in periods:
        df[f'EMA_{period}'] = df['closing_price'].ewm(span=period, adjust=False).mean()
    return df

# 6. ATR (Average True Range)
def calculate_atr(df, period=14):
    df['H-L'] = df['highest_price'] - df['lowest_price']
    df['H-PC'] = abs(df['highest_price'] - df['closing_price'].shift(1))
    df['L-PC'] = abs(df['lowest_price'] - df['closing_price'].shift(1))

    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df[f'ATR_{period}'] = df['TR'].rolling(window=period).mean()

    df.drop(['H-L', 'H-PC', 'L-PC', 'TR'], axis=1, inplace=True)
    return df

# 7. OBV (On-Balance Volume)

def calculate_obv(df):
    obv = [0]
    for i in range(1, len(df)):
        if df['closing_price'].iloc[i] > df['closing_price'].iloc[i - 1]:
            obv.append(obv[-1] + df['volume_traded'].iloc[i])
        elif df['closing_price'].iloc[i] < df['closing_price'].iloc[i - 1]:
            obv.append(obv[-1] - df['volume_traded'].iloc[i])
        else:
            obv.append(obv[-1])
    df['OBV'] = obv
    return df

# 8. VWAP (Volume Weighted Average Price)
# VWAP typically resets daily, but for backtesting intraday logic:

def calculate_vwap(df):
    df['cum_volume'] = df['volume_traded'].cumsum()
    df['cum_vp'] = (df['closing_price'] * df['volume_traded']).cumsum()
    df['VWAP'] = df['cum_vp'] / df['cum_volume']
    df.drop(['cum_volume', 'cum_vp'], axis=1, inplace=True)
    return df


# Determine signals and weights

def generate_signals(data):
    signals = []

    # RSI Signal (25%)
    if data['RSI'].iloc[-1] < 30:
        signals.append(1 * 0.25)  # Buy
    elif data['RSI'].iloc[-1] > 70:
        signals.append(-1 * 0.25)  # Sell
    else:
        signals.append(0)

    # MACD Signal (20%)
    if data['MACD'].iloc[-1] > data['MACD_signal'].iloc[-1]:
        signals.append(1 * 0.20)  # Buy
    elif data['MACD'].iloc[-1] < data['MACD_signal'].iloc[-1]:
        signals.append(-1 * 0.20)  # Sell
    else:
        signals.append(0)

    # Bollinger Bands Signal (20%)
    if data['closing_price'].iloc[-1] <= data['Bollinger_lower'].iloc[-1]:
        signals.append(1 * 0.20)  # Buy
    elif data['closing_price'].iloc[-1] >= data['Bollinger_upper'].iloc[-1]:
        signals.append(-1 * 0.20)  # Sell
    else:
        signals.append(0)

    # SMA Signal (15%)
    if data['closing_price'].iloc[-1] > data['SMA_20'].iloc[-1]:
        signals.append(1 * 0.15)  # Buy
    elif data['closing_price'].iloc[-1] < data['SMA_20'].iloc[-1]:
        signals.append(-1 * 0.15)  # Sell
    else:
        signals.append(0)

    # Combined SMA Confirmation (20%)
    if data['SMA_20'].iloc[-1] > data['SMA_50'].iloc[-1]:
        signals.append(1 * 0.20)  # Buy
    elif data['SMA_20'].iloc[-1] < data['SMA_50'].iloc[-1]:
        signals.append(-1 * 0.20)  # Sell
    else:
        signals.append(0)

    return sum(signals)