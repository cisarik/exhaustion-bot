# AGENTS.md – The Brain: Coding Agent Protocols & Knowledge Base

Tento súbor slúži ako **Centrálny Mozog** pre AI agentov (Claude, Codex, Gemini, Droid ...).
Obsahuje presné inštrukcie, ako začať projekt alebo ako v ňom plynule pokračovať.

---

## 🤖 BOOT PROTOCOLS (Prompt Engineering)

### 🟢 A. RESUME PROMPT (Pre pokračovanie v práci)
**Použi tento prompt, keď sa vraciaš k projektu a chceš, aby agent okamžite pochopil kontext, históriu a ďalšie kroky.**

> **Copy & Paste do Chatu:**
>
> Si **Senior Python Developer** špecializovaný na Cardano DeFi. Infosec expert. Hacker. Backend magician. Evolution algorithms strategist. Trading expert. Tvojou úlohou je pokračovať vo vývoji projektu **Cardano Exhaustion Bot**.
>
> **Tvoj Prvý Krok (Context Loading):**
> Skôr než napíšeš riadok kódu, vykonaj túto sekvenciu analýzy prostredia:
> 1. **Prečítaj Project Mission:** `cat PRD.md` (pochop cieľ: profit, 15m timeframe, paper trading).
> 2. **Zisti Stav Kódu:** `ls -R` (pozri štruktúru) a `cat requirements.txt`.
> 3. **Analyzuj Históriu:** Spusti `git log -n 3 --oneline` a `git status`, aby si videl, čo naposledy robil predchádzajúci agent.
> 4. **Identifikuj Ďalší Krok:** Pozri sa do sekcie "Roadmap" v `PRD.md` a nájdi prvú neodškrtnutú úlohu [ ].
>
> **Tvoje Pravidlá Vývoja (Strict Rules):**
> *   **Profit First:** Každá zmena v kóde musí smerovať k zisku. Žiadny refactoring pre krásu, len pre funkčnosť a rýchlosť.
> *   **No Hallucinations:** Používaj len existujúce knižnice (`deltadefi-sdk`, `blockfrost-python`). Nevymýšľaj si API endpointy.
> *   **Hardening:** SSH beží na RPi. Neměň firewall pravidlá bez vedomia užívateľa.
> *   **Paper Trading Mode:** Všetky transakcie musia byť zatiaľ simulované (LOG only), pokiaľ `PRD.md` nehovorí inak.
>
> **Akcia:**
> Po analýze mi napíš krátke zhrnutie: "Analyzoval som repo. Posledná zmena bola X. Nasledujúci logický krok podľa PRD je Y." A potom čakaj na potvrdenie alebo začni kódovať.

---

### 🟡 B. INIT PROMPT (Len pre úplný začiatok)
**Použi len ak je repozitár prázdny.**

> **Copy & Paste do Chatu:**
>
> Si expert Python developer. Tvoj cieľ: Naprogramuj "HFT Exhaustion Bot" na Raspberry Pi 4 podľa priloženého `PRD.md`.
> Stack: Python 3.11, DeltaDefi SDK, BlockFrost, SQLite, FastAPI.
> Stratégia: Exhaustion Signal (Level 3 Reversal).
> Začni vytvorením základnej štruktúry: `exhaustion_detector.py` a `paper_trader.py`.

---

## 🛠️ Developer Knowledge Base (Pre Agenta)

### 1. Architektúra Systému
*   **Core Loop (`paper_trader.py`):**
    *   Pripája sa na Websocket (BlockFrost/DeltaDefi).
    *   Drží buffer posledných 50 sviečok (15m).
    *   Posiela dáta do `ExhaustionDetector`.
    *   Ak `Detector` vráti `SIGNAL_LEVEL_3`:
        *   Vypočíta risk (2% kapitálu).
        *   Vykoná "Virtual Swap".
        *   Zapíše do DB/Logu.
*   **Web Dashboard (`dashboard_api.py`):**
    *   FastAPI backend.
    *   Číta DB a zobrazuje QR kódy walletu.
    *   Generuje JSON pre frontend (timeline, profit).

### 2. Profit Mathematics (Prečo to funguje?)
*   **Timeframe:** 15 minút (Sweet spot medzi HFT a šumom).
*   **Fee Structure:** 0.3% swap fee + ~0.2 ADA tx fee.
*   **Threshold:** Aby bol obchod ziskový, pohyb ceny musí byť > 0.6% (Break-even).
*   **Cieľ:** Level 3 Exhaustion štatisticky predikuje pohyb 2-5%.

### 3. Raspberry Pi Hardening (Referencia)
Agent, ak musíš generovať inštalačné skripty, drž sa tohto štandardu:
*   **User:** `pi` (alebo custom), nikdy `root` pre aplikáciu.
*   **SSH:** Port 22 skrytý za `knockd` sekvenciou. Key-based auth only.
*   **Service:** Systemd unit file `cardano-bot.service` s `Restart=always`.

---

## 📝 Changelog & Context Handover
*(Agenti, sem zapisujte dôležité zmeny na konci vašej session, aby ďalší agent vedel nadviazať)*

*   **[2025-11-25] Init:** Vytvorené `PRD.md` a `AGENTS.md`. Definovaná stratégia 15m HFT.
*   **[Next]:** Implementácia `exhaustion_detector.py` podľa Pine Script logiky.
