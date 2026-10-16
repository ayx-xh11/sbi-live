# SBI Live Balance Desktop Widget for Windows

A polished, secure Windows desktop widget that monitors your State Bank of India (SBI) Savings Account available balance and displays it directly on your desktop.

![Status](https://img.shields.io/badge/Security-OS--Level%20Encrypted-green)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)

---

## Key Features

- **Polished Desktop Widget**: Draggable, frameless dark-mode card designed for Windows 10/11 desktops.
- **Privacy Mode**: Click directly on the balance to toggle privacy masking (`₹ 24,582.37` ↔ `₹ ••••••••`).
- **Persistent Background Session**: Uses a dedicated Microsoft Edge / Chromium profile to maintain an authenticated SBI session in the background.
- **Strict Security & Compliance**:
  - **Zero OTP Interception**: OTP and CAPTCHA challenges are completed directly in the official SBI browser window.
  - **No Plaintext Credentials**: Credentials are stored only in **Windows Credential Manager** (`keyring`).
  - **Zero Persistence of Sensitive Data**: Never stores OTP, PIN, CAPTCHA, or full account numbers.
  - **Redacting SafeLogger**: Scrubbing engine prevents accidental logging of passwords, tokens, or account numbers.
  - **Strict Domain Guard**: Aborts navigations outside verified SBI domains.
- **Multi-Account Support**: Automatically detects savings accounts and provides a selection dialog showing only masked identifiers (e.g., `••••1234`).
- **Configurable Refresh**: Background refresh intervals (5m, 10m, 15m default, 30m, or manual only).
- **Windows Integration**:
  - Always-on-top toggle.
  - Start with Windows automatically via `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
  - System Tray integration with minimization and background actions.
  - Remembers widget desktop coordinates.

---

## Authentication & Security Architecture

### Flow Diagram

```text
               Windows Startup / App Launch
                           │
                           ▼
                    Balance Widget
                           │
                 [Check Active Session]
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
   [Session Valid]                 [Session Expired / None]
          │                                 │
          │ Background                      ▼
          │ Poll                   [Bring Official SBI Window Forward]
          │                                 │
          ▼                        [Prefill Username & Password]
    Extract Balance                         │
          │                        [User Enters CAPTCHA on SBI]
          ▼                                 │
    Update Widget                  [User Enters SMS OTP on SBI]
          │                                 │
   [Return to Idle]                [Detect Authenticated Dashboard]
                                            │
                                            ▼
                                   [Hide / Minimize Browser]
                                            │
                                            ▼
                                     Extract Balance
```

### What Happens When SBI Requests CAPTCHA or OTP?
1. The widget transitions to `CAPTCHA_REQUIRED` or `OTP_REQUIRED` state and displays the status.
2. The **real official SBI browser window** is brought to the foreground (`user32.ShowWindow` + `SetForegroundWindow`).
3. If credentials are saved in Windows Credential Manager, the widget pre-fills username and password on the verified domain.
4. **You enter the CAPTCHA and SMS OTP directly into the authentic SBI web page.** The widget never intercepts or reads your OTP.
5. The moment authentication succeeds and the dashboard loads, the browser automatically minimizes back into the background, and the widget displays your fresh available balance.

### Session Lifespan & RBI Guidelines
Per Reserve Bank of India (RBI) internet banking security guidelines, sessions expire after 5–15 minutes of inactivity. The widget's background refresh loop sends lightweight keep-alive requests while your PC is on and active. When the computer sleeps, restarts, or the session naturally expires, the widget marks the balance as `(cached)` and clearly indicates that authentication is required.

---

## Project Structure

```text
d:\code\balance\
├── app/
│   ├── config.py                 # Persistent settings & Windows startup registry
│   ├── state.py                  # Explicit AuthState state machine
│   ├── security/
│   │   ├── domain_guard.py       # Strict allowlisting & URL validation
│   │   ├── safe_logger.py        # Redacting logger (never logs credentials/OTP/acc)
│   │   └── credentials.py       # Windows Credential Manager wrapper (keyring)
│   ├── browser/
│   │   ├── window_utils.py       # Windows OS API window management (ctypes user32)
│   │   ├── browser_manager.py    # Playwright lifecycle & persistent context
│   │   └── selectors.py          # Resilient selectors for YONO/SBI
│   ├── sbi/
│   │   ├── auth_flow.py          # Live SBI login, prefill, and user challenge loops
│   │   ├── balance_parser.py     # Indian Rupee parser & savings account extractor
│   │   └── session_monitor.py    # Background refresh & keep-alive coordinator
│   └── ui/
│       ├── theme.py              # Visual colors & typography
│       ├── widget.py             # Floating draggable widget card
│       ├── settings_dialog.py    # Credential & preferences modal
│       ├── account_dialog.py     # Multi-account selection modal
│       └── tray_icon.py          # System tray icon (pystray)
├── tests/
│   ├── test_credentials.py
│   ├── test_domain_guard.py
│   ├── test_safe_logger.py
│   ├── test_balance_parser.py
│   ├── test_state_machine.py
│   ├── test_config.py
│   ├── test_integration.py
│   └── fixtures/mock_sbi_pages.py
├── run_widget.py                 # Main Python entrypoint
├── requirements.txt              # Dependencies
├── build_exe.bat                 # PyInstaller production build script
└── README.md
```

---

## Installation & Setup

### Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.11+ (or run the standalone compiled `.exe`)
- Microsoft Edge or Chromium

### Option 1: Running from Source

1. Clone or navigate to the project directory:
   ```cmd
   cd d:\code\balance
   ```

2. Create and activate a virtual environment:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   playwright install chromium
   ```

4. Run the widget:
   ```cmd
   python run_widget.py
   ```
   *(To run without a console window, use `pythonw run_widget.py`)*

---

### Option 2: Running the Standalone Executable

The application can be compiled into a self-contained `.exe` that runs without Python installed:

1. Build the executable:
   ```cmd
   .\build_exe.bat
   ```
2. The executable will be generated at:
   ```text
   dist\SBIBalanceWidget\SBIBalanceWidget.exe
   ```
3. Run `SBIBalanceWidget.exe`. It launches cleanly with zero console windows.

---

## First-Run Experience

1. Launch the widget. A sleek dark card appears on your desktop.
2. Click the **⚙ (Settings)** button on the top right.
3. In the **SBI Internet Banking Credentials** section:
   - Enter your SBI Username and Password.
   - Click **Save to Windows**. Your credentials are encrypted and stored in your Windows Vault.
4. Click **🔐 Re-authenticate Now** (or **↻ Refresh**).
5. The official SBI browser window opens with your username and password pre-filled.
6. Complete the CAPTCHA and SMS OTP in the browser.
7. As soon as you log in, the browser automatically minimizes and your Available Balance appears on the widget.
8. Click the balance anytime to toggle privacy mode (`₹ ••••••••`).

---

## Running the Automated Test Suite

Run the full pytest suite:

```cmd
.venv\Scripts\pytest -v
```

All 26 automated tests cover:
- Windows Credential Manager integration (mocked isolated backend)
- Domain allowlisting and phishing/redirect rejection
- SafeLogger redaction of passwords, OTPs, and account numbers
- Indian Rupee currency formatting (`₹ 1,23,456.78`) and parsing
- Isolation of Available Balance from Hold, Lien, and Ledger balances
- Multi-account detection and selection
- State machine lifecycle transitions
- Offline cached balance handling
- Configuration persistence

---

## Security Guarantees

1. **Direct Official Authentication**: No MITM proxies or third-party servers. All web traffic flows strictly between Microsoft Edge and SBI official servers (`*.sbi.bank.in`, `*.onlinesbi.sbi`).
2. **No Credential Leakage**: Credentials are saved exclusively in Windows Credential Manager via Windows DPAPI / Vault.
3. **No OTP Retention**: OTPs are entered directly on the bank's page and are never logged or stored.
4. **Redacted Logs**: Any logs created in `%APPDATA%\SBIBalanceWidget\logs\widget.log` are strictly sanitized.
