# 🌲 PyneCore: The Bridge Between TradingView and Python
> **Knowledge Base for Factory Droid Agents**
> *Status: Active Learning Module*
> *Version: 1.0 (November 2025)*

## 1. What is PyneCore?
PyneCore is a revolutionary framework that brings **Pine Script's execution model** to Python. Unlike standard Python (which uses vectorized operations like Pandas), PyneCore executes code **bar-by-bar**, exactly like TradingView.

**Why is this game-changing?**
*   **Zero Translation Friction:** You can take almost ANY strategy from TradingView and convert it to Python 1:1.
*   **State Management:** It handles `var` (persistence) variables automatically via AST transformation.
*   **Accuracy:** 14-15 digits precision match with TradingView.
*   **Ecosystem:** Compatible with standard Python libraries (TensorFlow, etc.) but runs with Pine logic.

---

## 2. Installation & Setup
PyneCore requires **Python 3.11+**.

```bash
# Install with UV (Recommended)
uv pip install "pynesys-pynecore[all]"
```

---

## 3. Anatomy of a PyneCore Strategy

A PyneCore script looks like Python but behaves like Pine Script. It MUST start with the `@pyne` magic docstring or be processed by the Pyne runner.

### Basic Structure (Example: Simple RSI Strategy)

```python
"""
@pyne
"""
from pynecore.lib import script, open, high, low, close, ta, plot, strategy, input, color

# Define Strategy Parameters
@script.strategy(title="My First Pyne Strategy", overlay=True)
def main(
    length=input.int("RSI Length", 14),
    overbought=input.float("Overbought", 70.0),
    oversold=input.float("Oversold", 30.0)
):
    # 1. Calculate Indicators (Just like Pine!)
    # 'close' is automatically a Series
    rsi_value = ta.rsi(close, length)
    
    # 2. Logic
    # 'crossunder' and 'crossover' are available in ta library
    if ta.crossover(rsi_value, oversold):
        strategy.entry("Long", strategy.long)
        
    if ta.crossunder(rsi_value, overbought):
        strategy.close("Long")
        
    # 3. Plotting
    plot(rsi_value, title="RSI", color=color.purple)
```

### Key Concepts
1.  **`Series`**: Variables like `close`, `high` are Series. Operations on them (e.g. `close + 1`) return a new Series.
2.  **`ta` Library**: Contains all Pine Script indicators (`ta.sma`, `ta.ema`, `ta.macd`, `ta.rsi`).
3.  **Execution**: The `main` function is called ONCE per bar.
4.  **History Access**: `close[1]` accesses the previous bar's close price.

---

## 4. AI Strategy Generation Protocol ("The AI High Level")

This is the core protocol for Droid Agents. Instead of writing strategies from scratch, we leverage the vast library of TradingView strategies and use LLMs to port them.

### 🤖 Step-by-Step Workflow

#### Step 1: Find a Pine Script Strategy
Find a strategy concept (e.g., "SuperTrend", "MACD Divergence"). You can often find the source code on TradingView.

#### Step 2: The "Transpiler Prompt"
Use this specific prompt to ask an LLM (like Claude 3.5 Sonnet or GPT-4) to convert the code.

> **System Prompt:**
> You are an expert in both Pine Script v5/v6 and the `pynesys-pynecore` Python framework.
> Your task is to convert the following Pine Script into a valid PyneCore Python script.
>
> **Rules:**
> 1. Use `from pynecore.lib import *`.
> 2. Use the `@script.strategy` decorator.
> 3. Map `ta.*` functions 1:1 (e.g. `ta.sma` -> `ta.sma`).
> 4. Map `input.*` functions 1:1.
> 5. Ensure `strategy.entry` and `strategy.close` are used correctly.
> 6. Do not use Pandas or Numpy; stick to PyneCore series logic.
>
> **Input Pine Script:**
> [INSERT PINE SCRIPT HERE]

#### Step 3: Validation
Run the generated script using the Pyne CLI or runner to verify syntax.

```bash
pyne run strategy.py --data data/my_data.csv
```

---

## 5. Advanced Features

### Persistent Variables (`var` in Pine)
In Pine: `var float my_sum = 0.0`
In PyneCore:
```python
from pynecore import Persistent

# Inside function
my_sum: Persistent[float] = 0.0
my_sum += close
```

### Data Management
PyneCore has a built-in data manager.
```bash
pyne data download ccxt --symbol "BINANCE:ADA/USDT" --timeframe "1m"
```

---

## 6. Current Implementation Status (Exhaustion Bot)
*   **Current Engine:** Custom Python `BacktestEngine` (Legacy).
*   **Future Goal:** Migrate `BacktestEngine` to PyneCore to allow rapid strategy iteration.
*   **Roadmap:**
    1. Install Python 3.11 environment (Done: `.venv311`).
    2. Install PyneCore (Done).
    3. Port "Trend + Pullback" strategy to `strategies/trend_pullback.py`.
    4. Compare results.

---

> *Use this document to master the art of "Pine-in-Python".*
