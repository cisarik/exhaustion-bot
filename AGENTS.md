# AGENTS.md – The Brain: Coding Agent Protocols & Knowledge Base

Tento súbor slúži ako **Centrálny Mozog** pre AI agentov (Claude, Codex, Gemini, Droid ...).
Obsahuje presné inštrukcie, ako začať projekt alebo ako v ňom plynule pokračovať.

---

## 🤖 BOOT PROTOCOLS (Prompt Engineering)

### 🟢 A. RESUME PROMPT (Pre pokračovanie v práci)
**Použi tento prompt, keď sa vraciaš k projektu a chceš, aby agent okamžite pochopil kontext, históriu a ďalšie kroky.**

> **Copy & Paste do Chatu:**
>
> Si **Senior Python Developer** špecializovaný na Cardano DeFi, HFT a Algorithmic Trading.
> Tvojou úlohou je pokračovať vo vývoji projektu **Cardano Exhaustion Bot**.
>
> **Tvoj Prvý Krok (Context Loading):**
> Skôr než napíšeš riadok kódu, vykonaj túto sekvenciu analýzy prostredia:
> 1. **Prečítaj Project Mission:** `cat PRD.md` (pochop cieľ: profit).
> 2. **Zisti Stav Kódu:** `ls -F` a `cat requirements.txt`. Projekt používa **`uv` package manager**.
> 3. **Analyzuj Históriu:** `git log -n 3 --oneline`.
> 4. **Načítaj Ziskovú Stratégiu:** `cat tests/test_profitable_config.py` a `cat config.json`. Toto je tvoja "Golden Reference".
> 5. **Identifikuj Ďalší Krok:** Pozri sa do sekcie "Roadmap" v `PRD.md` a nájdi prvú neodškrtnutú úlohu.
>
> **Tvoje Pravidlá Vývoja (Strict Rules):**
> *   **Profit First:** Každá zmena musí prejsť regresným testom `uv run python -m unittest tests/test_profitable_config.py`.
> *   **UV Only:** Na spúšťanie príkazov používaj výhradne `uv run <command>` (napr. `uv run python ...`). Nepoužívaj priamo `python` ani `pip`.
> *   **No Hallucinations:** Používaj existujúci `delta_defi_client.py` pre WebSocket dáta.
> *   **Test Driven:** Nová funkcionalita začína vytvorením testu.
>
> **Akcia:**
> Analyzuj repo a napíš zhrnutie: "Stratégia je nastavená na [Timeframe/Params]. Posledný profit test bol [Result]. Nasledujúci krok je [Task]."

---

### 🟡 B. INIT PROMPT (Len pre úplný začiatok)
**Použi len ak je repozitár prázdny.**

> **Copy & Paste do Chatu:**
>
> Si expert Python developer. Tvoj cieľ: Naprogramuj "HFT Exhaustion Bot" na Raspberry Pi 4.
> Stack: Python 3.11+, uv, SQLite, FastAPI.
> Stratégia: Exhaustion Signal (Level 3 Reversal).

---

## 🛠️ Developer Knowledge Base (Pre Agenta)

### 1. Architektúra Systému
*   **Core Loop (`paper_trader.py`):**
    *   Beží ako `cardano-bot.service` (Systemd).
    *   Používa `delta_defi_client.py` pre Async WebSocket data feed (HFT 1m dáta).
    *   Data processing cez `ExhaustionDetector` + RSI Filter.
*   **Strategy Lab (`dashboard_api.py`):**
    *   FastAPI backend na porte 8000.
    *   Endpoint `/api/backtest/simulate` pre real-time simulácie.
    *   Frontend `strategy_lab.html` s Lightweight Charts.

### 2. Profit Mathematics (Overená Stratégia)
Na základe Matrix Search a TDD (November 2025):
*   **Timeframe:** 1m (HFT Dip Hunting).
*   **Stratégia:** EMA 200 Trend Filter + L3 Exhaustion + Fib 0.5 Exit.
*   **Logika:** Kúpiť len keď cena > EMA 200 a nastane L3 Dip (Pullback).
*   **Exit:** Dynamický Fibonacci Retracement (0.5).
*   **Výsledok:** Profit $1.03 (na 10k sviečkach), 11 obchodov, stabilnejšie ako čistý counter-trend.

### 3. Tooling & Commands
*   **Spustenie Bota:** `sudo systemctl start cardano-bot`
*   **Spustenie Dashboardu:** `./start_dashboard.sh` (používa `uv`)
*   **Run Tests:** `uv run python -m unittest discover tests`
*   **Profit Matrix:** `uv run python profit_matrix_tool.py`
*   **PyneCore Strategy Dev:** `uv run -p .venv311/bin/python strategy_pynecore.py` (viď `PYNECORE.md`)

---

## 🧬 AI Strategy Generation (The Future)
Našli sme cestu k nekonečnej studnici stratégií cez **PyneCore**.
*   **Knowledge Base:** Prečítaj `PYNECORE.md` pre detaily.
*   **Workflow:**
    1.  Nájdi Pine Script stratégiu na TradingView.
    2.  Použi "Transpiler Prompt" z `PYNECORE.md` na konverziu do Pythonu.
    3.  Otestuj v `.venv311` prostredí.

---

## 📝 Changelog & Context Handover
*(Agenti, sem zapisujte dôležité zmeny na konci vašej session)*

*   **[2025-11-25] Init:** Vytvorené `PRD.md` a `AGENTS.md`.
*   **[2025-11-26] HFT & UV Migration:**
    *   Migrácia na **`uv`**.
    *   Implementácia `Strategy Lab`.
    *   **Nový "Holy Grail":** Trend + Pullback (EMA 200 + L3 + Fib 0.5).
    *   **PyneCore Foundation:** Vytvorený `PYNECORE.md` a prostredie `.venv311` pre budúci vývoj stratégií v štýle Pine Script.
    *   Bot beží na `paper_trader.py` s aktualizovanou logikou.
