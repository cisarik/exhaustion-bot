# INFOSEC.md – Cardano Bot Security Architecture (2025 Standards)

## 1. Security Philosophy: "Zero Trust & Defense in Depth"
This system handles financial assets (Private Keys). Security is not an add-on; it is the foundation. We assume the network is hostile and the hardware could be physically compromised.

## 2. Critical Assets
1.  **Mnemonic Phrases (BIP39):** The "Keys to the Kingdom". Access to funds.
2.  **API Keys (BlockFrost, DeltaDefi):** Access to data and execution.
3.  **Trade Logic:** Intellectual property (Strategy).
4.  **Logs:** Privacy leakage (IPs, balances).

## 3. Hardening Layers

### Layer 1: Network (The Moat)
*   **Firewall (UFW):**
    *   Default: `DENY INCOMING`, `ALLOW OUTGOING`.
    *   Allow ONLY: SSH (Port 22 - conditional), HTTP (Port 8000 - local only).
*   **Port Knocking (Knockd):**
    *   SSH port is **CLOSED** by default.
    *   Opens only after a specific sequence of "knocks" (e.g., 7000 -> 8000 -> 9000).
    *   Closes automatically after 30 seconds.
*   **Fail2Ban:**
    *   Ban IP after 3 failed SSH attempts.
    *   Ban IP after 5 suspicious HTTP requests.

### Layer 2: OS & Access (The Castle Walls)
*   **User Management:**
    *   Default `pi` user DISABLED or renamed.
    *   New user `bot_admin` with sudo privileges.
    *   **SSH Keys ONLY:** Password authentication disabled (`PasswordAuthentication no`).
*   **Updates:**
    *   `unattended-upgrades` enabled for security patches.

### Layer 3: Application Security (The Vault)
*   **Encrypted Storage:**
    *   **NEVER** store Mnemonics in plain text (SQLite).
    *   **Implementation:** AES-256-GCM encryption using a master key derived from a user-provided passphrase (PBKDF2).
    *   The master key is **never stored on disk**. It must be input on service start (RAM only).
*   **Environment Variables:**
    *   API Keys stored in `.env` file, readable ONLY by the bot user (`chmod 600`).
*   **Memory Hygiene:**
    *   Mnemonics cleared from memory immediately after use (`gc.collect()`, overwrite variables).

### Layer 4: Operational Security (The Guards)
*   **Circuit Breakers:**
    *   **Max Drawdown Stop:** If PnL drops < -5% in 24h, bot auto-terminates.
    *   **Fat Finger Check:** Max trade size limit (e.g., 100 ADA).
*   **Monitoring:**
    *   Alerts on: Failed login attempts, Service restarts, Large balance changes.

## 4. Implementation Roadmap (TDD)

### Step 1: Secure Storage (Priority)
*   [ ] Create `crypto_utils.py`: Helper for AES encryption/decryption.
*   [ ] Update `wallet_manager.py`: Encrypt mnemonics before DB insert.
*   [ ] Test: Verify that DB content is gibberish without the key.

### Step 2: Runtime Security
*   [ ] Modify `systemd_service.py`: Prompt for password on start (or use systemd-creds).
*   [ ] Implement `SecurityAudit` class: Checks file permissions and firewall status on startup.

## 5. Emergency Procedures
*   **Panic Button:** Script `panic.sh` that:
    1.  Stops the bot service.
    2.  Closes all open ports (UFW deny all).
    3.  Wipes the `.env` file.
    4.  (Optional) Deletes the encrypted DB.
