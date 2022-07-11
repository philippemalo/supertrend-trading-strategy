import ccxt
import pandas as pd
# pd.set_option('display.max_rows', None)
from ta.volatility import average_true_range
import schedule
import time
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
import os
from dotenv import load_dotenv

load_dotenv()

def supertrend(df: pd.DataFrame, period: int=15, multiplier: int=3):
    # Calculating Average True Range on candlesticks data.
    df['atr'] = average_true_range(high=df['high'], low=df['low'], close=df['close'], window=period)
    # Basic upper and lower bands
    hl2 = (df['high'] + df['low']) / 2
    df['upperband'] = hl2 + (multiplier * df['atr'])
    df['lowerband'] = hl2 - (multiplier * df['atr'])
    df['upperband'] = hl2 + (multiplier * df['atr'])
    df['lowerband'] = hl2 - (multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1, len(df.index)):
        previous = current - 1
        
        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]

    return df


def check_buy_sell_signals(df: pd.DataFrame):
    print('Checking for buy and sell signal')
    print(df.tail(5))
    if df['in_uptrend'].iloc[-1] == True and df['in_uptrend'].iloc[-2] == False:
        print('BUY!')
    elif df['in_uptrend'].iloc[-1] == False and df['in_uptrend'].iloc[-2] == True:
        print('SELL!')
    else:
        print('No signal')


def run_bot():
    key = os.getenv('FTX_BOT_API_KEY')
    secret = os.getenv('FTX_BOT_API_SECRET')
    exchange = ccxt.ftx({
        'apiKey': key,
        'secret': secret
    })
    exchange.headers = {
        'FTX-SUBACCOUNT': 'bot'
    }

    print(f'Fetching new candles for {datetime.now().isoformat()}')
    candles = exchange.fetch_ohlcv('BTC/USD', timeframe='1m', limit=120)
    df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    supertrend_data = supertrend(df)

    check_buy_sell_signals(supertrend_data)

schedule.every(15).seconds.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)