# EVE-Online-FC-Payout-Tool
Tool to help fc do less and faster paperwork when doing payouts

---

## Setup and Install Guide

### Step 1: Install Python

1. Go to: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download **Python 3.9 or newer**
3. Run the installer

**IMPORTANT:** During installation, check the box: Add Python to PATH

---

## Step 2: Download tool and install dependencies

Either clone this GitHub repo, or download `FC_Payout_tool_v1.4.2.py` and `requirements.txt` into a folder. Open a terminal or Powershell window to this folder and run the following command:

```bash
pip install -r requirements.txt
```

The packages installed will be:
- `pyperclip` – copying in-game mail text to clipboard
- `requests` - gets character ids from the esi
- `playwright` - virtual browser to pull down br.evetools.org


Install Playwright browser

```bash
playwright install chromium
```

---

### Step 3: Run the tool

To launch the FC payout GUI:

```bash
python FC_Payout_Tool_v1.4.2.py
```

You will be able to:
- Enter Buyback ISK amount
- Import pilots in bulk from br.evetools.org by going to report ---> composition ---> chars and copying pilots including their photo and name.
- Import pilots in bulk by name with a list of names each on its own line.
- Import pilots from a fat link by copy pasting the names (can and likely will include the system and ship they were in when they clicked the link. These will be ignored)
- Import pilots automatically from a br.evetools.org URL
- Mark scouts and exclude pilots from payout
- Automatically generate an in-game mail and copy to clipboard

---

### Optional: Fix for Linux Clipboard

If `pyperclip` doesn’t work on Linux, install `xclip`:

```bash
sudo apt install xclip
```

---

### Optional: Build a Standalone Executable (.exe)

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

### Contributing

- Clone this repo using `git clone`
- Generate and use a Python Virtual Environment `python -m venv .venv` and `source .venv/bin/activate`
- Always update requirements.txt from inside the venv `pipreqs . --ignore .venv,tests --encoding utf-8 --force`

