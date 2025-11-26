import os
import sys

def generate_service_file():
    cwd = os.getcwd()
    python_exec = sys.executable
    user = os.getenv('USER', 'pi')
    
    # Robust service configuration for production
    service_content = f"""[Unit]
Description=Cardano DeFi HFT Exhaustion Bot
Documentation=https://github.com/your-repo/cardano-bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={user}
WorkingDirectory={cwd}
# Use unbuffered output for real-time logging
Environment=PYTHONUNBUFFERED=1
# Use uv for execution
ExecStart=/home/agile/.local/bin/uv run {cwd}/paper_trader.py

# Restart policy for high availability
Restart=always
RestartSec=10s
StartLimitInterval=300
StartLimitBurst=5

# Security hardening
ProtectSystem=full
PrivateTmp=true
NoNewPrivileges=true

# Logging
StandardOutput=append:{cwd}/bot_service.log
StandardError=append:{cwd}/bot_service_error.log

[Install]
WantedBy=multi-user.target
"""
    
    with open("cardano-bot.service", "w") as f:
        f.write(service_content)
    
    print(f"Generated 'cardano-bot.service' in {cwd}")
    print("To install:")
    print(f"sudo cp cardano-bot.service /etc/systemd/system/")
    print("sudo systemctl daemon-reload")
    print("sudo systemctl enable cardano-bot")
    print("sudo systemctl start cardano-bot")

if __name__ == "__main__":
    generate_service_file()
