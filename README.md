# EVE-Online-FC-Payout-Tool
Tool to help fc do less and faster paperwork when doing payouts


# How to make .exe & run below



# ✅ FC Payout Tool v1.1 - Installation & Setup Guide

This is the fully verified setup guide to run the FC Payout Tool v1.1.

---

## 🚀 Step 1: Install Python

1. Go to: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download **Python 3.9 or newer**
3. Run the installer

**IMPORTANT:** During installation, check the box:
> ✅ "Add Python to PATH"

---

## ✅ Step 2: Open PowerShell or Terminal

Navigate to the folder where the script is saved:

```bash
cd C:\Users\YourName\Documents\fcpayout
```

---

## ✅ Step 3: Install Required Python Packages

Run the following command:

```bash
pip install playwright pyperclip
```

These packages are used for:
- `playwright` – web scraping zKillboard
- `pyperclip` – copying in-game mail text to clipboard

> Note: `asyncio` is built into Python — no need to install it.

---

## ✅ Step 4: Set Local Playwright Browser Path

Your script forces the use of a local browser folder, so you must set this environment variable:

### On Windows PowerShell:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\playwright-browsers"
```

### On macOS/Linux:

```bash
export PLAYWRIGHT_BROWSERS_PATH="$PWD/playwright-browsers"
```

This ensures that browser binaries are stored locally and work with `.exe` if needed.

---

## ✅ Step 5: Install Playwright Chromium Browser

Run this command after setting the env variable:

```bash
python -m playwright install chromium
```

This installs Chromium into the `playwright-browsers/` folder.

---

## ✅ Step 6: Run the Tool

To launch the FC payout GUI:

```bash
python FC_Payout_Tool_v1.1.py
```

You will be able to:
- Paste zKillboard links
- Enter Buyback ISK amount
- Import pilots in bulk from br.evetools.org by going to report ---> composition ---> chars and copying pilots including their photo and name or from killmails by pasating zkill link.
EXAMPLE:
```
charID-0123456789
NAME
charID-0123456789
NAME
charID-0123456789
NAME
```
- Mark scouts and exclude pilots from payout
- Automatically generate an in-game mail and copy to clipboard

---

## 🧠 Optional Fix for Linux Clipboard

If `pyperclip` doesn’t work on Linux, install `xclip`:

```bash
sudo apt install xclip
```

---

## ⚙️ Optional: Build a Standalone Executable (.exe)

To convert the script to a portable `.exe` file:

1. Install PyInstaller:

```bash
pip install pyinstaller
```

2. Build your `.exe`:

```bash
pyinstaller --onefile --add-data "playwright-browsers;playwright-browsers" FC_Payout_Tool_v1.1.py
```
OR

```bash
pyinstaller --onefile --noconsole .\FC_Payout_Tool_v1.1.py
```

Make sure `playwright-browsers/` is copied next to your `.exe`.

---

## 🎉 You're Done!

Enjoy using the FC Payout Tool! Fly safe o7

