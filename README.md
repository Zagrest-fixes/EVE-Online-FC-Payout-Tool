# EVE-Online-FC-Payout-Tool
Tool to help fc do less and faster paperwork when doing payouts


# How to make .exe & run below



# ✅ FC Payout Tool v2.0 - Installation & Setup Guide

This is the fully verified setup guide to run the FC Payout Tool v2.0.

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
pip install playwright pyperclip requests
```

These packages are used for:
- `pyperclip` – copying in-game mail text to clipboard
- `requests` - gets character ids from the esi

> Note: `asyncio` is built into Python — no need to install it.

---

## ✅ Step 4: Run the Tool

To launch the FC payout GUI:

```bash
python FC_Payout_Tool_v2.0.py
```

You will be able to:
- Enter Buyback ISK amount
- Import pilots in bulk from br.evetools.org by going to report ---> composition ---> chars and copying pilots including their photo and name.
- Import pilots in bulk by name with a list of names each on its own line.
- Import pilots from a fat link by copy pasting the names (can and likely will include the system and ship they were in when they clicked the link. These will be ignored)
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
pyinstaller --onefile --add-data "playwright-browsers;playwright-browsers" FC_Payout_Tool_v2.0.py
```
OR

```bash
pyinstaller --onefile --noconsole .\FC_Payout_Tool_v2.0.py
```

Make sure `playwright-browsers/` is copied next to your `.exe`.

---

## 🎉 You're Done!

Enjoy using the FC Payout Tool! Fly safe o7

