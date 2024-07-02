import os
import ccxt
from datetime import datetime
import dotenv

dotenv.load_dotenv()

api_key = os.environ["BINANCE_API_KEY"],
secret_key = os.environ["BINANCE_SECRET_KEY"],

def get_candlestick_data(symbol, interval, limit=100):
    binance_client = ccxt.binance({
        'apiKey': api_key,
        'secret': secret_key,
    })

    try:
        candlesticks = binance_client.fetch_ohlcv(symbol, interval, limit=limit)
        formatted_candlesticks = [{
            'timestamp': datetime.utcfromtimestamp(candlestick[0] / 1000.0).strftime('%Y-%m-%d %H:%M:%S'),
            'open': candlestick[1],
            'high': candlestick[2],
            'low': candlestick[3],
            'close': candlestick[4],
            'volume': candlestick[5]
        } for candlestick in candlesticks]
        return formatted_candlesticks
    except ccxt.NetworkError as e:
        print(f"Network error: {e}")
    except ccxt.ExchangeError as e:
        print(f"Exchange error: {e}")
    except Exception as e:
        print(f"Error: {e}")
