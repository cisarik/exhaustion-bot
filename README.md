# Cardano HFT Exhaustion Bot 🚀

![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Status](https://img.shields.io/badge/Status-Paper%20Trading-orange)

A high-frequency trading bot optimized for the Cardano (ADA) blockchain, running efficiently on Raspberry Pi 4. It utilizes a custom "Exhaustion Level 3" reversal strategy to capture short-term volatility with precision.

## 🎯 Project Mission
**Target:** Generate +20-35% monthly ROI through automated, low-latency execution.
**Strategy:** Contrarian reversal based on sequential candle analysis (Pine Script adaptation).
**Hardware:** Optimized for ARM64 architecture (Raspberry Pi 4/5).

## ✨ Key Features
*   **🧠 Smart Detector:** Configurable Exhaustion Logic (Levels 1-3) with adjustable lookbacks.
*   **🧬 Genetic Optimization:** Built-in AI (Optuna) to evolve strategy parameters based on market conditions.
*   **🛡️ Safety First:** Circuit breakers, Slippage protection, and encrypted wallet management.
*   **📊 Glassmorphism Dashboard:** Modern Web UI for real-time monitoring, backtesting, and configuration.
*   **🧪 Backtest Verification:** One-click validation against historical data to prove profitability before deployment.

## 🛠️ Installation

### Prerequisites
*   Python 3.11+
*   Raspberry Pi OS (Lite/64-bit recommended) or Linux

### Setup
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/cardano-hft-bot.git
    cd cardano-hft-bot
    ```

2.  **Install dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Start the Dashboard:**
    ```bash
    uvicorn dashboard_api:app --host 0.0.0.0 --port 8000
    ```

4.  **Access UI:** Open `http://localhost:8000` in your browser.

## 🚀 Usage Guide

1.  **Optimize:** Go to the Dashboard config and click **"Vylepši (AI)"** to find the best parameters for the current market.
2.  **Verify:** Click **"OVERIŤ"** to run a backtest. Ensure the Equity Curve is green and upward.
3.  **Activate:** Set `paper_mode: false` in `config.json` (future feature) and fund your wallet.
4.  **Profit:** Watch the QR code turn **Green** when the profit target is met.

## ⚠️ Disclaimer
This software is for educational purposes only. Cryptocurrency trading involves high risk. Use at your own risk. The authors are not responsible for any financial losses.

---
*Built with ❤️ by Factory Agents*
