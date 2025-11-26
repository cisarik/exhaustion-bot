
from data_loader import DataLoader
import logging

logging.basicConfig(level=logging.INFO)

# Download 5m data
loader = DataLoader(exchange_id='binance', symbol='ADA/USDT', timeframe='5m')
# 5000 candles of 5m = ~17 days
data = loader.fetch_data(limit=5000, force_update=True)
print(f"Downloaded {len(data)} 5m candles.")
