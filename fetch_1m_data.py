
from data_loader import DataLoader
import logging

logging.basicConfig(level=logging.INFO)

# Download 1m data for HFT TDD
loader = DataLoader(exchange_id='binance', symbol='ADA/USDT', timeframe='1m')
# We need a lot of data for 1m backtest, say 10,000 candles (~7 days)
data = loader.fetch_data(limit=10000, force_update=True)
print(f"Downloaded {len(data)} 1m candles.")
