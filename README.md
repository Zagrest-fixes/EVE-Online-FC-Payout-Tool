# EVE-Online-FC-Payout-Tool
Tool to help fc do less and faster paperwork when doing payouts


# How to make .exe below (IF YOU WANT TO RUN IT USING PYTHON, AND NOT FOLLOW INSTRUCTIONS HOW TO COMPILE TO .EXE I ASSUME YOU ARE EXPERIENCED ENOUGH TO FIGURE IT OUT YOURSELF :))


# 🚀 FC_Payout_Tool_v1.0 - Full Installation Guide

This guide explains step-by-step how to set up and run the **FC_Payout_Tool_v1.0**. It includes all required Python packages and configuration needed for zKillboard importing, clipboard copying, and Playwright support.

---

## ✅ Step 1: Install Python

1. Go to: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download and install **Python 3.9 or newer**
3. During installation, **check this box**:
> ✅ "Add Python to PATH"

---

## ✅ Step 2: Open Terminal or PowerShell

- On **Windows**: Press `Win + R`, type `powershell`, press **Enter**
- On **macOS/Linux**: Open **Terminal**

Navigate to the folder containing your payout tool:

```bash
cd C:\Users\YourName\Documents\fcpayout
```

---

## ✅ Step 3: Install Required Python Packages

Run the following command to install all dependencies:

```bash
pip install playwright pyperclip asyncio
```

These packages are used for:
- `playwright`: fetching data from zKillboard
- `pyperclip`: copying mail to clipboard
- `asyncio`: managing asynchronous scraping

---

## ✅ Step 4: Set Local Browser Path for Playwright

Set the Playwright browser path to a local folder. This is required to bundle with `.exe` or to avoid permission issues:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\playwright-browsers"
```

> This sets a local browser path so Playwright installs into your current directory.

---

## ✅ Step 5: Install Chromium for Playwright

Install the Chromium browser engine into the local folder:

```bash
python -m playwright install chromium
```

This creates a `playwright-browsers` folder in your directory.

---

## ✅ Step 6: Run the Tool

To start the app, simply run:

```bash
python FC_Payout_Tool_v1.0.py
```

The GUI allows you to:
- Paste zKillboard killmail links
- Enter Buyback ISK amount
- Bulk import pilots (with optional charIDs for clickable links)
- Toggle Scout and Include status
- Remove or clear pilots
- Generate in-game mail and copy it to clipboard

---

## ✅ Clipboard Fix for Linux

If `pyperclip` doesn't work on Linux, run:

```bash
sudo apt install xclip
```

---

## ⚙️ Optional: Build into Executable (.exe)

To convert this script into a standalone `.exe` file:

### Step A: Install PyInstaller

```bash
pip install pyinstaller
```

### Step B: Build the Executable

```bash
pyinstaller --onefile --add-data "playwright-browsers;playwright-browsers" FC_Payout_Tool_v1.0.py
```

This generates the `.exe` inside the `dist/` folder. Make sure `playwright-browsers/` is copied alongside the `.exe`.

---

## 🆘 Troubleshooting

- If a browser or Playwright fails to load, try deleting the `playwright-browsers/` folder and reinstall using:
```bash
python -m playwright install chromium
```

- If copy to clipboard doesn't work:
  - On Linux: install `xclip` as shown above
  - On Windows/macOS: should work out of the box

---

## 🎉 You're Done!

Enjoy using the FC Payout Tool! Fly safe o7

