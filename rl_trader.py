
import pandas as pd
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RL_Trader")

class CryptoTradingEnv(gym.Env):
    """
    Custom Environment for trading ADA/USDT
    """
    metadata = {'render.modes': ['human']}

    def __init__(self, df, initial_balance=1000.0):
        super(CryptoTradingEnv, self).__init__()
        
        self.df = df
        self.initial_balance = initial_balance
        
        # Action Space: 0=Hold, 1=Buy, 2=Sell
        self.action_space = spaces.Discrete(3)
        
        # Observation Space: [Close, Volume, RSI, Exhaustion_Bull, Exhaustion_Bear, Position_Status]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32
        )
        
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.balance = self.initial_balance
        self.crypto_held = 0
        self.net_worth = self.initial_balance
        self.max_net_worth = self.initial_balance
        self.current_step = 0
        
        return self._next_observation(), {}

    def _next_observation(self):
        # Get the data for the current step
        frame = self.df.iloc[self.current_step]
        
        obs = np.array([
            frame['close'],
            frame['volume'],
            frame.get('rsi', 50.0),
            frame.get('bull_signal', 0),
            frame.get('bear_signal', 0),
            1.0 if self.crypto_held > 0 else 0.0 # Position status
        ], dtype=np.float32)
        
        return obs

    def step(self, action):
        # Execute one time step within the environment
        self._take_action(action)
        self.current_step += 1
        
        if self.current_step >= len(self.df) - 1:
            done = True
        else:
            done = False
            
        delay_modifier = (self.current_step / len(self.df))
        
        # Calculate Reward
        # Simple Reward: Change in Net Worth
        current_price = self.df.iloc[self.current_step]['close']
        current_net_worth = self.balance + (self.crypto_held * current_price)
        
        reward = current_net_worth - self.net_worth
        self.net_worth = current_net_worth
        
        if self.net_worth > self.max_net_worth:
            self.max_net_worth = self.net_worth
            
        obs = self._next_observation()
        
        return obs, reward, done, False, {}

    def _take_action(self, action):
        current_price = self.df.iloc[self.current_step]['close']
        
        # Buy
        if action == 1 and self.balance > 0:
            # Buy with 100% of balance (Aggressive)
            amount = self.balance / current_price
            fee = amount * current_price * 0.001 # 0.1% Fee
            self.crypto_held += (self.balance - fee) / current_price
            self.balance = 0
            
        # Sell
        elif action == 2 and self.crypto_held > 0:
            amount = self.crypto_held
            revenue = amount * current_price
            fee = revenue * 0.001
            self.balance += revenue - fee
            self.crypto_held = 0

def train_agent():
    from stable_baselines3 import A2C
    from stable_baselines3.common.vec_env import DummyVecEnv
    
    # Load Data
    logger.info("Loading Data for RL...")
    df = pd.read_csv("data/binance_ADAUSDT_1m.csv")
    
    # Add Features (RSI, Exhaustion)
    # We need to compute these beforehand
    logger.info("Computing Features...")
    
    # Simple RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50)
    
    # Dummy Signals (Placeholder for actual Exhaustion Detector logic)
    # ideally we import ExhaustionDetector and run it
    df['bull_signal'] = 0
    df['bear_signal'] = 0
    
    df = df.dropna().reset_index(drop=True)
    
    # Split Train/Test
    train_size = int(len(df) * 0.8)
    train_df = df[:train_size]
    test_df = df[train_size:]
    
    # Create Env
    env = DummyVecEnv([lambda: CryptoTradingEnv(train_df)])
    
    # Initialize Agent
    logger.info("Initializing A2C Agent...")
    model = A2C("MlpPolicy", env, verbose=1)
    
    # Train
    logger.info("Training...")
    model.learn(total_timesteps=10000)
    
    logger.info("Training Complete. Testing...")
    
    # Test
    test_env = CryptoTradingEnv(test_df)
    obs, _ = test_env.reset()
    done = False
    
    while not done:
        action, _states = model.predict(obs)
        obs, reward, done, truncated, info = test_env.step(action)
        
    logger.info(f"Final Net Worth: ${test_env.net_worth:.2f}")

if __name__ == "__main__":
    train_agent()
