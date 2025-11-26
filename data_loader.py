import ccxt
import pandas as pd
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, exchange_id='binance', symbol='ADA/USDT', timeframe='15m', data_dir='data'):
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.timeframe = timeframe
        self.data_dir = data_dir
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        self.filename = os.path.join(data_dir, f"{exchange_id}_{symbol.replace('/', '')}_{timeframe}.csv")
        
        try:
            self.exchange = getattr(ccxt, exchange_id)()
        except AttributeError:
            logger.error(f"Exchange {exchange_id} not found in ccxt.")
            raise

    def fetch_data(self, limit=1000, force_update=False) -> list[float]:
        """
        Fetches OHLCV data. 
        Tries to load from CSV first. If not found or force_update is True, fetches from API.
        Returns a list of CLOSE prices.
        """
        if not force_update and os.path.exists(self.filename):
            logger.info(f"Loading data from {self.filename}...")
            df = pd.read_csv(self.filename)
            # Ensure we have enough data (allow 10% margin)
            if len(df) >= limit * 0.9:
                return df['close'].tolist()
            else:
                logger.info(f"Cached data insufficient ({len(df)} < {limit}). Fetching fresh data...")
        
        logger.info(f"Fetching approx {limit} candles for {self.symbol} from {self.exchange_id}...")
        try:
            all_ohlcv = []
            # Calculate start time: limit * timeframe_in_ms
            timeframe_ms = 15 * 60 * 1000 
            # Ensure we go back enough time. Add extra buffer.
            duration_ms = (limit + 100) * timeframe_ms
            start_timestamp = self.exchange.milliseconds() - duration_ms
            
            target_candles = limit
            
            while len(all_ohlcv) < target_candles:
                # Use 'since' parameter to fetch sequentially
                current_since = start_timestamp + (len(all_ohlcv) * timeframe_ms)
                
                ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, since=current_since, limit=720) # Kraken usually limits to 720
                if not ohlcv:
                    break
                
                all_ohlcv.extend(ohlcv)
                
                if len(ohlcv) < 10: # End of data
                    break
                    
                # Small delay to be nice to API
                import time
                time.sleep(0.2)
            
            # Sort and Deduplicate
            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
            
            # If we have too many, trim from start
            if len(df) > limit:
                df = df.iloc[-limit:]
            
            # Save to CSV
            df.to_csv(self.filename, index=False)
            logger.info(f"Data saved to {self.filename} ({len(df)} rows)")
            
            return df['close'].tolist()
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            # Fallback to synthetic if fetch fails? Or raise?
            # For robustness, let's raise so we know optimization is broken.
            raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loader = DataLoader()
    data = loader.fetch_data(limit=100)
    print(f"Fetched {len(data)} candles. Last close: {data[-1]}")
