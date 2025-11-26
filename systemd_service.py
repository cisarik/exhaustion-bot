import os
import sys

def generate_service_file():
    cwd = os.getcwd()
    python_exec = sys.executable
    user = os.getenv('USER', 'pi')
    
    service_content = f"""[Unit]
Description=Cardano DeFi HFT Exhaustion Bot
After=network.target

[Service]
User={user}
WorkingDirectory={cwd}
ExecStart={python_exec} {cwd}/paper_trader.py
Restart=always
RestartSec=5
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
