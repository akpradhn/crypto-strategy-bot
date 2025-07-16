'''
Read Last N Entries and Generate Recommendations
'''

import pandas as pd

from data.download_bulk import get_start_end_epoch, get_crypto_price, convert_epoch_to_ist
from strategy.strategy_engine import generate_signals, calculate_rsi, calculate_macd, calculate_bollinger_bands, \
    calculate_sma, calculate_ema, calculate_atr, calculate_obv, calculate_vwap

pd.options.mode.chained_assignment = None

# Final recommendation
def get_recommendation(score):
    if score >= 0.5:
        return "LONG"
    elif -0.5 < score < 0.5:
        return "HOLD"
    else:
        return "SHORT"

def get_tp_sl_multipliers(percent=1):
    """
    Given a percent (e.g., 1 or 2), return the take-profit and stop-loss multipliers.

    Args:
        percent (int or float): Desired % for TP/SL

    Returns:
        tuple: (take_profit_multiplier, stop_loss_multiplier)
    """
    if percent <= 0 or percent >= 100:
        raise ValueError("Percent must be between 0 and 100")

    take_profit = 1 + (percent / 100)
    stop_loss = 1 - (percent / 100)

    return round(take_profit, 4), round(stop_loss, 4)

# Step 4: Generate Recommendation
def generate_recommendation(df,trade_margin):

    last_row = df.iloc[-1]

    # Default values
    signal = None
    take_profit = None
    stop_loss = None
    limit_order_price = None

    # Generate signals and calculate score
    score = generate_signals(df)
    signal = get_recommendation(score)

    tp, sl = get_tp_sl_multipliers(trade_margin)

    # If no condition triggers, recommend HOLD
    if signal is None:
        signal = "HOLD: No clear signal."

    # Define take profit, stop loss, and limit order price

    if "LONG" in signal:
        take_profit = last_row['closing_price'] * tp
        stop_loss = last_row['closing_price'] * sl
        limit_order_price = last_row['closing_price'] * 0.995 # Buy cheaper

    elif "SHORT" in signal:
        take_profit = last_row['closing_price'] * sl
        stop_loss = last_row['closing_price'] * tp
        limit_order_price = last_row['closing_price'] * 1.005  # Sell higher


    df_v1 = df.reset_index()

    df_v1 = df_v1.tail(1)
    df_v1['recommendation'] = signal
    df_v1['take_profit'] = take_profit
    df_v1['stop_loss'] = stop_loss
    df_v1['limit_order_price'] = limit_order_price

    return df_v1


def calculate_all_indicators(df):
    try:
        df = calculate_rsi(df)
        df = calculate_macd(df)
        df = calculate_bollinger_bands(df)
        df = calculate_sma(df)
        df = calculate_ema(df)
        df = calculate_atr(df)
        df = calculate_obv(df)
        df = calculate_vwap(df)
        return df
    except Exception as e:
        print(f"[Error] Failed to calculate indicators: {e}")
        return df

# Get the recommendation for the next minute

def generate_crypto_recommendations(config):

    scrapping_interval = config['SCRAPPING_INTERVAL']
    look_back = config['LOOK_BACK']
    trade_margin = config['TRADE_MARGIN']
    current_time = config['CURRENT_TIME']
    coin = config['COIN']

    # Download Historical Data

    start_epoch,end_epoch = get_start_end_epoch(current_time,look_back)

    response_data = get_crypto_price(start_epoch, end_epoch, scrapping_interval,coin)

    historical_price_raw = pd.DataFrame(response_data)


# Create datetime index with 1-minute frequency
#-----------------------------------------------------------

    start_time = convert_epoch_to_ist(start_epoch).strftime("%Y-%m-%d %H:%M:00")
    end_time = convert_epoch_to_ist(end_epoch).strftime("%Y-%m-%d %H:%M:00")

    time_range = pd.date_range(start=start_time, end=end_time, freq="1min").strftime('%Y-%m-%d %H:%M:00').tolist()

    ts_index = pd.DataFrame({"ts": time_range})

    ## Data Cleaning

    historical_price_v0 = ts_index.merge(historical_price_raw,on='ts',how='left')

    historical_price_v0.set_index('ts', inplace=True)

    ## Check If Missing Values exists

    missing_values_exist =  historical_price_v0.isnull().values.any()
    # print(f'Missing Values exists ?? {missing_values_exist}')

    ## TO DO
    ## Add Logic to fill missing values . For Now proceeding with no missing values as directly Calling API

    historical_price_v1 = calculate_all_indicators(historical_price_v0)

    recommendation_v0 = generate_recommendation(historical_price_v1,trade_margin)

    expected_cols = [
        # Time & Metadata
        'ts', 'start_time','end_time', 'start_epoch', 'end_epoch', 'symbol', 'interval',

        # Price & Volume
        'opening_price', 'closing_price', 'highest_price', 'lowest_price','volume_traded', 'trade_count',

        # Indicators
        'RSI', 'MACD', 'MACD_signal','MA_20', 'SMA_20', 'SMA_50','EMA_9', 'EMA_21','STD_20', 'Bollinger_upper', 'Bollinger_lower','ATR_14', 'OBV', 'VWAP',

        # Strategy / Output
        'recommendation', 'take_profit', 'stop_loss', 'limit_order_price'
    ]

    recommendation_dict = recommendation_v0[expected_cols].to_dict(orient="records")

    return recommendation_dict