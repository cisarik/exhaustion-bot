<coding_guidelines>
# AGENTS.md – Cardano HFT Exhaustion Bot Developer Guide

## 1. Project Mission
**Goal:** Build a High-Frequency Trading (HFT) bot for Cardano (ADA/USDC) running on a Raspberry Pi 4.
**Strategy:** "Exhaustion Signal Level 3" (reversal strategy based on 15m candles).
**Target:** +20-35% monthly profit via frequent, small-gain trades (10-18 trades/month).
**Current Phase:** **PUBLIC BETA / PAPER TRADING** (Validation Complete, Ready for Fork).

## 2. Architecture Overview
The system is modular, designed for low-latency execution on constrained hardware (RPi 4).

### Modules
1.  **`exhaustion_detector.py`**
    *   **Role:** The "Brain". Analyzes price history to find "Level 3" exhaustion signals.
    *   **Logic:** Counts consecutive candles against a lookback period. Configurable via `config.json`.
    *   **Input:** List of close prices.
    *   **Output:** Signal Dict (`bull_l3`, `bear_l3`, counts).

2.  **`paper_trader.py`**
    *   **Role:** The "Engine". Main `asyncio` loop.
    *   **Function:** Connects to Websocket (DeltaDefi/BlockFrost/Simulated), feeds data to Detector, executes virtual trades.
    *   **Features:** PnL tracking, Slippage/Fee simulation, Risk Management (SL/TP), Config Hot-Reloading.
    *   **Config:** Loads from `config.json`.

3.  **`wallet_manager.py`** & **`profit_manager.py`**
    *   **Role:** The "Vault" & "Accountant".
    *   **Function:** BIP39 key management (encrypted), Profit Payout logic.
    *   **Security:** Strict file permissions, automatic backup endpoints.

4.  **`dashboard_api.py`**
    *   **Role:** The "Face". FastAPI application.
    *   **Features:**
        *   **Live Monitor:** Glassmorphism UI with dynamic status colors (Red/Orange/Green).
        *   **AI Lab:** "Vylepši" button triggers Genetic Optimization (`optimize_strategy.py`).
        *   **Validation:** "Overiť" button runs `backtest_engine.py` on history.

5.  **`backtest_engine.py`**
    *   **Role:** The "Prover". Simulates trades against historical CSV data to calculate Monthly ROI, Drawdown, and Profit Factor.

## 3. Technical Stack
*   **Language:** Python 3.13+
*   **Core Libs:** `asyncio`, `numpy`, `optuna` (AI), `pandas`, `ccxt`.
*   **Web/API:** `fastapi`, `uvicorn`, `jinja2`, `tailwindcss`.
*   **Security:** `sentry-sdk`, `cryptography`, `.gitignore` rules.

## 4. Developer Workflow

### A. The Optimization Loop
1.  **Analyze:** User observes metrics on Dashboard.
2.  **Optimize:** Click "Vylepši (AI)". System runs 20-100 generations of evolution to fit current market volatility.
3.  **Verify:** Click "Overiť". System runs backtest on last 2000 candles to confirm safety.
4.  **Deploy:** Config is auto-saved. Bot uses new parameters immediately.

### B. Testing
Always run the "Profit Proof" before committing:
```bash
python test_profit_proof.py
```
Output must show `PROJECTED MONTHLY PROFIT: > $200`.

### C. InfoSec Guidelines
*   Never commit `*.key` files.
*   Never log mnemonics to stdout.
*   Use `wallet_manager.backup_wallet()` for user-requested exports only.

## 6. Current Status
*   **[DONE]** Core modules (Detector, Trader, Wallet, Backtest).
*   **[DONE]** AI Optimization & UI Integration.
*   **[DONE]** "Profit Proof" Automated Test.
*   **[TODO]** **Live Trading:** Switch `paper_mode: false` and integrate `pycardano` signing.

</coding_guidelines>
