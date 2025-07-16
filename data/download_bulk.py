import json
import pytz
import warnings
import requests
from datetime import datetime, timedelta
from urllib3.exceptions import NotOpenSSLWarning

# Suppress OpenSSL warning
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

# ─────────────────────────────────────────────────────────────────────────────
# API Utilities
# ─────────────────────────────────────────────────────────────────────────────

def format_response(response_obj):
    """
    Formats the raw response from the API into a list of structured candle records.

    Args:
        response_obj (list): List of dictionaries representing candlestick data.

    Returns:
        list: Formatted list of candle records.
    """
    if not isinstance(response_obj, list):
        print("[Error] format_response: response_obj must be a list.")
        return []

    formatted_data = []
    for i, candle in enumerate(response_obj):
        try:

            ist_start = convert_epoch_to_ist(candle['t'])
            ist_end = convert_epoch_to_ist(candle['T'])

            formatted_data.append({
                'ts': ist_start.strftime('%Y-%m-%d %H:%M:00'),
                'start_time': ist_start.strftime('%Y-%m-%d %H:%M:%S:%f'),
                'end_time': ist_end.strftime('%Y-%m-%d %H:%M:%S:%f'),
                'start_epoch': candle['t'],
                'end_epoch': candle['T'],
                'symbol': candle['s'],
                'interval': candle['i'],
                'opening_price': float(candle['o']),
                'closing_price': float(candle['c']),
                'highest_price': float(candle['h']),
                'lowest_price': float(candle['l']),
                'volume_traded': float(candle['v']),
                'trade_count': candle['n']
            })
        except KeyError as ke:
            print(f"[Warning] Missing key {ke} in candle at index {i}. Skipping this record.")
        except Exception as e:
            print(f"[Error] Failed to format candle at index {i}: {e}")

    return formatted_data



def get_crypto_price(start_epoch, end_epoch, interval,coin):
    """Fetch cryptocurrency candle data from Hyperliquid API."""
    if not isinstance(start_epoch, int) or not isinstance(end_epoch, int):
        return {"error": "Epoch values must be integers."}
    if start_epoch >= end_epoch:
        return {"error": "start_epoch must be less than end_epoch."}
    if interval not in {"1m", "15m", "1h"}:
        return {"error": f"Invalid interval. Choose from: 1m, 15m, 1h."}

    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": coin,
            "interval": interval,
            "startTime": start_epoch,
            "endTime": end_epoch
        }
    }

    try:
        res = requests.post(
            'https://api.hyperliquid.xyz/info',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload),
            timeout=10
        )
        if res.status_code != 200:
            return {"error": f"API Error {res.status_code}", "details": res.text}
        return format_response(res.json())
    except requests.RequestException as e:
        return {"error": "API request failed", "details": str(e)}

# ─────────────────────────────────────────────────────────────────────────────
# Time Conversion
# ─────────────────────────────────────────────────────────────────────────────

def convert_epoch_to_ist(epoch_ms):
    """
    Convert epoch timestamp in milliseconds to IST datetime.

    Args:
        epoch_ms (int or float): Epoch time in milliseconds.

    Returns:
        datetime: Time converted to Asia/Kolkata timezone.

    Raises:
        ValueError: If input is not a valid number.
    """
    try:
        if not isinstance(epoch_ms, (int, float)):
            raise ValueError("epoch_ms must be an integer or float representing milliseconds since epoch.")

        utc_time = datetime.fromtimestamp(epoch_ms / 1000, tz=pytz.utc)
        return utc_time.astimezone(pytz.timezone('Asia/Kolkata'))

    except Exception as e:
        print(f"[Error] convert_epoch_to_ist failed for input {epoch_ms}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Main Loop
# ─────────────────────────────────────────────────────────────────────────────

def get_start_end_epoch(end_time, look_back):
    """
    Calculate start and end epoch timestamps in milliseconds.

    Args:
        end_time (datetime): The end datetime to calculate back from.
        look_back (int): Number of minutes to look back.

    Returns:
        tuple: (epoch_start, epoch_end) in milliseconds.

    Raises:
        ValueError: If inputs are invalid.
    """

    look_back = look_back-1
    try:
        if not isinstance(end_time, datetime):
            raise ValueError("end_time must be a datetime object.")
        if not isinstance(look_back, int) or look_back <= 0:
            raise ValueError("look_back must be a positive integer.")

        prev_minutes = (end_time - timedelta(minutes=1)).replace(second=0, microsecond=0)
        start_minutes = prev_minutes - timedelta(minutes=look_back)
        end_seconds = prev_minutes + timedelta(seconds=59, milliseconds=999)

        epoch_start = int(start_minutes.timestamp() * 1000)
        epoch_end = int(end_seconds.timestamp() * 1000)

        return epoch_start, epoch_end

    except Exception as e:
        print(f"[Error] get_start_end_epoch failed: {e}")
        return None, None


## Use Function

# scrapping_interval = '1m'
# current_time =  datetime.now()
# look_back = 180
# start_epoch,end_epoch = get_start_end_epoch("x",look_back)
#
# response_data = get_crypto_price(start_epoch, end_epoch, scrapping_interval)
#
# print(response_data)