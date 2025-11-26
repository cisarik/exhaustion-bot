from fastapi import FastAPI, HTTPException, Body, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging
import os
import json
import re
import asyncio
import aiofiles
from wallet_manager import WalletManager
from profit_manager import ProfitManager
from paper_trader import PaperTrader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DashboardAPI")

app = FastAPI(title="Cardano Exhaustion Bot API", version="1.0.0")

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize Managers
wm = WalletManager() 
CONFIG_FILE = "config.json"

# Global Trader Instance
trader = None
bot_task = None

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    # Default fallback
    return {
        "strategy": {"level1": 9, "level2": 12, "level3": 14},
        "risk": {"stop_loss_pct": 0.012, "take_profit_pct": 0.03, "risk_per_trade": 0.02, "max_trade_size_usdc": 500.0},
        "system": {"paper_mode": True, "status": "STOPPED"},
        "profit": {"target_ada": 100.0, "reserve_ada": 10.0, "withdraw_address": ""}
    }

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

BOT_CONFIG = load_config()

@app.on_event("startup")
async def startup_event():
    global trader
    # Initialize Trader
    trader = PaperTrader(config_path=CONFIG_FILE)
    logger.info("Bot Engine Initialized.")
    
    # Auto-start if configured
    if BOT_CONFIG.get("system", {}).get("status") == "RUNNING":
        await start_bot_internal()

async def start_bot_internal():
    global bot_task, trader
    if bot_task: return
    
    # Reload config into trader just in case
    trader.load_config(CONFIG_FILE)
    bot_task = asyncio.create_task(trader.start())
    logger.info("Bot loop started.")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Gather data for dashboard
    wallets = get_wallets_data()
    trades = get_trades_data()
    profit = get_profit_data()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wallets": wallets,
        "trades": trades,
        "profit": profit,
        "config": BOT_CONFIG,
        "bot_status": "RUNNING" if bot_task else "STOPPED"
    })

def get_wallets_data():
    wallets = wm.list_wallets()
    enriched_wallets = []
    # Fallback defaults if config is missing keys
    profit_cfg = BOT_CONFIG.get("profit", {})
    target_ada = profit_cfg.get("target_ada", 100.0)
    reserve_ada = profit_cfg.get("reserve_ada", 10.0)
    
    for w in wallets:
        # w: (id, name, address, network)
        # Mock balance or real
        # For demo, use mock based on paper trader if available?
        # PaperTrader tracks USDC balance.
        # Let's mock ADA balance for the wallet visual.
        
        current_balance = 50.0 # Default mock
        if w[1] == "Paper Trading Wallet":
             # If it's the paper wallet, maybe reflect paper trader balance?
             if trader:
                 current_balance = trader.balance_ada # Use virtual ADA balance
        
        progress = (current_balance / target_ada) * 100 if target_ada > 0 else 0
        
        # Color Logic
        # Green: >= Target
        # Orange: > Reserve but < Target
        # Red: < Reserve
        status_color = "red"
        if current_balance >= target_ada:
            status_color = "green"
        elif current_balance > reserve_ada:
            status_color = "orange"
            
        is_hidden = current_balance >= target_ada # "Strati sa z overview" on payout?
        # User said "nastala by hodnota payout strati sa z overview".
        # So if green, it might be hidden or shown as "Payout Processing" then hidden.
        # Let's keep it visible but mark it "Payout Ready" for now, unless specifically asked to hide.
        # Actually user said "strati sa". Let's add a flag.
        
        enriched_wallets.append({
            "id": w[0],
            "name": w[1],
            "address": w[2],
            "balance": round(current_balance, 2),
            "target": target_ada,
            "progress": round(progress, 1),
            "color": status_color,
            "hidden": False # We'll handle hiding in frontend or here. 
                            # If hidden, maybe we don't even append it? 
                            # But user might want to see history. 
                            # Let's set hidden=True and let template decide.
        })
    return enriched_wallets

def get_trades_data():
    try:
        if os.path.exists("bot_trade_log.txt"):
            with open("bot_trade_log.txt", "r") as f:
                return f.readlines()[-20:]
    except:
        pass
    return []

def get_profit_data():
    if trader:
        return {
            "usdc": round(trader.balance_usdc, 2),
            "ada": round(trader.balance_ada, 2)
        }
    return {"usdc": 0, "ada": 0}

@app.post("/bot/start")
async def start_bot_api():
    global BOT_CONFIG
    BOT_CONFIG["system"]["status"] = "RUNNING"
    save_config(BOT_CONFIG)
    await start_bot_internal()
    return {"status": "RUNNING"}

@app.post("/bot/stop")
async def stop_bot_api():
    global bot_task, BOT_CONFIG
    BOT_CONFIG["system"]["status"] = "STOPPED"
    save_config(BOT_CONFIG)
    
    if bot_task:
        bot_task.cancel()
        bot_task = None
    return {"status": "STOPPED"}

# ... other endpoints (QR, restore, backup) ...
@app.get("/qr/{wallet_name}")
def get_qr(wallet_name: str):
    file_path = f"wallet_{wallet_name.replace(' ', '_')}.png"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    # Return a placeholder if not found
    return HTMLResponse("QR Not Found", status_code=404)

@app.get("/trades")
def get_trades_endpoint():
    return {"recent_trades": get_trades_data()}

@app.post("/wallet/restore")
async def restore_wallet_endpoint(file: UploadFile = File(...), wallet_name: str = Form(...)):
    try:
        temp_filename = f"temp_restore_{file.filename}"
        async with aiofiles.open(temp_filename, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        result = wm.restore_wallet(temp_filename, wallet_name)
        os.remove(temp_filename)
        return {"status": "success", "wallet": result}
    except Exception as e:
        if os.path.exists(temp_filename): os.remove(temp_filename)
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/wallet/backup/{wallet_name}")
def backup_wallet_endpoint(wallet_name: str):
    try:
        filename = f"backup_{wallet_name.replace(' ', '_')}.key"
        path = wm.backup_wallet(wallet_name, filename)
        return FileResponse(path, filename=filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
@app.get("/profit")
def get_profit_endpoint():
    return get_profit_data()

@app.post("/bot/optimize")
async def optimize_bot():
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    from optimize_strategy import run_optimization
    
    # Run optimization in a separate thread to avoid blocking event loop
    loop = asyncio.get_event_loop()
    try:
        with ThreadPoolExecutor() as pool:
            # Run for fewer trials in API mode for responsiveness, or spawn background task
            # Let's do 20 trials (quick check)
            best_params = await loop.run_in_executor(pool, run_optimization, 20)
            
        if best_params:
            # Reload config in trader
            if trader:
                trader.load_config(CONFIG_FILE)
            
            # Reload global config for UI
            global BOT_CONFIG
            BOT_CONFIG = load_config()
            
            return {"status": "success", "params": best_params}
        else:
             raise HTTPException(status_code=500, detail="Optimization failed (no data?)")
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bot/backtest")
async def run_backtest_endpoint():
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    from backtest_engine import BacktestEngine
    from data_loader import DataLoader

    loop = asyncio.get_event_loop()
    
    def _run_backtest():
        # Load Data (Cached)
        loader = DataLoader(exchange_id='kraken', symbol='ADA/USDT', timeframe='15m')
        data = loader.fetch_data(limit=2000)
        
        if not data: return None
        
        engine = BacktestEngine(initial_capital=1000.0)
        engine.load_data(data)
        
        # Apply Current Config
        config = BOT_CONFIG
        engine.detector.level1 = config['strategy']['level1']
        engine.detector.level2 = config['strategy']['level2']
        engine.detector.level3 = config['strategy']['level3']
        engine.detector.lookback1 = config['strategy'].get('lookback1', 4)
        engine.detector.lookback2 = config['strategy'].get('lookback2', 3)
        engine.detector.lookback3 = config['strategy'].get('lookback3', 2)
        
        engine.stop_loss_pct = config['risk']['stop_loss_pct']
        engine.take_profit_pct = config['risk']['take_profit_pct']
        engine.risk_per_trade = config['risk'].get('risk_per_trade', 0.02)
        
        engine.run()
        
        metrics = engine.get_metrics()
        metrics['equity_curve'] = engine.equity_curve
        # Sampling equity curve for chart (reduce points if too many)
        if len(metrics['equity_curve']) > 200:
            step = len(metrics['equity_curve']) // 200
            metrics['equity_curve'] = metrics['equity_curve'][::step]
            
        return metrics

    try:
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, _run_backtest)
            
        if result:
            return {"status": "success", "result": result}
        else:
            return {"status": "error", "detail": "No data available"}
            
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/config/update")
async def update_config(new_config: dict = Body(...)):
    global BOT_CONFIG
    BOT_CONFIG.update(new_config)
    save_config(BOT_CONFIG)
    # Reload trader
    if trader:
        trader.load_config(CONFIG_FILE)
    return {"status": "updated"}
