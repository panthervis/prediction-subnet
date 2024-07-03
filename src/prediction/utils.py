from typing import Literal, Any
import datetime
import csv
from datetime import datetime, timedelta
import random

def iso_timestamp_now() -> str:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    iso_now = now.isoformat()
    return iso_now


def log(
    msg: str,
    *values: object,
    sep: str | None = " ",
    end: str | None = "\n",
    file: Any | None = None,
    flush: Literal[False] = False,
):
    print(
        f"[{iso_timestamp_now()}] " + msg,
        *values,
        sep=sep,
        end=end,
        file=file,
        flush=flush,
    )

def export_to_csv(data, filename):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['time', 'pair', 'quoteAmount', 'open', 'high', 'low', 'close'])

        for candlestick in data:
            time = candlestick['timestamp']
            pair = f"{candlestick['baseCurrency']['symbol']}/{candlestick['quoteCurrency']['symbol']}" if 'baseCurrency' in candlestick else 'UNI/USDT'
            quote_amount = candlestick['quoteAmount'] if 'quoteAmount' in candlestick else candlestick['volume']
            open_price = candlestick['open']
            high_price = candlestick['high']
            low_price = candlestick['low']
            close_price = candlestick['close']

            writer.writerow([time, pair, quote_amount, open_price, high_price, low_price, close_price])
            
def dateToTimestamp(date_string):
    formatted_date_string = date_string.replace('h', ':').replace('m', ':').replace('s', '')
    formatted_date_string = formatted_date_string.replace('.', '-')

    date_format = "%Y-%m-%d.%H:%M:%S"
    date_object = datetime.strptime(formatted_date_string, date_format)

    return date_object.timestamp()

def get_random_future_timestamp(hours_ahead=8):
    now = datetime.now()
    random_seconds = random.randint(0, hours_ahead * 3600)
    random_future_timestamp = now + timedelta(seconds=random_seconds)
    
    return random_future_timestamp